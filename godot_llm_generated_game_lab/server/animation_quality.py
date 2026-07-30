from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageSequence
from scipy import ndimage


@dataclass(frozen=True)
class AnimationQuality:
    frame_count: int
    frame_width: int
    frame_height: int
    distinct_sheet_frames: int
    distinct_gif_frames: int
    coverage: list[float]
    transparent_ratio: list[float]
    border_visible_ratio: list[float]
    largest_component_ratio: list[float]
    center_step_px: list[float]
    adjacent_rgba_diff: list[float]
    first_last_rgba_diff: float
    alpha_intersection_over_union: float
    gif_sheet_coverage_error: list[float]
    gif_sheet_mask_disagreement: list[float]
    soft_alpha_ratio: list[float]
    bbox_width_ratio: list[float]
    bbox_height_ratio: list[float]
    lower_body_change: list[float]
    upper_body_change: list[float]
    looped_gif: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)



def encode_transparent_gif(
    frames: list[Image.Image],
    output: Path,
    *,
    duration_ms: int = 125,
    alpha_threshold: int = 16,
) -> None:
    """Encode RGBA frames with palette index 0 permanently reserved for transparency."""
    if len(frames) < 2:
        raise ValueError("transparent GIF requires at least two frames")
    encoded: list[Image.Image] = []
    expected_size = frames[0].size
    for frame in frames:
        rgba = frame.convert("RGBA")
        if rgba.size != expected_size:
            raise ValueError(f"GIF frame size {rgba.size} differs from {expected_size}")
        array = np.asarray(rgba, dtype=np.uint8)
        alpha = array[:, :, 3]
        rgb = Image.fromarray(array[:, :, :3], "RGB")
        quantized = rgb.quantize(colors=254, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        indices = np.asarray(quantized, dtype=np.uint8).astype(np.uint16) + 1
        indices[alpha <= alpha_threshold] = 0
        indexed = Image.fromarray(indices.astype(np.uint8), "P")
        source_palette = quantized.getpalette() or []
        palette = [0, 0, 0] + source_palette[: 254 * 3]
        palette.extend([0] * (768 - len(palette)))
        indexed.putpalette(palette)
        indexed.info["transparency"] = 0
        indexed.info["disposal"] = 2
        encoded.append(indexed)
    output.parent.mkdir(parents=True, exist_ok=True)
    encoded[0].save(
        output,
        format="GIF",
        save_all=True,
        append_images=encoded[1:],
        duration=duration_ms,
        loop=0,
        disposal=2,
        transparency=0,
        optimize=False,
    )

def _frames_from_sheet(path: Path, count: int, width: int, height: int) -> list[Image.Image]:
    with Image.open(path) as image:
        sheet = image.convert("RGBA")
    if sheet.size != (count * width, height):
        raise ValueError(f"sheet size {sheet.size} does not match {(count * width, height)}")
    return [sheet.crop((index * width, 0, (index + 1) * width, height)) for index in range(count)]


def _frames_from_gif(path: Path) -> tuple[list[Image.Image], bool]:
    with Image.open(path) as image:
        looped = image.info.get("loop") == 0
        frames = [frame.copy().convert("RGBA") for frame in ImageSequence.Iterator(image)]
    return frames, looped


def _mask_metrics(alpha: np.ndarray) -> tuple[float, float, float, tuple[float, float]]:
    visible = alpha > 16
    coverage = float(visible.mean())
    transparent = float((alpha == 0).mean())
    border = np.concatenate((visible[:2, :].ravel(), visible[-2:, :].ravel(), visible[:, :2].ravel(), visible[:, -2:].ravel()))
    border_ratio = float(border.mean())
    labels, count = ndimage.label(visible, structure=np.ones((3, 3), dtype=bool))
    areas = [int((labels == index).sum()) for index in range(1, count + 1)]
    largest_ratio = float(max(areas, default=0) / max(1, int(visible.sum())))
    weights = alpha.astype(np.float64)
    total = float(weights.sum())
    if total:
        yy, xx = np.indices(alpha.shape)
        center = (float((xx * weights).sum() / total), float((yy * weights).sum() / total))
    else:
        center = (0.0, 0.0)
    return coverage, transparent, border_ratio, largest_ratio, center


def analyze_animation(sheet_path: Path, gif_path: Path, frame_count: int, frame_width: int, frame_height: int) -> AnimationQuality:
    sheet_frames = _frames_from_sheet(sheet_path, frame_count, frame_width, frame_height)
    gif_frames, looped = _frames_from_gif(gif_path)
    if len(gif_frames) != frame_count:
        raise ValueError(f"GIF has {len(gif_frames)} frames, expected {frame_count}")
    sheet_arrays = [np.asarray(frame, dtype=np.int16) for frame in sheet_frames]
    gif_arrays = [np.asarray(frame.resize((frame_width, frame_height)), dtype=np.int16) for frame in gif_frames]
    alpha_arrays = [array[:, :, 3].astype(np.uint8) for array in sheet_arrays]
    gif_alpha = [array[:, :, 3].astype(np.uint8) for array in gif_arrays]
    coverage: list[float] = []
    transparent: list[float] = []
    border: list[float] = []
    largest: list[float] = []
    centers: list[tuple[float, float]] = []
    for alpha in alpha_arrays:
        cov, trans, edge, component, center = _mask_metrics(alpha)
        coverage.append(cov)
        transparent.append(trans)
        border.append(edge)
        largest.append(component)
        centers.append(center)
    gif_coverage = [float((alpha > 16).mean()) for alpha in gif_alpha]
    soft_alpha = [float(((alpha > 2) & (alpha < 253)).mean()) for alpha in alpha_arrays]
    mask_disagreement = [float(np.logical_xor(gif_alpha[index] > 16, alpha_arrays[index] > 16).mean()) for index in range(frame_count)]
    center_step = [float(np.linalg.norm(np.asarray(centers[index]) - np.asarray(centers[index - 1]))) for index in range(1, frame_count)]
    adjacent = [float(np.abs(sheet_arrays[index] - sheet_arrays[index - 1]).mean()) for index in range(1, frame_count)]
    visible_masks = [alpha > 16 for alpha in alpha_arrays]
    bboxes=[]
    for mask in visible_masks:
        ys,xs=np.where(mask)
        bboxes.append((int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1) if len(xs) else (0,0,0,0))
    bbox_width=[(box[2]-box[0])/frame_width for box in bboxes]
    bbox_height=[(box[3]-box[1])/frame_height for box in bboxes]
    lower=[];upper=[]
    split=int(frame_height*0.52)
    for index in range(1,frame_count):
        diff=np.abs(sheet_arrays[index]-sheet_arrays[index-1]).mean(axis=2)
        upper.append(float(diff[:split].mean()))
        lower.append(float(diff[split:].mean()))
    union = np.logical_or.reduce(visible_masks)
    intersection = np.logical_and.reduce(visible_masks)
    return AnimationQuality(
        frame_count=frame_count,
        frame_width=frame_width,
        frame_height=frame_height,
        distinct_sheet_frames=len({hashlib.sha256(array.tobytes()).hexdigest() for array in sheet_arrays}),
        distinct_gif_frames=len({hashlib.sha256(array.tobytes()).hexdigest() for array in gif_arrays}),
        coverage=[round(value, 6) for value in coverage],
        transparent_ratio=[round(value, 6) for value in transparent],
        border_visible_ratio=[round(value, 6) for value in border],
        largest_component_ratio=[round(value, 6) for value in largest],
        center_step_px=[round(value, 6) for value in center_step],
        adjacent_rgba_diff=[round(value, 6) for value in adjacent],
        first_last_rgba_diff=round(float(np.abs(sheet_arrays[0] - sheet_arrays[-1]).mean()), 6),
        alpha_intersection_over_union=round(float(intersection.sum() / max(1, union.sum())), 6),
        gif_sheet_coverage_error=[round(abs(gif_coverage[index] - coverage[index]), 6) for index in range(frame_count)],
        gif_sheet_mask_disagreement=[round(value,6) for value in mask_disagreement],
        soft_alpha_ratio=[round(value,6) for value in soft_alpha],
        bbox_width_ratio=[round(value,6) for value in bbox_width],
        bbox_height_ratio=[round(value,6) for value in bbox_height],
        lower_body_change=[round(value,6) for value in lower],
        upper_body_change=[round(value,6) for value in upper],
        looped_gif=looped,
    )


def validate_animation(
    quality: AnimationQuality,
    *,
    transparent: bool,
    loop_required: bool,
    action_clip: bool,
    clip_name: str = "idle",
    require_soft_alpha: bool = False,
) -> list[str]:
    errors: list[str] = []
    if quality.frame_count < 2:
        errors.append("animation must contain at least two frames")
    if not quality.looped_gif:
        errors.append("GIF must loop forever")
    if quality.distinct_sheet_frames < max(2, quality.frame_count // 2):
        errors.append("sprite sheet lacks distinct motion frames")
    if quality.distinct_gif_frames < max(2, quality.frame_count // 2):
        errors.append("GIF lacks distinct motion frames")
    if max(quality.gif_sheet_coverage_error, default=0.0) > 0.08:
        errors.append("GIF transparency does not match the sprite sheet")
    if max(quality.gif_sheet_mask_disagreement, default=0.0) > 0.01:
        errors.append("GIF preview mask disagrees with the runtime sprite sheet")
    if require_soft_alpha and min(quality.soft_alpha_ratio, default=0.0) < 0.005:
        errors.append("runtime sprite sheet lacks recurrent soft-alpha edge pixels")
    if transparent:
        if min(quality.coverage, default=0.0) < 0.015:
            errors.append("subject disappears in at least one frame")
        if max(quality.coverage, default=1.0) > 0.68:
            errors.append("transparent subject occupies too much of the frame")
        if max(quality.border_visible_ratio, default=1.0) > 0.01:
            errors.append("transparent subject touches the frame border")
        if min(quality.largest_component_ratio, default=0.0) < 0.90:
            errors.append("transparent subject is fragmented or contains detached background")
        positive = [value for value in quality.coverage if value > 0]
        if positive and max(positive) / min(positive) > (1.75 if action_clip else 1.35):
            errors.append("alpha coverage changes too much between frames")
        if max(quality.center_step_px, default=0.0) > max(24.0, quality.frame_width * 0.16):
            errors.append("subject position jumps between adjacent frames")
    if max(quality.adjacent_rgba_diff, default=0.0) < 0.35:
        errors.append("animation contains no visible motion")
    if clip_name == "walk":
        if quality.frame_count < 12:
            errors.append("walk cycle must contain at least twelve frames")
        if max(quality.lower_body_change, default=0.0) < 1.5:
            errors.append("walk cycle has no visible lower-body gait motion")
        if sum(value > 1.0 for value in quality.lower_body_change) < max(6, quality.frame_count // 2):
            errors.append("walk cycle does not sustain alternating leg motion")
        if max(quality.bbox_width_ratio, default=0.0) - min(quality.bbox_width_ratio, default=0.0) < 0.015:
            errors.append("walk silhouette does not change width across the gait cycle")
        if max(quality.center_step_px, default=0.0) < 0.15:
            errors.append("walk body center is static")
    if loop_required:
        limit = 4.0 if action_clip else 3.0
        if quality.first_last_rgba_diff > limit:
            errors.append(f"loop does not return to its starting frame: {quality.first_last_rgba_diff:.3f} > {limit:.3f}")
    return errors


def audit_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    root = path.parent.parent
    results: dict[str, Any] = {}
    for asset_id, asset in manifest.get("assets", {}).items():
        clips = asset.get("clips") if isinstance(asset.get("clips"), dict) else {"idle": asset}
        for clip_name, clip in clips.items():
            sheet = root / clip["sheet_path"]
            gif = root / clip["gif_path"]
            quality = analyze_animation(sheet, gif, int(clip["frame_count"]), int(clip["frame_width"]), int(clip["frame_height"]))
            usage = str(asset.get("asset_usage", "isolated_sprite"))
            errors = validate_animation(
                quality,
                transparent=usage not in {"tileable_texture", "background_layer"},
                loop_required=clip_name in {"idle", "walk"},
                action_clip=clip_name not in {"idle", "walk"},
                clip_name=clip_name,
                require_soft_alpha=bool(clip.get("alpha_temporal_model", False)),
            )
            results[f"{asset_id}:{clip_name}"] = {"quality": quality.to_dict(), "errors": errors}
    return results
