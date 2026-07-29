#!/usr/bin/env python3
from __future__ import annotations

import base64
import hashlib
import io
import json
import math
import os
import re
import subprocess
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

HOST = os.environ.get("THOR_IMAGE_HOST", "10.8.0.7")
PORT = int(os.environ.get("THOR_IMAGE_PORT", "15310"))
SDXL_CHECKPOINT = os.environ.get("THOR_SDXL_CHECKPOINT", "/data/models/image/sdxl/sd_xl_base_1.0.safetensors")
CACHE = Path(os.environ.get("THOR_IMAGE_CACHE", "/data/var/llm_game/grounded_asset_cache"))
MAX_BODY_BYTES = int(os.environ.get("THOR_IMAGE_MAX_BODY_BYTES", "131072"))
VLM_BIN = os.environ.get("THOR_VLM_BIN", "/data/src/external/llama.cpp/build/bin/llama-mtmd-cli")
VLM_MODEL = os.environ.get("THOR_VLM_MODEL", "/data/models/vlm/qwen2.5-vl-3b/Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf")
VLM_MMPROJ = os.environ.get("THOR_VLM_MMPROJ", "/data/models/vlm/qwen2.5-vl-3b/mmproj-Qwen2.5-VL-3B-Instruct-Q8_0.gguf")
CACHE.mkdir(parents=True, exist_ok=True)

text_pipeline: Any | None = None
image_pipeline: Any | None = None
loaded_at = 0.0
load_error = ""
generation_lock = threading.Lock()

REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "recognizable": {"type": "boolean"},
        "single_subject": {"type": "boolean"},
        "full_subject": {"type": "boolean"},
        "correct_category": {"type": "boolean"},
        "required_elements_visible": {"type": "boolean"},
        "forbidden_elements_absent": {"type": "boolean"},
        "anatomy_or_geometry": {"type": "string", "enum": ["normal", "minor_error", "major_error"]},
        "grounded_materials": {"type": "boolean"},
        "clean_plain_background": {"type": "boolean"},
        "clear_silhouette": {"type": "boolean"},
        "recognized_subject": {"type": "string", "maxLength": 160},
        "critical_defects": {"type": "array", "items": {"type": "string"}, "maxItems": 8},
        "description": {"type": "string", "maxLength": 500}
    },
    "required": ["recognizable", "single_subject", "full_subject", "correct_category", "required_elements_visible", "forbidden_elements_absent", "anatomy_or_geometry", "grounded_materials", "clean_plain_background", "clear_silhouette", "recognized_subject", "critical_defects", "description"],
    "additionalProperties": False
}
REVIEW_SCHEMA_PATH = CACHE / "grounded_review_schema.json"
REVIEW_SCHEMA_PATH.write_text(json.dumps(REVIEW_SCHEMA, indent=2) + "\n", encoding="utf-8")


def send_json(handler: BaseHTTPRequestHandler, code: int, payload: dict[str, Any]) -> None:
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(raw)))
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("X-Content-Type-Options", "nosniff")
    handler.end_headers()
    try:
        handler.wfile.write(raw)
    except (BrokenPipeError, ConnectionResetError):
        pass


def load_pipelines() -> None:
    global text_pipeline, image_pipeline, loaded_at, load_error
    try:
        import torch
        from diffusers import DPMSolverMultistepScheduler, StableDiffusionXLImg2ImgPipeline, StableDiffusionXLPipeline

        started = time.monotonic()
        text = StableDiffusionXLPipeline.from_single_file(
            SDXL_CHECKPOINT,
            torch_dtype=torch.bfloat16,
            use_safetensors=True,
        )
        text.scheduler = DPMSolverMultistepScheduler.from_config(
            text.scheduler.config,
            use_karras_sigmas=True,
            algorithm_type="dpmsolver++",
        )
        text.to("cuda")
        text.enable_attention_slicing()
        text.set_progress_bar_config(disable=True)
        image = StableDiffusionXLImg2ImgPipeline(**text.components)
        image.set_progress_bar_config(disable=True)
        text_pipeline = text
        image_pipeline = image
        loaded_at = time.time()
        load_error = ""
        print(json.dumps({"event": "loaded", "engine": "sdxl-grounded-img2img", "seconds": round(time.monotonic() - started, 3), "checkpoint": SDXL_CHECKPOINT}), flush=True)
    except Exception as exc:
        load_error = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()[-5000:]}"
        print(json.dumps({"event": "load_error", "error": load_error}), flush=True)


SUPPORTED_KINDS = {
    "player", "npc", "creature", "enemy", "terrain", "surface", "structure", "static_prop",
    "vegetation", "water", "collectible", "loot", "weapon", "armor", "consumable", "vehicle", "light",
    "particle_emitter", "hazard", "portal",
}
CHARACTER_KINDS = {"player", "npc", "creature", "enemy"}


def dimensions_for(kind: str) -> tuple[int, int, int, int, int]:
    if kind in CHARACTER_KINDS:
        return 640, 896, 192, 256, 8
    return 640, 640, 160, 160, 6


def compact(value: Any, maximum: int) -> str:
    return " ".join(str(value or "").split())[:maximum]


def request_key(payload: dict[str, Any]) -> str:
    material = json.dumps({
        "version": "sdxl-grounded-v6-opaque-gif",
        "kind": payload.get("kind"),
        "name": payload.get("name"),
        "structural_prompt": payload.get("structural_prompt"),
        "semantic_prompt": payload.get("semantic_prompt"),
        "negative_prompt": payload.get("negative_prompt"),
        "animation_description": payload.get("animation_description"),
        "expected_labels": payload.get("expected_labels"),
        "review_requirements": payload.get("review_requirements"),
        "asset_usage": payload.get("asset_usage", "isolated_sprite"),
    }, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:24]


def asset_usage(payload: dict[str, Any]) -> str:
    return compact(payload.get("asset_usage", "isolated_sprite"), 40) or "isolated_sprite"


def opaque_asset(payload: dict[str, Any]) -> bool:
    return asset_usage(payload) in {"tileable_texture", "background_layer"}


def background_color(rgb: Any) -> Any:
    import numpy as np
    edge = max(10, min(rgb.shape[0], rgb.shape[1]) // 32)
    samples = np.concatenate([
        rgb[:edge, :, :].reshape(-1, 3), rgb[-edge:, :, :].reshape(-1, 3),
        rgb[:, :edge, :].reshape(-1, 3), rgb[:, -edge:, :].reshape(-1, 3),
    ], axis=0)
    bright = samples[np.min(samples, axis=1) > 180]
    if bright.shape[0] >= max(100, samples.shape[0] // 5):
        samples = bright
    return np.median(samples, axis=0)


def alpha_quality(rgba: Any, bg: Any) -> dict[str, Any]:
    import numpy as np
    from scipy import ndimage
    array = np.asarray(rgba, dtype=np.uint8)
    rgb = array[:, :, :3].astype(np.float32)
    alpha = array[:, :, 3]
    h, w = alpha.shape
    border = np.concatenate([alpha[:4, :].ravel(), alpha[-4:, :].ravel(), alpha[:, :4].ravel(), alpha[:, -4:].ravel()])
    visible = alpha > 8
    partial = (alpha > 8) & (alpha < 247)
    boundary = visible & ~ndimage.binary_erosion(visible, structure=np.ones((3, 3), dtype=bool))
    matte_distance = np.linalg.norm(rgb - bg[None, None, :], axis=2)
    labels, count = ndimage.label(visible, structure=np.ones((3, 3), dtype=bool))
    areas = [int(np.sum(labels == index)) for index in range(1, count + 1)]
    largest = max(areas, default=0)
    total = int(np.sum(visible))
    bbox_y, bbox_x = np.where(visible)
    bbox = [int(bbox_x.min()), int(bbox_y.min()), int(bbox_x.max()) + 1, int(bbox_y.max()) + 1] if total else [0, 0, 0, 0]
    return {
        "transparent_ratio": round(float(np.mean(alpha == 0)), 5),
        "partial_alpha_ratio": round(float(np.mean(partial)), 5),
        "border_visible_ratio": round(float(np.mean(border > 8)), 5),
        "foreground_components": count,
        "largest_component_ratio": round(float(largest) / float(max(1, total)), 5),
        "boundary_matte_ratio": round(float(np.mean(matte_distance[boundary] < 28.0)) if np.any(boundary) else 0.0, 5),
        "bbox": bbox,
    }


def minimum_subject_area(kind: str) -> float:
    return 0.055 if kind in CHARACTER_KINDS else 0.012


def _bridge_mask_components(mask: Any, component: Any, radius: int = 5) -> Any:
    import numpy as np
    from scipy import ndimage
    if not np.any(mask):
        return component.copy()
    distance, nearest = ndimage.distance_transform_edt(~mask, return_indices=True)
    ys, xs = np.where(component)
    if len(xs) == 0:
        return mask
    values = distance[ys, xs]
    index = int(np.argmin(values))
    y1, x1 = int(ys[index]), int(xs[index])
    y0, x0 = int(nearest[0, y1, x1]), int(nearest[1, y1, x1])
    steps = max(abs(y1 - y0), abs(x1 - x0), 1)
    bridge = np.zeros(mask.shape, dtype=bool)
    for step in range(steps + 1):
        fraction = step / steps
        y = int(round(y0 + (y1 - y0) * fraction))
        x = int(round(x0 + (x1 - x0) * fraction))
        y_start, y_end = max(0, y - radius), min(mask.shape[0], y + radius + 1)
        x_start, x_end = max(0, x - radius), min(mask.shape[1], x + radius + 1)
        yy, xx = np.ogrid[y_start:y_end, x_start:x_end]
        bridge[y_start:y_end, x_start:x_end] |= (yy - y) ** 2 + (xx - x) ** 2 <= radius ** 2
    return mask | component | bridge


def alpha_for_frame(image: Any, kind: str = "static_prop") -> tuple[Any, tuple[int, int, int, int], dict[str, Any]]:
    import numpy as np
    from PIL import Image
    from scipy import ndimage

    rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)
    pixels = rgb.astype(np.float32)
    h, w = rgb.shape[:2]
    border_width = max(6, min(h, w) // 80)
    border_pixels = np.concatenate([
        pixels[:border_width, :, :].reshape(-1, 3), pixels[-border_width:, :, :].reshape(-1, 3),
        pixels[:, :border_width, :].reshape(-1, 3), pixels[:, -border_width:, :].reshape(-1, 3),
    ], axis=0)
    border_brightness = border_pixels.mean(axis=1)
    border_saturation = border_pixels.max(axis=1) - border_pixels.min(axis=1)
    bright_neutral_border_ratio = float(np.mean((border_brightness > 145.0) & (border_saturation < 95.0)))
    if bright_neutral_border_ratio < 0.80:
        raise RuntimeError(f"extraction background border is not bright and neutral: {bright_neutral_border_ratio:.4f}")

    bg = background_color(rgb).astype(np.float32)
    distance = np.linalg.norm(pixels - bg[None, None, :], axis=2)
    brightness = pixels.mean(axis=2)
    saturation = pixels.max(axis=2) - pixels.min(axis=2)
    # Only border-connected light neutral pixels are background. White subject details enclosed by the subject survive.
    traversable = (distance < 100.0) | ((brightness > 175.0) & (saturation < 70.0))
    seeds = np.zeros(traversable.shape, dtype=bool)
    seeds[:border_width, :] = traversable[:border_width, :]
    seeds[-border_width:, :] = traversable[-border_width:, :]
    seeds[:, :border_width] = traversable[:, :border_width]
    seeds[:, -border_width:] = traversable[:, -border_width:]
    background = ndimage.binary_propagation(seeds, mask=traversable, structure=np.ones((3, 3), dtype=bool))
    foreground = ~background
    foreground = ndimage.binary_opening(foreground, structure=np.ones((2, 2), dtype=bool))
    foreground = ndimage.binary_closing(foreground, structure=np.ones((3, 3), dtype=bool))
    labels, count = ndimage.label(foreground, structure=np.ones((3, 3), dtype=bool))
    components: list[tuple[float, int, int, float, float]] = []
    minimum_component = max(90, h * w // 5000)
    for index in range(1, count + 1):
        ys, xs = np.where(labels == index)
        area = int(xs.size)
        if area < minimum_component:
            continue
        # Background residue and clipped subjects touching the source frame are never accepted.
        if xs.min() < border_width or xs.max() >= w - border_width or ys.min() < border_width or ys.max() >= h - border_width:
            continue
        cx, cy = float(xs.mean()), float(ys.mean())
        if abs(cx - w / 2) > w * 0.30:
            continue
        centrality = math.hypot((cx - w / 2) / w, (cy - h / 2) / h)
        score = area * (1.4 - min(centrality, 0.9))
        components.append((score, index, area, cx, cy))
    if not components:
        raise RuntimeError("segmentation found no centered non-border subject")
    components.sort(reverse=True)
    _main_score, main_index, main_area, main_cx, _main_cy = components[0]
    keep = labels == main_index
    selected_components = 1
    for _score, index, area, cx, _cy in components[1:]:
        if area < main_area * 0.05 or abs(cx - main_cx) >= w * 0.28:
            continue
        component = labels == index
        distance_to_subject = float(np.min(ndimage.distance_transform_edt(~keep)[component]))
        if distance_to_subject > max(h, w) * 0.12:
            continue
        keep = _bridge_mask_components(keep, component, radius=max(3, min(h, w) // 100))
        selected_components += 1
    keep = ndimage.binary_closing(keep, structure=np.ones((5, 5), dtype=bool), iterations=2)
    keep = ndimage.binary_fill_holes(keep)
    labels_final, final_count = ndimage.label(keep, structure=np.ones((3, 3), dtype=bool))
    final_areas = [int(np.sum(labels_final == index)) for index in range(1, final_count + 1)]
    if not final_areas:
        raise RuntimeError("segmentation produced an empty subject")
    largest_index = int(np.argmax(final_areas)) + 1
    keep = labels_final == largest_index

    # Erode the matte by roughly one pixel and feather inward, eliminating white halos.
    inside = ndimage.distance_transform_edt(keep)
    outside = ndimage.distance_transform_edt(~keep)
    signed = inside - outside
    alpha_f = np.clip((signed - 0.45) / 1.45, 0.0, 1.0)
    alpha_f = ndimage.gaussian_filter(alpha_f, sigma=0.30)
    alpha_f[alpha_f < 0.025] = 0.0
    alpha_f[alpha_f > 0.975] = 1.0
    alpha = np.round(alpha_f * 255.0).astype(np.uint8)

    # Remove the estimated background matte from antialiased edge pixels.
    a = alpha_f[:, :, None]
    denominator = np.maximum(a, 0.08)
    unmatte = (pixels - bg[None, None, :] * (1.0 - a)) / denominator
    unmatte = np.clip(unmatte, 0, 255)
    core = alpha >= 245
    if np.any(core):
        _distance, nearest = ndimage.distance_transform_edt(~core, return_indices=True)
        nearest_rgb = unmatte[nearest[0], nearest[1]]
        edge_weight = np.clip((245.0 - alpha.astype(np.float32)) / 180.0, 0.0, 0.72)[:, :, None]
        unmatte = unmatte * (1.0 - edge_weight) + nearest_rgb * edge_weight
    unmatte[alpha == 0] = 0
    rgba = Image.fromarray(np.dstack([unmatte.astype(np.uint8), alpha]), "RGBA")
    quality = alpha_quality(rgba, bg)
    quality["bright_neutral_border_ratio"] = round(bright_neutral_border_ratio, 5)
    quality["selected_components"] = selected_components
    bbox = tuple(quality["bbox"])
    area_ratio = 1.0 - quality["transparent_ratio"]
    if area_ratio < minimum_subject_area(kind) or area_ratio > 0.58:
        raise RuntimeError(f"subject area ratio is implausible for {kind}: {area_ratio:.4f}")
    if quality["border_visible_ratio"] > 0.0:
        raise RuntimeError(f"subject touches frame border: {quality['border_visible_ratio']:.4f}")
    if quality["largest_component_ratio"] < 0.995:
        raise RuntimeError(f"foreground remains fragmented: {quality['largest_component_ratio']:.4f}")
    if quality["boundary_matte_ratio"] > 0.12:
        raise RuntimeError(f"white matte remains on subject boundary: {quality['boundary_matte_ratio']:.4f}")
    return rgba, bbox, quality


def parse_json_from_log(text: str) -> dict[str, Any]:
    starts = [m.start() for m in re.finditer(r"(?m)^\{", text)]
    for start in reversed(starts):
        candidate = text[start:].strip()
        end = candidate.rfind("}")
        if end < 0:
            continue
        try:
            value = json.loads(candidate[:end + 1])
            if isinstance(value, dict):
                return value
        except json.JSONDecodeError:
            continue
    raise RuntimeError("vision reviewer did not return JSON")


def finalize_review(review: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    kind = compact(payload.get("kind"), 30)
    expected = [compact(value, 80) for value in payload.get("expected_labels", []) if compact(value, 80)]
    character_kind = kind in CHARACTER_KINDS
    usage = asset_usage(payload)
    opaque_mode = opaque_asset(payload)
    materials_pass = review.get("grounded_materials") is True or character_kind
    background_pass = True if opaque_mode else review.get("clean_plain_background") is True
    pass_fields = [
        review.get("recognizable") is True,
        review.get("single_subject") is True,
        review.get("full_subject") is True,
        review.get("correct_category") is True,
        review.get("required_elements_visible") is True,
        review.get("forbidden_elements_absent") is True,
        review.get("anatomy_or_geometry") == "normal",
        materials_pass,
        review.get("clean_plain_background") is True,
        review.get("clear_silhouette") is True,
        review.get("critical_defects") == [],
    ]
    recognized = (str(review.get("recognized_subject", "")) + " " + str(review.get("description", ""))).casefold()
    primary_labels = [label.casefold() for label in expected[:2]]
    label_pass = not primary_labels or any(label in recognized for label in primary_labels)
    review["materials_required"] = not character_kind
    review["materials_pass"] = materials_pass
    review["asset_usage"] = usage
    review["background_mode"] = "opaque_full_frame" if opaque_mode else "transparent_isolated"
    review["background_pass"] = background_pass
    review["deterministic_pass"] = all(pass_fields) and label_pass
    review["label_pass"] = label_pass
    return review


def review_candidate(image: Any, payload: dict[str, Any], key: str, index: int) -> dict[str, Any]:
    review_path = CACHE / f"{key}.candidate-{index}.png"
    image.save(review_path)
    kind = compact(payload.get("kind"), 30)
    expected = [compact(value, 80) for value in payload.get("expected_labels", []) if compact(value, 80)]
    requirements = compact(payload.get("review_requirements"), 900)
    usage = asset_usage(payload)
    usage_instruction = (
        "This is an opaque seamless full-frame material texture; clean_plain_background means the frame contains only the requested material with no border, white margin, scenery, object, or text. "
        if usage in {"tileable_texture", "background_layer"}
        else "This is a transparent isolated asset source; clean_plain_background means a uniform pure-white extraction background with no noise, scenery, shadow field, or gradient. "
    )
    prompt = (
        "Inspect this generated game asset using visible evidence only. The intended asset kind is " + kind + " and usage is " + usage + ". " + usage_instruction +
        "Expected labels: " + ", ".join(expected) + ". Requirements: " + requirements + ". "
        "Set each boolean independently. correct_category is true only if the subject is immediately recognizable as the intended kind. grounded_materials is true for plausible human anatomy, skin, hair, clothing, and accessories on characters, or physically plausible materials on objects. "
        "required_elements_visible is true only if every explicitly required visible element is present and clear. "
        "forbidden_elements_absent is true only if no forbidden duplicate, extra object, malformed part, scenery, text, or watermark is visible. "
        "Return the required JSON only."
    )
    command = [
        VLM_BIN, "-m", VLM_MODEL, "--mmproj", VLM_MMPROJ, "--image", str(review_path),
        "--image-min-tokens", "1024", "--image-max-tokens", "1024",
        "--json-schema-file", str(REVIEW_SCHEMA_PATH), "--temp", "0", "-n", "360", "-c", "8192",
        "--no-perf", "-p", prompt,
    ]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=90, check=False)
    output = (completed.stdout or "") + "\n" + (completed.stderr or "")
    review = parse_json_from_log(output)
    return finalize_review(review, payload)


def generate_canonical(payload: dict[str, Any], key: str) -> tuple[Any, dict[str, Any], int]:
    if text_pipeline is None:
        raise RuntimeError("SDXL pipeline is not loaded")
    import torch

    kind = compact(payload.get("kind"), 30)
    width, height, _fw, _fh, _fc = dimensions_for(kind)
    usage = asset_usage(payload)
    if opaque_asset(payload):
        structural = compact(payload.get("structural_prompt"), 390) + ", seamless edge-to-edge full-frame texture, no border, no margin"
        semantic = compact(payload.get("semantic_prompt"), 820) + " Fill the entire frame with one continuous seamless material sample. No white background, border, perspective scene, isolated object, or text."
        negative = compact(payload.get("negative_prompt"), 900) + ", white border, white margin, frame, isolated object, room scene, horizon, text"
    else:
        structural = compact(payload.get("structural_prompt"), 390) + ", isolated on a pure solid white background"
        semantic = compact(payload.get("semantic_prompt"), 820) + " The complete subject is isolated on a uniform pure white background with no shadow field, scenery, gradient, or noise."
        negative = compact(payload.get("negative_prompt"), 900) + ", gray halo, white halo, noisy background, textured background, shadow field"
    seed_base = int(hashlib.sha256((key + "canonical").encode()).hexdigest()[:8], 16)
    reviews: list[dict[str, Any]] = []
    with generation_lock:
        for index in range(6):
            seed = seed_base + index
            generator = torch.Generator(device="cuda").manual_seed(seed)
            started = time.monotonic()
            image = text_pipeline(
                prompt=structural,
                prompt_2=semantic,
                negative_prompt=negative,
                negative_prompt_2=negative,
                width=width,
                height=height,
                num_inference_steps=32,
                guidance_scale=6.5,
                generator=generator,
            ).images[0]
            review = review_candidate(image, payload, key, index)
            try:
                if opaque_asset(payload):
                    bbox = (0, 0, image.width, image.height)
                    extraction_quality = {"mode": "opaque_full_frame"}
                else:
                    _rgba, bbox, extraction_quality = alpha_for_frame(image, kind)
                extraction_error = ""
            except Exception as exc:
                bbox = (0, 0, 0, 0)
                extraction_quality = {}
                extraction_error = f"{type(exc).__name__}: {exc}"
            review.update({"candidate_index": index, "seed": seed, "seconds": round(time.monotonic() - started, 3), "bbox": list(bbox), "extraction_quality": extraction_quality, "extraction_error": extraction_error})
            reviews.append(review)
            (CACHE / f"{key}.candidate-{index}.review.json").write_text(json.dumps(review, indent=2) + "\n")
            if review["deterministic_pass"] and not extraction_error:
                return image, {"reviews": reviews, "selected_review": review}, seed
    raise RuntimeError("no canonical candidate passed grounded visual review: " + json.dumps(reviews, ensure_ascii=False)[-5000:])


def animation_phases(kind: str, description: str, frame_count: int) -> list[str]:
    description = compact(description, 300)
    if kind in CHARACTER_KINDS:
        phases = ["neutral idle", "slight inhale", "weight shifts forward", "clothing or surface details settle", "neutral idle", "slight exhale", "weight shifts back", "returns to neutral"]
    elif kind in {"collectible", "loot", "static_prop", "structure", "vehicle"}:
        phases = ["still", "small material highlight", "subtle physical settling", "still", "small secondary detail movement", "returns exactly to start"]
    elif kind == "weapon":
        phases = ["held level and still", "subtle material highlight", "very slight angle change", "held level and still", "subtle highlight fades", "returns exactly to start"]
    elif kind == "armor":
        phases = ["hanging still", "slight material settling", "small surface movement", "hanging still", "material settles", "returns exactly to start"]
    elif kind == "consumable":
        phases = ["standing still", "contents shift slightly", "small material highlight", "standing still", "contents settle", "returns exactly to start"]
    elif kind in {"terrain", "surface", "water", "vegetation"}:
        phases = ["stable environmental state", "subtle breeze or ripple", "small texture movement", "stable environmental state", "subtle secondary motion", "returns to start"]
    elif kind in {"light", "particle_emitter", "hazard", "portal"}:
        phases = ["steady effect", "intensity rises slightly", "effect drifts", "steady effect", "intensity falls slightly", "returns to start"]
    else:
        phases = ["still", "subtle natural motion", "still", "subtle natural motion", "still", "returns to start"]
    return [(description + " " + phases[index % len(phases)] + ". Same exact subject, identity, materials, equipment, colors, viewpoint, scale, and plain white background.") for index in range(frame_count)]


def generate_animation(canonical: Any, payload: dict[str, Any], key: str, seed: int) -> tuple[list[Any], dict[str, Any]]:
    if image_pipeline is None:
        raise RuntimeError("SDXL img2img pipeline is not loaded")
    import numpy as np
    import torch

    kind = compact(payload.get("kind"), 30)
    width, height, _fw, _fh, frame_count = dimensions_for(kind)
    if opaque_asset(payload):
        structural = compact(payload.get("structural_prompt"), 390) + ", seamless edge-to-edge full-frame texture, no border, no margin"
        semantic = compact(payload.get("semantic_prompt"), 820) + " Fill the complete frame with the same seamless material."
        negative = compact(payload.get("negative_prompt"), 900) + ", white border, white margin, frame, isolated object, room scene, camera movement, text"
    else:
        structural = compact(payload.get("structural_prompt"), 390) + ", isolated on a pure solid white background"
        semantic = compact(payload.get("semantic_prompt"), 820) + " The complete subject is isolated on a uniform pure white background with no shadow field, scenery, gradient, or noise."
        negative = compact(payload.get("negative_prompt"), 900) + ", changed identity, changed equipment, duplicate subject, camera movement, background change, gray halo, white halo, noisy background"
    phases = animation_phases(kind, compact(payload.get("animation_description"), 350), frame_count)
    frames: list[Any] = [canonical]
    strengths = {"player": 0.16, "npc": 0.16, "creature": 0.16, "enemy": 0.16, "weapon": 0.09, "armor": 0.10, "consumable": 0.10, "terrain": 0.08, "surface": 0.08, "structure": 0.08, "static_prop": 0.10, "vegetation": 0.12, "water": 0.12, "light": 0.14, "particle_emitter": 0.14, "hazard": 0.12, "portal": 0.14}
    strength = strengths.get(kind, 0.11)
    with generation_lock:
        for index in range(1, frame_count):
            generator = torch.Generator(device="cuda").manual_seed(seed + 1000 + index)
            frame = image_pipeline(
                prompt=structural + ", " + phases[index],
                prompt_2=semantic + " " + phases[index],
                negative_prompt=negative,
                negative_prompt_2=negative,
                image=canonical,
                strength=strength,
                num_inference_steps=24,
                guidance_scale=5.5,
                generator=generator,
                width=width,
                height=height,
            ).images[0]
            frames.append(frame)
    arrays = [np.asarray(frame.convert("RGB"), dtype=np.int16) for frame in frames]
    differences = [float(np.abs(arrays[i] - arrays[0]).mean()) for i in range(1, len(arrays))]
    if max(differences, default=0.0) < 0.35:
        raise RuntimeError(f"conditioned animation contains insufficient generated change: {differences}")
    mid_review = review_candidate(frames[len(frames) // 2], payload, key, 100)
    if not mid_review["deterministic_pass"]:
        raise RuntimeError("conditioned animation lost subject identity: " + json.dumps(mid_review, ensure_ascii=False))
    return frames, {"frame_diff_from_source": [round(value, 4) for value in differences], "mid_frame_review": mid_review, "img2img_strength": strength}


def process_frames(raw_frames: list[Any], kind: str, usage: str) -> tuple[list[Any], dict[str, Any]]:
    import numpy as np
    from PIL import Image

    _w, _h, frame_width, frame_height, _count = dimensions_for(kind)
    if usage in {"tileable_texture", "background_layer"}:
        output = [frame.convert("RGB").resize((frame_width, frame_height), Image.Resampling.LANCZOS).convert("RGBA") for frame in raw_frames]
        arrays = [np.asarray(frame, dtype=np.int16) for frame in output]
        diffs = [float(np.abs(arrays[i] - arrays[i - 1]).mean()) for i in range(1, len(arrays))]
        if max(diffs, default=0.0) < 0.12:
            raise RuntimeError(f"opaque texture frames contain no measurable motion: {diffs}")
        return output, {
            "mode": "opaque_full_frame",
            "source_crop": [0, 0, raw_frames[0].width, raw_frames[0].height],
            "alpha_extrema": [[255, 255] for _ in output],
            "processed_frame_diff": [round(value, 4) for value in diffs],
        }
    keyed: list[Any] = []
    boxes: list[tuple[int, int, int, int]] = []
    qualities: list[dict[str, Any]] = []
    for frame in raw_frames:
        rgba, bbox, quality = alpha_for_frame(frame, kind)
        keyed.append(rgba)
        boxes.append(bbox)
        qualities.append(quality)
    x0 = max(0, min(box[0] for box in boxes) - 18)
    y0 = max(0, min(box[1] for box in boxes) - 18)
    x1 = min(keyed[0].width, max(box[2] for box in boxes) + 18)
    y1 = min(keyed[0].height, max(box[3] for box in boxes) + 18)
    crop_width, crop_height = max(1, x1 - x0), max(1, y1 - y0)
    margin = 28 if kind in CHARACTER_KINDS else 24
    scale = min((frame_width - margin * 2) / crop_width, (frame_height - margin * 2) / crop_height)
    target_width = max(1, int(round(crop_width * scale)))
    target_height = max(1, int(round(crop_height * scale)))
    output: list[Any] = []
    final_qualities: list[dict[str, Any]] = []
    for rgba in keyed:
        crop = rgba.crop((x0, y0, x1, y1)).resize((target_width, target_height), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (frame_width, frame_height), (0, 0, 0, 0))
        canvas.alpha_composite(crop, ((frame_width - target_width) // 2, frame_height - target_height - margin))
        output.append(canvas)
        final_qualities.append(alpha_quality(canvas, np.array([255.0, 255.0, 255.0], dtype=np.float32)))
    alpha = [frame.getchannel("A").getextrema() for frame in output]
    if not all(value == (0, 255) for value in alpha):
        raise RuntimeError(f"transparent frame validation failed: {alpha}")
    for index, quality in enumerate(final_qualities):
        if quality["border_visible_ratio"] > 0.0:
            raise RuntimeError(f"processed frame {index} touches border: {quality}")
        if quality["boundary_matte_ratio"] > 0.12:
            raise RuntimeError(f"processed frame {index} retains matte contamination: {quality}")
        if quality["largest_component_ratio"] < 0.96:
            raise RuntimeError(f"processed frame {index} remains fragmented: {quality}")
    arrays = [np.asarray(frame, dtype=np.int16) for frame in output]
    diffs = [float(np.abs(arrays[i] - arrays[i - 1]).mean()) for i in range(1, len(arrays))]
    if max(diffs, default=0.0) < 0.15:
        raise RuntimeError(f"processed frames contain no measurable motion: {diffs}")
    return output, {
        "mode": "transparent_isolated_clean",
        "source_crop": [x0, y0, x1, y1],
        "alpha_extrema": [[0, 255] for _ in output],
        "source_alpha_quality": qualities,
        "final_alpha_quality": final_qualities,
        "processed_frame_diff": [round(value, 4) for value in diffs],
    }


def encode_assets(frames: list[Any], usage: str) -> tuple[bytes, bytes, bytes]:
    from PIL import Image
    png = io.BytesIO(); frames[0].save(png, format="PNG")
    gif = io.BytesIO()
    if usage in {"tileable_texture", "background_layer"}:
        opaque_frames = [frame.convert("RGB") for frame in frames]
        opaque_frames[0].save(
            gif,
            format="GIF",
            save_all=True,
            append_images=opaque_frames[1:],
            duration=120,
            loop=0,
            disposal=2,
            optimize=False,
        )
    else:
        frames[0].save(
            gif,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=120,
            loop=0,
            disposal=2,
            transparency=0,
            optimize=False,
        )
    sheet_background = (0, 0, 0, 255) if usage in {"tileable_texture", "background_layer"} else (0, 0, 0, 0)
    sheet = Image.new("RGBA", (frames[0].width * len(frames), frames[0].height), sheet_background)
    for index, frame in enumerate(frames):
        sheet.alpha_composite(frame, (index * frame.width, 0))
    sheet_buffer = io.BytesIO(); sheet.save(sheet_buffer, format="PNG")
    return png.getvalue(), gif.getvalue(), sheet_buffer.getvalue()


def validate_encoded(gif: bytes, sheet: bytes, expected_frames: int, frame_width: int, frame_height: int, usage: str) -> dict[str, Any]:
    from PIL import Image
    with Image.open(io.BytesIO(gif)) as image:
        if image.n_frames != expected_frames or image.info.get("loop") != 0:
            raise RuntimeError("GIF frame count or loop metadata failed")
        alpha = []
        hashes = []
        for index in range(image.n_frames):
            image.seek(index); frame = image.convert("RGBA")
            alpha.append(frame.getchannel("A").getextrema())
            hashes.append(hashlib.sha256(frame.tobytes()).hexdigest())
        expected_alpha = (255, 255) if usage in {"tileable_texture", "background_layer"} else (0, 255)
        if not all(value == expected_alpha for value in alpha):
            raise RuntimeError(f"GIF alpha mode failed: expected {expected_alpha}, got {alpha}")
        if len(set(hashes)) < max(3, expected_frames // 2):
            raise RuntimeError("GIF does not contain enough distinct generated frames")
    with Image.open(io.BytesIO(sheet)) as image:
        expected_alpha = (255, 255) if usage in {"tileable_texture", "background_layer"} else (0, 255)
        if image.mode != "RGBA" or image.size != (frame_width * expected_frames, frame_height) or image.getchannel("A").getextrema() != expected_alpha:
            raise RuntimeError(f"sprite sheet validation failed for usage {usage}")
    return {"gif_frames": expected_frames, "distinct_gif_frames": len(set(hashes)), "gif_alpha": [list(expected_alpha) for _ in alpha], "sheet_alpha": list(expected_alpha), "asset_usage": usage}


def paths_for(key: str) -> dict[str, Path]:
    return {"png": CACHE / f"{key}.png", "gif": CACHE / f"{key}.gif", "sheet": CACHE / f"{key}.sheet.png", "meta": CACHE / f"{key}.json"}


def canonical_paths_for(key: str) -> dict[str, Path]:
    return {"png": CACHE / f"{key}.canonical-source.png", "meta": CACHE / f"{key}.canonical-source.json"}


def generate_canonical_only(payload: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    key = request_key(payload)
    paths = canonical_paths_for(key)
    if paths["png"].exists() and paths["meta"].exists():
        meta = json.loads(paths["meta"].read_text(encoding="utf-8"))
        meta["cached"] = True
        return paths["png"].read_bytes(), meta
    started = time.monotonic()
    image, review_meta, seed = generate_canonical(payload, key)
    output = io.BytesIO()
    image.convert("RGB").save(output, format="PNG")
    png = output.getvalue()
    meta = {
        "ok": True,
        "cached": False,
        "key": key,
        "engine": "sdxl-base-reviewed-canonical",
        "kind": compact(payload.get("kind"), 30),
        "asset_usage": asset_usage(payload),
        "name": compact(payload.get("name"), 100),
        "width": image.width,
        "height": image.height,
        "canonical_seed": seed,
        "generation_seconds": round(time.monotonic() - started, 3),
        "canonical_review": review_meta,
        "source_has_alpha": False,
        "fallback_used": False,
        "png_path": str(paths["png"]),
    }
    paths["png"].write_bytes(png)
    paths["meta"].write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return png, meta


def generate(payload: dict[str, Any]) -> tuple[bytes, bytes, bytes, dict[str, Any]]:
    key = request_key(payload)
    paths = paths_for(key)
    if all(path.exists() for path in paths.values()):
        meta = json.loads(paths["meta"].read_text(encoding="utf-8")); meta["cached"] = True
        return paths["png"].read_bytes(), paths["gif"].read_bytes(), paths["sheet"].read_bytes(), meta
    started = time.monotonic()
    canonical, review_meta, seed = generate_canonical(payload, key)
    raw_frames, animation_meta = generate_animation(canonical, payload, key, seed)
    kind = compact(payload.get("kind"), 30)
    usage = asset_usage(payload)
    frames, processing_meta = process_frames(raw_frames, kind, usage)
    png, gif, sheet = encode_assets(frames, usage)
    _w, _h, fw, fh, count = dimensions_for(kind)
    encoded_meta = validate_encoded(gif, sheet, count, fw, fh, usage)
    meta = {
        "ok": True, "cached": False, "key": key, "engine": "sdxl-base-canonical+sdxl-img2img-animation",
        "identity_anchored": True, "motion_generated": True, "kind": kind, "asset_usage": usage, "name": compact(payload.get("name"), 100),
        "frame_count": count, "frame_width": fw, "frame_height": fh, "frame_duration_ms": 120,
        "generation_seconds": round(time.monotonic() - started, 3), "canonical_seed": seed,
        "canonical_review": review_meta, "animation": animation_meta, "processing": processing_meta, "validation": encoded_meta,
        "png_path": str(paths["png"]), "gif_path": str(paths["gif"]), "sheet_path": str(paths["sheet"]),
    }
    paths["png"].write_bytes(png); paths["gif"].write_bytes(gif); paths["sheet"].write_bytes(sheet)
    paths["meta"].write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return png, gif, sheet, meta


class Handler(BaseHTTPRequestHandler):
    server_version = "ThorGroundedRPGAssets/3.0"
    def log_message(self, fmt: str, *args: Any) -> None:
        print(json.dumps({"event": "access", "path": self.path, "message": fmt % args}), flush=True)
    def do_GET(self) -> None:
        if self.path.split("?", 1)[0] == "/health":
            send_json(self, 200 if text_pipeline is not None else 503, {"ok": text_pipeline is not None, "loaded": text_pipeline is not None, "engine": "sdxl-base-canonical+sdxl-img2img-animation", "identity_anchored": True, "motion_generated": True, "checkpoint": SDXL_CHECKPOINT, "routes": ["/canonical", "/generate"], "canonical_engine": "sdxl-base-reviewed-canonical", "loaded_at": loaded_at, "load_error": load_error, "time": time.time()})
            return
        send_json(self, 404, {"ok": False, "error": "not found"})
    def do_POST(self) -> None:
        route = self.path.split("?", 1)[0]
        if route not in {"/generate", "/canonical"}:
            send_json(self, 404, {"ok": False, "error": "not found"}); return
        try:
            length = int(self.headers.get("Content-Length", "0") or "0")
            if length < 1 or length > MAX_BODY_BYTES:
                send_json(self, 413, {"ok": False, "error": "invalid request size"}); return
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            payload.setdefault("asset_usage", "isolated_sprite")
            required = ["kind", "name", "structural_prompt", "semantic_prompt", "negative_prompt", "animation_description", "expected_labels", "review_requirements"]
            missing = [key for key in required if key not in payload]
            if missing:
                send_json(self, 400, {"ok": False, "error": "missing fields", "missing": missing}); return
            if payload["kind"] not in SUPPORTED_KINDS:
                send_json(self, 400, {"ok": False, "error": "unsupported kind", "supported": sorted(SUPPORTED_KINDS)}); return
            if route == "/canonical":
                png, meta = generate_canonical_only(payload)
                send_json(self, 200, {"ok": True, "png_b64": base64.b64encode(png).decode("ascii"), **meta})
                return
            png, gif, sheet, meta = generate(payload)
            send_json(self, 200, {"ok": True, "png_b64": base64.b64encode(png).decode("ascii"), "gif_b64": base64.b64encode(gif).decode("ascii"), "sheet_b64": base64.b64encode(sheet).decode("ascii"), **meta})
        except Exception as exc:
            send_json(self, 500, {"ok": False, "error": f"{type(exc).__name__}: {exc}", "trace": traceback.format_exc()[-5000:]})


def main() -> int:
    load_pipelines()
    print(json.dumps({"event": "listening", "host": HOST, "port": PORT, "checkpoint": SDXL_CHECKPOINT}), flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
