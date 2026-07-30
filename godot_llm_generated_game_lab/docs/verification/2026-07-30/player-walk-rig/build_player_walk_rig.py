from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Callable

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageSequence
from scipy.spatial import Delaunay
from scipy import ndimage

SOURCE_ROOT = Path('/data/tmp/player-rig-source')
OUT = Path('/data/tmp/player-walk-rig-proof')
FRAME_COUNT = 32
FRAME_DURATION_MS = 60
CROP_X0, CROP_Y0, CROP_X1, CROP_Y1 = 96, 0, 544, 896
CROP_W, CROP_H = CROP_X1 - CROP_X0, CROP_Y1 - CROP_Y0
FINAL_SIZE = (320, 640)


def point(value: dict[str, float]) -> np.ndarray:
    return np.array([value['x'] - CROP_X0, value['y'] - CROP_Y0], dtype=np.float64)


def rotate(vector: np.ndarray, angle: float) -> np.ndarray:
    c, s = math.cos(angle), math.sin(angle)
    return np.array([c * vector[0] - s * vector[1], s * vector[0] + c * vector[1]], dtype=np.float64)


def ik_midpoint(start: np.ndarray, end: np.ndarray, length_a: float, length_b: float, sign: float) -> np.ndarray:
    delta = end - start
    distance = float(np.linalg.norm(delta))
    distance = min(max(distance, abs(length_a - length_b) + 1e-3), length_a + length_b - 1e-3)
    direction = delta / max(float(np.linalg.norm(delta)), 1e-6)
    a = (length_a * length_a - length_b * length_b + distance * distance) / (2.0 * distance)
    h = math.sqrt(max(length_a * length_a - a * a, 0.0))
    perpendicular = np.array([-direction[1], direction[0]], dtype=np.float64)
    return start + direction * a + perpendicular * h * sign


def gait_offset(q: float, step: float, lift: float) -> tuple[float, float]:
    if q < 0.5:
        u = q / 0.5
        return step * (1.0 - 2.0 * u), 0.0
    u = (q - 0.5) / 0.5
    smooth = u * u * (3.0 - 2.0 * u)
    return -step + 2.0 * step * smooth, -lift * math.sin(math.pi * u)


def local_segment_point(a: np.ndarray, b: np.ndarray, t: float, offset: float) -> np.ndarray:
    vector = b - a
    normal = np.array([-vector[1], vector[0]], dtype=np.float64)
    normal /= max(float(np.linalg.norm(normal)), 1e-6)
    return a + vector * t + normal * offset


def transform_segment_point(
    source_a: np.ndarray,
    source_b: np.ndarray,
    target_a: np.ndarray,
    target_b: np.ndarray,
    source_point: np.ndarray,
) -> np.ndarray:
    source_vector = source_b - source_a
    source_length = max(float(np.linalg.norm(source_vector)), 1e-6)
    source_direction = source_vector / source_length
    source_normal = np.array([-source_direction[1], source_direction[0]])
    relative = source_point - source_a
    t = float(np.dot(relative, source_direction) / source_length)
    offset = float(np.dot(relative, source_normal))
    target_vector = target_b - target_a
    target_length = max(float(np.linalg.norm(target_vector)), 1e-6)
    target_direction = target_vector / target_length
    target_normal = np.array([-target_direction[1], target_direction[0]])
    return target_a + target_vector * t + target_normal * offset


def bilinear(corners: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray], u: float, v: float) -> np.ndarray:
    top_left, top_right, bottom_left, bottom_right = corners
    top = top_left * (1.0 - u) + top_right * u
    bottom = bottom_left * (1.0 - u) + bottom_right * u
    return top * (1.0 - v) + bottom * v


def warp_piecewise(source: np.ndarray, source_points: np.ndarray, target_points: np.ndarray) -> np.ndarray:
    triangulation = Delaunay(target_points)
    yy, xx = np.mgrid[0:CROP_H, 0:CROP_W]
    query = np.column_stack([xx.ravel(), yy.ravel()]).astype(np.float64)
    simplex = triangulation.find_simplex(query)
    valid = simplex >= 0
    mapped = np.full((query.shape[0], 2), -1000.0, dtype=np.float32)
    transforms = triangulation.transform[simplex[valid], :2]
    offsets = triangulation.transform[simplex[valid], 2]
    delta = query[valid] - offsets
    first = np.einsum('nij,nj->ni', transforms, delta)
    barycentric = np.column_stack([first, 1.0 - first.sum(axis=1)])
    vertices = triangulation.simplices[simplex[valid]]
    mapped[valid] = np.einsum('ni,nij->nj', barycentric, source_points[vertices]).astype(np.float32)
    map_x = mapped[:, 0].reshape(CROP_H, CROP_W)
    map_y = mapped[:, 1].reshape(CROP_H, CROP_W)
    channels = [cv2.remap(source[:, :, channel], map_x, map_y, cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=0) for channel in range(source.shape[2])]
    return np.stack(channels, axis=2)


def resize_premultiplied(rgba: np.ndarray, size: tuple[int, int]) -> np.ndarray:
    alpha = rgba[:, :, 3].astype(np.float32) / 255.0
    rgb = rgba[:, :, :3].astype(np.float32) / 255.0
    premultiplied = rgb * alpha[:, :, None]
    premul_resized = cv2.resize(premultiplied, size, interpolation=cv2.INTER_LANCZOS4)
    alpha_resized = np.clip(cv2.resize(alpha, size, interpolation=cv2.INTER_LANCZOS4), 0.0, 1.0)
    output_rgb = np.zeros_like(premul_resized)
    valid = alpha_resized > 1e-6
    output_rgb[valid] = premul_resized[valid] / alpha_resized[valid, None]
    return np.dstack([np.round(np.clip(output_rgb, 0.0, 1.0) * 255).astype(np.uint8), np.round(alpha_resized * 255).astype(np.uint8)])


def shared_palette(frames: list[Image.Image]) -> list[int]:
    thumbs = [frame.convert('RGB').resize((80, 160), Image.Resampling.BILINEAR) for frame in frames]
    atlas = Image.new('RGB', (80 * 8, 160 * math.ceil(len(thumbs) / 8)), (0, 0, 0))
    for index, image in enumerate(thumbs):
        atlas.paste(image, ((index % 8) * 80, (index // 8) * 160))
    quantized = atlas.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    palette = (quantized.getpalette() or [])[:255 * 3]
    palette.extend([0] * (255 * 3 - len(palette)))
    return palette


def encode_gif(frames: list[Image.Image], path: Path) -> None:
    palette = shared_palette(frames)
    palette_image = Image.new('P', (1, 1))
    palette_image.putpalette(palette + [0, 0, 0])
    full_palette = [0, 0, 0] + palette
    full_palette.extend([0] * (768 - len(full_palette)))
    encoded = []
    for frame in frames:
        rgba = np.asarray(frame.convert('RGBA'), dtype=np.uint8)
        quantized = Image.fromarray(rgba[:, :, :3], 'RGB').quantize(palette=palette_image, dither=Image.Dither.NONE)
        indexes = np.asarray(quantized, dtype=np.uint8).astype(np.uint16) + 1
        indexes[rgba[:, :, 3] <= 10] = 0
        image = Image.fromarray(indexes.astype(np.uint8), 'P')
        image.putpalette(full_palette)
        image.info['transparency'] = 0
        image.info['disposal'] = 2
        encoded.append(image)
    encoded[0].save(path, format='GIF', save_all=True, append_images=encoded[1:], duration=FRAME_DURATION_MS, loop=0, transparency=0, disposal=2, optimize=False, background=0)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for path in OUT.iterdir():
        if path.is_file():
            path.unlink()
    source_full = np.asarray(Image.open(SOURCE_ROOT / 'canonical-rgba.png').convert('RGBA'), dtype=np.uint8)
    source = source_full[CROP_Y0:CROP_Y1, CROP_X0:CROP_X1].copy()
    keypoint_data = json.loads((SOURCE_ROOT / 'keypoints.json').read_text())
    joints = {name: point(value) for name, value in keypoint_data['keypoints'].items()}

    neck = (joints['left_shoulder'] + joints['right_shoulder']) * 0.5
    pelvis = (joints['left_hip'] + joints['right_hip']) * 0.5
    head_center = np.mean([joints['nose'], joints['left_eye'], joints['right_eye'], joints['left_ear'], joints['right_ear']], axis=0)
    source_joints = dict(joints)
    source_joints['neck'] = neck
    source_joints['pelvis'] = pelvis
    source_joints['head_center'] = head_center

    # Rigid head layer: source face/hair pixels are never deformed.
    yy, xx = np.mgrid[0:CROP_H, 0:CROP_W]
    head_rx, head_ry = 82.0, 108.0
    distance = ((xx - head_center[0]) / head_rx) ** 2 + ((yy - (head_center[1] + 3.0)) / head_ry) ** 2
    head_mask = np.clip(1.0 - (distance - 0.70) / 0.30, 0.0, 1.0)
    head_mask = cv2.GaussianBlur(head_mask.astype(np.float32), (0, 0), 3.0)
    source_alpha = source[:, :, 3].astype(np.float32) / 255.0
    head_alpha = source_alpha * head_mask
    body_alpha = source_alpha * (1.0 - head_mask)
    source_rgb = source[:, :, :3].astype(np.float32) / 255.0
    body_premul = np.dstack([source_rgb * body_alpha[:, :, None], body_alpha]).astype(np.float32)
    head_premul = np.dstack([source_rgb * head_alpha[:, :, None], head_alpha]).astype(np.float32)

    descriptors: list[tuple[str, tuple[object, ...]]] = []
    source_points: list[np.ndarray] = []
    seen: set[tuple[int, int]] = set()

    def add(value: np.ndarray, kind: str, *args: object) -> None:
        clipped = np.array([np.clip(value[0], 0.0, CROP_W - 1.0), np.clip(value[1], 0.0, CROP_H - 1.0)], dtype=np.float64)
        key = (int(round(clipped[0] * 10)), int(round(clipped[1] * 10)))
        if key in seen:
            return
        seen.add(key)
        source_points.append(clipped)
        descriptors.append((kind, args))

    # Fixed transparent border anchors.
    for x in [0.0, CROP_W * 0.25, CROP_W * 0.5, CROP_W * 0.75, CROP_W - 1.0]:
        add(np.array([x, 0.0]), 'fixed')
        add(np.array([x, CROP_H - 1.0]), 'fixed')
    for y in [CROP_H * 0.2, CROP_H * 0.4, CROP_H * 0.6, CROP_H * 0.8]:
        add(np.array([0.0, y]), 'fixed')
        add(np.array([CROP_W - 1.0, y]), 'fixed')

    for name, value in source_joints.items():
        add(value, 'joint', name)

    bones = [
        ('left_shoulder', 'left_elbow', 24.0), ('left_elbow', 'left_wrist', 21.0),
        ('right_shoulder', 'right_elbow', 24.0), ('right_elbow', 'right_wrist', 21.0),
        ('left_hip', 'left_knee', 35.0), ('left_knee', 'left_ankle', 31.0),
        ('right_hip', 'right_knee', 35.0), ('right_knee', 'right_ankle', 31.0),
    ]
    for a, b, width in bones:
        for t in [0.22, 0.5, 0.78]:
            for offset in [-width, 0.0, width]:
                add(local_segment_point(source_joints[a], source_joints[b], t, offset), 'segment', a, b)

    torso_source = (source_joints['right_shoulder'], source_joints['left_shoulder'], source_joints['right_hip'], source_joints['left_hip'])
    for u in [0.18, 0.5, 0.82]:
        for v in [0.18, 0.42, 0.68, 0.88]:
            add(bilinear(torso_source, u, v), 'torso', u, v)

    # Extra rigid head controls stabilize the neck/head transition in the body warp.
    for angle in np.linspace(0.0, 2.0 * math.pi, 12, endpoint=False):
        add(head_center + np.array([head_rx * 0.72 * math.cos(angle), head_ry * 0.72 * math.sin(angle)]), 'head')

    source_points_array = np.asarray(source_points, dtype=np.float64)
    lengths = {}
    bend_signs = {}
    for side in ['left', 'right']:
        lengths[f'{side}_thigh'] = float(np.linalg.norm(source_joints[f'{side}_knee'] - source_joints[f'{side}_hip']))
        lengths[f'{side}_shin'] = float(np.linalg.norm(source_joints[f'{side}_ankle'] - source_joints[f'{side}_knee']))
        lengths[f'{side}_upper_arm'] = float(np.linalg.norm(source_joints[f'{side}_elbow'] - source_joints[f'{side}_shoulder']))
        lengths[f'{side}_forearm'] = float(np.linalg.norm(source_joints[f'{side}_wrist'] - source_joints[f'{side}_elbow']))
        leg_line = source_joints[f'{side}_ankle'] - source_joints[f'{side}_hip']
        leg_knee = source_joints[f'{side}_knee'] - source_joints[f'{side}_hip']
        bend_signs[f'{side}_leg'] = 1.0 if np.cross(leg_line, leg_knee) >= 0 else -1.0
        arm_line = source_joints[f'{side}_wrist'] - source_joints[f'{side}_shoulder']
        arm_elbow = source_joints[f'{side}_elbow'] - source_joints[f'{side}_shoulder']
        bend_signs[f'{side}_arm'] = 1.0 if np.cross(arm_line, arm_elbow) >= 0 else -1.0

    base_ground = max(source_joints['left_ankle'][1], source_joints['right_ankle'][1])
    frames: list[Image.Image] = []
    frame_meta: list[dict[str, object]] = []
    aligned_head_hashes: list[str] = []

    for index in range(FRAME_COUNT):
        t = index / FRAME_COUNT
        phase = 2.0 * math.pi * t
        bob_y = -4.0 + 4.0 * math.cos(2.0 * phase)
        sway_x = 3.0 * math.sin(phase)
        hip_angle = math.radians(1.4) * math.sin(phase)
        shoulder_angle = -math.radians(2.2) * math.sin(phase)
        target: dict[str, np.ndarray] = {}

        target_pelvis = pelvis + np.array([sway_x, bob_y])
        target_neck = neck + np.array([-1.6 * sway_x, 0.72 * bob_y])
        for side in ['left', 'right']:
            target[f'{side}_hip'] = target_pelvis + rotate(source_joints[f'{side}_hip'] - pelvis, hip_angle)
            target[f'{side}_shoulder'] = target_neck + rotate(source_joints[f'{side}_shoulder'] - neck, shoulder_angle)

        for side, phase_offset in [('left', 0.0), ('right', 0.5)]:
            q = (t + phase_offset) % 1.0
            horizontal, vertical = gait_offset(q, 22.0, 38.0)
            base_ankle = source_joints[f'{side}_ankle']
            side_direction = 1.0 if side == 'left' else -1.0
            ankle = np.array([base_ankle[0] + horizontal * 0.48 + side_direction * 2.5 * math.sin(phase), base_ground + vertical], dtype=np.float64)
            target[f'{side}_ankle'] = ankle
            target[f'{side}_knee'] = ik_midpoint(
                target[f'{side}_hip'], ankle,
                lengths[f'{side}_thigh'], lengths[f'{side}_shin'], bend_signs[f'{side}_leg'],
            )

        for side, arm_phase in [('left', phase + math.pi), ('right', phase)]:
            source_wrist = source_joints[f'{side}_wrist']
            shoulder_delta = target[f'{side}_shoulder'] - source_joints[f'{side}_shoulder']
            wrist = source_wrist + shoulder_delta + np.array([19.0 * math.sin(arm_phase), -10.0 * math.sin(arm_phase)], dtype=np.float64)
            target[f'{side}_wrist'] = wrist
            target[f'{side}_elbow'] = ik_midpoint(
                target[f'{side}_shoulder'], wrist,
                lengths[f'{side}_upper_arm'], lengths[f'{side}_forearm'], bend_signs[f'{side}_arm'],
            )

        head_translation = np.round(target_neck - neck).astype(np.float64)
        for name in ['nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear', 'head_center']:
            target[name] = source_joints[name] + head_translation
        target['neck'] = target_neck
        target['pelvis'] = target_pelvis

        torso_target = (target['right_shoulder'], target['left_shoulder'], target['right_hip'], target['left_hip'])
        target_points = []
        for source_point, (kind, args) in zip(source_points_array, descriptors):
            if kind == 'fixed':
                destination = source_point
            elif kind == 'joint':
                destination = target[str(args[0])]
            elif kind == 'segment':
                a, b = str(args[0]), str(args[1])
                destination = transform_segment_point(source_joints[a], source_joints[b], target[a], target[b], source_point)
            elif kind == 'torso':
                destination = bilinear(torso_target, float(args[0]), float(args[1]))
            elif kind == 'head':
                destination = source_point + head_translation
            else:
                raise RuntimeError(kind)
            target_points.append(destination)
        target_points_array = np.asarray(target_points, dtype=np.float64)

        warped_body = warp_piecewise(body_premul, source_points_array, target_points_array)
        tx, ty = int(head_translation[0]), int(head_translation[1])
        transform = np.float32([[1.0, 0.0, tx], [0.0, 1.0, ty]])
        warped_head = np.stack([
            cv2.warpAffine(head_premul[:, :, channel], transform, (CROP_W, CROP_H), flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
            for channel in range(4)
        ], axis=2)
        body_alpha_w = np.clip(warped_body[:, :, 3], 0.0, 1.0)
        head_alpha_w = np.clip(warped_head[:, :, 3], 0.0, 1.0)
        composite_alpha = head_alpha_w + body_alpha_w * (1.0 - head_alpha_w)
        composite_premul = warped_head[:, :, :3] + warped_body[:, :, :3] * (1.0 - head_alpha_w[:, :, None])
        composite_rgb = np.zeros_like(composite_premul)
        visible = composite_alpha > 1e-6
        composite_rgb[visible] = composite_premul[visible] / composite_alpha[visible, None]
        rgba = np.dstack([np.round(np.clip(composite_rgb, 0.0, 1.0) * 255).astype(np.uint8), np.round(np.clip(composite_alpha, 0.0, 1.0) * 255).astype(np.uint8)])
        resized = resize_premultiplied(rgba, FINAL_SIZE)
        frame = Image.fromarray(resized, 'RGBA')
        frame.save(OUT / f'frame_{index:02d}.png')
        frames.append(frame)

        # Align the final head crop by the exact integer translation and hash it; it must not change.
        head_box_source = (int(head_center[0] - 70), int(head_center[1] - 95), int(head_center[0] + 70), int(head_center[1] + 95))
        head_box_frame = tuple(int(round(value + (head_translation[0] if position % 2 == 0 else head_translation[1]))) for position, value in enumerate(head_box_source))
        inverse = np.float32([[1.0, 0.0, -tx], [0.0, 1.0, -ty]])
        restored_head = np.stack([
            cv2.warpAffine(warped_head[:, :, channel], inverse, (CROP_W, CROP_H), flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
            for channel in range(4)
        ], axis=2)
        hx0, hy0, hx1, hy1 = head_box_source
        aligned_head = np.ascontiguousarray(restored_head[hy0:hy1, hx0:hx1])
        aligned_head_hashes.append(hashlib.sha256(aligned_head.tobytes()).hexdigest())
        frame_meta.append({
            'frame': index,
            'phase': phase,
            'pelvis': target_pelvis.tolist(),
            'head_translation': head_translation.tolist(),
            'left_ankle': target['left_ankle'].tolist(),
            'right_ankle': target['right_ankle'].tolist(),
            'left_knee': target['left_knee'].tolist(),
            'right_knee': target['right_knee'].tolist(),
            'left_wrist': target['left_wrist'].tolist(),
            'right_wrist': target['right_wrist'].tolist(),
        })

    gif_path = OUT / 'player-walk.gif'
    encode_gif(frames, gif_path)
    with Image.open(gif_path) as image:
        decoded = [frame.copy().convert('RGBA') for frame in ImageSequence.Iterator(image)]
        loop = image.info.get('loop')
        duration = image.info.get('duration')
    arrays = [np.asarray(frame, dtype=np.uint8) for frame in decoded]
    masks = [array[:, :, 3] > 10 for array in arrays]
    adjacent = [float(np.abs(arrays[i].astype(np.int16) - arrays[i - 1].astype(np.int16)).mean()) for i in range(1, len(arrays))]
    loop_difference = float(np.abs(arrays[0].astype(np.int16) - arrays[-1].astype(np.int16)).mean())
    hashes = [hashlib.sha256(array.tobytes()).hexdigest() for array in arrays]
    coverage, border, largest = [], [], []
    for mask in masks:
        coverage.append(float(mask.mean()))
        edges = np.concatenate([mask[:2].ravel(), mask[-2:].ravel(), mask[:, :2].ravel(), mask[:, -2:].ravel()])
        border.append(float(edges.mean()))
        labels, count = ndimage.label(mask, structure=np.ones((3, 3), dtype=bool))
        areas = [int((labels == value).sum()) for value in range(1, count + 1)]
        largest.append(max(areas, default=0) / max(1, int(mask.sum())))

    left_y = [item['left_ankle'][1] for item in frame_meta]
    right_y = [item['right_ankle'][1] for item in frame_meta]
    left_x = [item['left_ankle'][0] for item in frame_meta]
    right_x = [item['right_ankle'][0] for item in frame_meta]
    left_wrist_x = [item['left_wrist'][0] for item in frame_meta]
    right_wrist_x = [item['right_wrist'][0] for item in frame_meta]
    metrics = {
        'generator': 'deterministic piecewise-affine skeletal mesh rig',
        'model_used_for_frames': False,
        'source_sha256': hashlib.sha256((SOURCE_ROOT / 'canonical-rgba.png').read_bytes()).hexdigest(),
        'frame_count': len(decoded),
        'frame_duration_ms': int(duration or 0),
        'loop': loop,
        'dimensions': list(FINAL_SIZE),
        'unique_frames': len(set(hashes)),
        'shared_palette': True,
        'transparent_palette_index': 0,
        'aligned_head_unique_hashes': len(set(aligned_head_hashes)),
        'adjacent_difference_min': min(adjacent),
        'adjacent_difference_max': max(adjacent),
        'adjacent_difference_median': float(np.median(adjacent)),
        'loop_transition_difference': loop_difference,
        'left_foot_horizontal_range_px': max(left_x) - min(left_x),
        'right_foot_horizontal_range_px': max(right_x) - min(right_x),
        'left_foot_vertical_range_px': max(left_y) - min(left_y),
        'right_foot_vertical_range_px': max(right_y) - min(right_y),
        'left_wrist_range_px': max(left_wrist_x) - min(left_wrist_x),
        'right_wrist_range_px': max(right_wrist_x) - min(right_wrist_x),
        'coverage_min': min(coverage),
        'coverage_max': max(coverage),
        'border_visible_max': max(border),
        'largest_component_ratio_min': min(largest),
        'fallback_used': False,
    }
    if len(decoded) != FRAME_COUNT or loop != 0 or int(duration or 0) != FRAME_DURATION_MS:
        raise RuntimeError(metrics)
    if metrics['unique_frames'] != FRAME_COUNT:
        raise RuntimeError('duplicate frames')
    if metrics['aligned_head_unique_hashes'] != 1:
        raise RuntimeError(f"head pixels changed: {metrics['aligned_head_unique_hashes']} aligned hashes")
    if metrics['adjacent_difference_min'] < 0.12 or metrics['adjacent_difference_max'] > 12.0:
        raise RuntimeError(metrics)
    if metrics['loop_transition_difference'] > metrics['adjacent_difference_median'] * 1.9:
        raise RuntimeError(metrics)
    if metrics['left_foot_vertical_range_px'] < 20.0 or metrics['right_foot_vertical_range_px'] < 20.0:
        raise RuntimeError(metrics)
    if metrics['left_foot_horizontal_range_px'] < 15.0 or metrics['right_foot_horizontal_range_px'] < 15.0:
        raise RuntimeError(metrics)
    if metrics['left_wrist_range_px'] < 20.0 or metrics['right_wrist_range_px'] < 20.0:
        raise RuntimeError(metrics)
    if metrics['border_visible_max'] != 0.0 or metrics['largest_component_ratio_min'] < 0.975:
        raise RuntimeError(metrics)
    if metrics['coverage_max'] > 0.55 or metrics['coverage_min'] < 0.10:
        raise RuntimeError(metrics)

    (OUT / 'metrics.json').write_text(json.dumps(metrics, indent=2) + '\n')
    (OUT / 'frame-metadata.json').write_text(json.dumps(frame_meta, indent=2) + '\n')

    # 12-frame dark/light/checker contact sheet.
    sample_indices = [round(i * (FRAME_COUNT - 1) / 11) for i in range(12)]
    cell_w, cell_h = 340, 690
    contact = Image.new('RGB', (6 * cell_w, 6 * cell_h), (45, 45, 45))
    for row_index, (name, color) in enumerate([('checker', None), ('dark', (24, 24, 24, 255)), ('light', (238, 238, 238, 255))]):
        for sample_index, frame_index in enumerate(sample_indices):
            frame = frames[frame_index]
            if color is None:
                background = Image.new('RGBA', frame.size, (210, 210, 210, 255))
                draw = ImageDraw.Draw(background)
                step = 20
                for y in range(0, frame.height, step):
                    for x in range(0, frame.width, step):
                        if (x // step + y // step) % 2:
                            draw.rectangle((x, y, x + step - 1, y + step - 1), fill=(135, 135, 135, 255))
            else:
                background = Image.new('RGBA', frame.size, color)
            background.alpha_composite(frame)
            tile = Image.new('RGB', (cell_w, cell_h), 'white')
            tile.paste(background, ((cell_w - frame.width) // 2, 26))
            ImageDraw.Draw(tile).text((6, 6), f'{name} frame {frame_index}', fill='black')
            row = row_index * 2 + sample_index // 6
            column = sample_index % 6
            contact.paste(tile, (column * cell_w, row * cell_h))
    contact.save(OUT / 'contact.png')
    print(json.dumps({'ok': True, 'gif': str(gif_path), 'metrics': metrics, 'contact': str(OUT / 'contact.png')}, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
