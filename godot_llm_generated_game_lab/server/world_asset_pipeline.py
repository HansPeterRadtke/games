from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from PIL import Image, ImageSequence

THOR_ASSET_URL = os.environ.get("LLM_GAME_THOR_ASSET_URL", "http://10.8.0.7:15310/generate")
THOR_ASSET_TIMEOUT = float(os.environ.get("LLM_GAME_THOR_ASSET_TIMEOUT", "900"))

VISUAL_KINDS = {
    "player", "npc", "creature", "enemy", "terrain", "surface", "structure", "static_prop",
    "vegetation", "water", "collectible", "weapon", "armor", "consumable", "vehicle", "light",
    "particle_emitter", "hazard", "portal",
}
CHARACTER_KINDS = {"player", "npc", "creature", "enemy"}


def safe_id(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return slug[:60] or "asset"


def _compact(value: Any, maximum: int) -> str:
    return " ".join(str(value or "").split())[:maximum]


def _expected_labels(entry: dict[str, Any], kind: str) -> list[str]:
    name = _compact(entry.get("name"), 80)
    description = _compact(entry.get("description"), 260).casefold()
    labels: list[str] = []
    if kind == "player":
        labels.extend(["adult human", "adult child"])
    elif kind == "npc":
        if "mother" in (name + " " + description).casefold() or "mom" in (name + " " + description).casefold():
            labels.extend(["mother", "adult woman"])
        else:
            labels.extend([name, "adult human"])
    elif kind in {"creature", "enemy"}:
        labels.extend([name, kind])
    else:
        labels.append(name)
        readable_kind = kind.replace("_", " ")
        if readable_kind not in name.casefold():
            labels.append(readable_kind)
    return [label for label in labels if label][:3]


def _structural_prompt(entry: dict[str, Any], kind: str) -> str:
    name = _compact(entry.get("name"), 100)
    usage = _compact(entry.get("visual_usage"), 40)
    if kind in CHARACTER_KINDS:
        return (
            f"single full-body {kind} game character representing {name}, readable side or three-quarter view, "
            "complete body and feet visible, centered composition, normal anatomy, clean silhouette"
        )
    if usage == "tileable_texture":
        return (
            f"seamless square game material texture representing {name}, edge-to-edge continuous surface, "
            "orthographic flat view, no border, no margin, no surrounding scene, no isolated object"
        )
    if usage == "effect_sprite":
        return (
            f"single isolated game effect sprite representing {name}, complete effect visible, centered, "
            "clear silhouette, no surrounding scene"
        )
    return (
        f"single isolated {kind.replace('_', ' ')} game asset representing {name}, complete object visible, "
        "front three-quarter view, centered, realistic proportions, clean readable silhouette"
    )


def build_asset_payload(entry: dict[str, Any], *, is_player: bool = False) -> dict[str, Any]:
    kind = "player" if is_player else _compact(entry.get("type"), 30)
    if kind not in VISUAL_KINDS:
        raise ValueError(f"unsupported generated visual kind {kind!r}")
    name = _compact(entry.get("name"), 100)
    if len(name) < 2:
        raise ValueError("generated visual is missing a usable name")
    usage = "character_sprite" if is_player else _compact(entry.get("visual_usage"), 40)
    if usage not in {"character_sprite", "isolated_sprite", "effect_sprite", "tileable_texture", "background_layer"}:
        raise ValueError(f"unsupported generated visual usage {usage!r}")
    asset_prompt = _compact(entry.get("asset_prompt"), 700)
    description = _compact(entry.get("description"), 360)
    animation = _compact(entry.get("animation"), 300).replace("_", " ")
    if len(asset_prompt.split()) < 5:
        raise ValueError(f"{name} has an underspecified asset prompt")
    if len(animation.split()) < 2:
        raise ValueError(f"{name} has an underspecified animation description")
    expected = _expected_labels(entry, kind)
    readable_kind = kind.replace("_", " ")
    if usage in {"tileable_texture", "background_layer"}:
        review = (
            f"One seamless edge-to-edge full-frame material texture for {name}. The entire frame must contain only the requested material: {asset_prompt}. "
            "No white border, white margin, transparent cutout, isolated object, perspective room scene, horizon, text, logo, watermark, or framing. "
            "The material must remain recognizable, continuous at every edge, physically plausible, and suitable for tiling across a game surface."
        )
        negative = (
            "white border, white margin, transparent cutout, isolated object, centered object, room scene, landscape, horizon, "
            "perspective, frame, text, letters, numbers, logo, watermark, blur, low detail, broken tiling, seam"
        )
    else:
        review = (
            f"Exactly one immediately recognizable {readable_kind} named {name}. The complete subject must be visible. "
            f"It must satisfy this visual request: {asset_prompt}. "
            "Normal anatomy or geometry, plausible materials, uniform pure-white extraction background, clean silhouette, "
            "no halo, background noise, shadow field, second subject, scenery, text, logo, watermark, cropped subject, duplicate parts, or malformed structure."
        )
        negative = (
            "second subject, duplicate subject, extra limbs, missing limbs, malformed anatomy, malformed geometry, cropped subject, cut off edges, "
            "scenery, room background, landscape background, gray halo, white halo, background noise, textured background, shadow field, gradient, "
            "text, letters, numbers, logo, watermark, blur, low detail, abstract replacement, wrong category"
        )
    return {
        "kind": kind,
        "asset_usage": usage,
        "name": name,
        "structural_prompt": _structural_prompt(entry, kind),
        "semantic_prompt": asset_prompt,
        "negative_prompt": negative,
        "animation_description": animation,
        "expected_labels": expected,
        "review_requirements": review,
        "source_description": description,
    }


def _post_generate(payload: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        THOR_ASSET_URL,
        data=json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=THOR_ASSET_TIMEOUT) as response:
            value = json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        raise RuntimeError(f"Thor image service HTTP {exc.code}: {detail}") from exc
    if not isinstance(value, dict) or value.get("ok") is not True:
        raise RuntimeError(f"Thor image service rejected the generated visual: {value!r}")
    return value


def verify_asset_files(png_path: Path, gif_path: Path, sheet_path: Path, meta: dict[str, Any]) -> dict[str, Any]:
    frame_count = int(meta.get("frame_count", 0))
    frame_width = int(meta.get("frame_width", 0))
    frame_height = int(meta.get("frame_height", 0))
    usage = str(meta.get("asset_usage", "isolated_sprite"))
    opaque = usage in {"tileable_texture", "background_layer"}
    expected_alpha = (255, 255) if opaque else (0, 255)
    if frame_count < 6 or frame_width < 64 or frame_height < 64:
        raise RuntimeError("Thor asset metadata has invalid frame geometry")
    with Image.open(png_path) as image:
        png_mode = image.mode
        png_size = image.size
        png_rgba = image.convert("RGBA")
        png_alpha = png_rgba.getchannel("A").getextrema()
    with Image.open(gif_path) as image:
        frames = [frame.copy().convert("RGBA") for frame in ImageSequence.Iterator(image)]
        gif_loop = image.info.get("loop")
    hashes = {hashlib.sha256(frame.tobytes()).hexdigest() for frame in frames}
    gif_alpha = [frame.getchannel("A").getextrema() for frame in frames]
    with Image.open(sheet_path) as image:
        sheet_mode = image.mode
        sheet_size = image.size
        sheet_rgba = image.convert("RGBA")
        sheet_alpha = sheet_rgba.getchannel("A").getextrema()
    canonical = meta.get("canonical_review", {}).get("selected_review", {})
    animation = meta.get("animation", {}).get("mid_frame_review", {})
    processing = meta.get("processing", {})
    failures: list[str] = []
    if png_mode != "RGBA" or png_alpha != expected_alpha:
        failures.append(f"canonical PNG alpha mode failed for {usage}: {png_alpha}")
    if len(frames) != frame_count or gif_loop != 0:
        failures.append("GIF frame count or loop failed")
    if len(hashes) < max(3, frame_count // 2):
        failures.append("GIF lacks enough distinct generated frames")
    if any(alpha != expected_alpha for alpha in gif_alpha):
        failures.append(f"GIF alpha mode failed for {usage}: {gif_alpha}")
    if sheet_mode != "RGBA" or sheet_size != (frame_count * frame_width, frame_height) or sheet_alpha != expected_alpha:
        failures.append(f"sprite sheet validation failed for {usage}")
    if canonical.get("deterministic_pass") is not True:
        failures.append("canonical visual review failed")
    if animation.get("deterministic_pass") is not True:
        failures.append("animation visual review failed")
    if meta.get("identity_anchored") is not True or meta.get("motion_generated") is not True:
        failures.append("identity-anchored generated motion metadata failed")
    if opaque:
        if processing.get("mode") != "opaque_full_frame":
            failures.append("surface texture was not processed as opaque full-frame")
    else:
        if processing.get("mode") != "transparent_isolated_clean":
            failures.append("isolated asset was not processed with clean transparency")
        quality = processing.get("final_alpha_quality", [])
        if len(quality) != frame_count:
            failures.append("clean-alpha quality metadata is missing")
        for index, item in enumerate(quality):
            if float(item.get("border_visible_ratio", 1.0)) > 0.0:
                failures.append(f"frame {index} touches the border")
            if float(item.get("boundary_matte_ratio", 1.0)) > 0.12:
                failures.append(f"frame {index} retains white matte")
            if float(item.get("largest_component_ratio", 0.0)) < 0.96:
                failures.append(f"frame {index} contains detached background noise")
    if failures:
        raise RuntimeError("; ".join(failures))
    return {
        "asset_usage": usage,
        "alpha_mode": "opaque" if opaque else "transparent_clean",
        "png_mode": png_mode,
        "png_size": list(png_size),
        "png_alpha": list(png_alpha),
        "gif_frames": len(frames),
        "gif_distinct_frames": len(hashes),
        "gif_alpha": [list(value) for value in gif_alpha],
        "sheet_mode": sheet_mode,
        "sheet_size": list(sheet_size),
        "sheet_alpha": list(sheet_alpha),
        "canonical_subject": canonical.get("recognized_subject"),
        "canonical_pass": True,
        "animation_pass": True,
        "processing_mode": processing.get("mode"),
        "alpha_quality": processing.get("final_alpha_quality", []),
    }


def generate_one(entry: dict[str, Any], output_dir: Path, *, is_player: bool = False) -> dict[str, Any]:
    object_id = _compact(entry.get("id"), 80)
    if not object_id:
        raise ValueError("generated visual has no id")
    target = output_dir / safe_id(object_id)
    target.mkdir(parents=True, exist_ok=True)
    payload = build_asset_payload(entry, is_player=is_player)
    payload_text = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    payload_hash = hashlib.sha256(payload_text.encode("utf-8")).hexdigest()
    request_path = target / "request.json"
    png_path = target / "canonical.png"
    gif_path = target / "animation.gif"
    sheet_path = target / "animation.sheet.png"
    metadata_path = target / "asset.json"
    existing_request = request_path.read_text(encoding="utf-8") if request_path.exists() else ""
    if metadata_path.exists() and png_path.exists() and gif_path.exists() and sheet_path.exists() and existing_request == payload_text:
        existing = json.loads(metadata_path.read_text(encoding="utf-8"))
        verify_asset_files(png_path, gif_path, sheet_path, {
            "frame_count": existing.get("frame_count"),
            "frame_width": existing.get("frame_width"),
            "frame_height": existing.get("frame_height"),
            "asset_usage": existing.get("asset_usage"),
            "canonical_review": {"selected_review": existing.get("review", {}).get("canonical", {})},
            "animation": {"mid_frame_review": existing.get("review", {}).get("animation", {})},
            "processing": existing.get("processing", {}),
            "identity_anchored": existing.get("identity_anchored"),
            "motion_generated": existing.get("motion_generated"),
        })
        existing["cached_local"] = True
        return existing
    request_path.write_text(payload_text, encoding="utf-8")
    value = _post_generate(payload)
    png_path.write_bytes(base64.b64decode(value.pop("png_b64"), validate=True))
    gif_path.write_bytes(base64.b64decode(value.pop("gif_b64"), validate=True))
    sheet_path.write_bytes(base64.b64decode(value.pop("sheet_b64"), validate=True))
    verification = verify_asset_files(png_path, gif_path, sheet_path, value)
    metadata = {
        "id": object_id,
        "kind": payload["kind"],
        "asset_usage": payload["asset_usage"],
        "name": payload["name"],
        "request_sha256": payload_hash,
        "png_path": str(png_path),
        "gif_path": str(gif_path),
        "sheet_path": str(sheet_path),
        "frame_count": int(value["frame_count"]),
        "frame_width": int(value["frame_width"]),
        "frame_height": int(value["frame_height"]),
        "frame_duration_ms": int(value["frame_duration_ms"]),
        "engine": value.get("engine"),
        "key": value.get("key"),
        "cached": value.get("cached"),
        "generation_seconds": value.get("generation_seconds"),
        "identity_anchored": value.get("identity_anchored"),
        "motion_generated": value.get("motion_generated"),
        "processing": value.get("processing", {}),
        "verification": verification,
        "review": {
            "canonical": value.get("canonical_review", {}).get("selected_review", {}),
            "animation": value.get("animation", {}).get("mid_frame_review", {}),
        },
    }
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return metadata


def compile_world_assets(bundle_path: Path, output_dir: Path, runtime_manifest_path: Path) -> dict[str, Any]:
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    plan = bundle.get("scene_plan")
    if not isinstance(plan, dict):
        raise RuntimeError("world bundle has no validated scene plan")
    if plan.get("visual_generator") != "thor_sdxl":
        raise RuntimeError("world plan does not require the real Thor SDXL generator")
    entries: list[tuple[dict[str, Any], bool]] = [(plan["player"], True)]
    for entry in plan.get("objects", []):
        if isinstance(entry, dict) and entry.get("visual_usage") != "none":
            entries.append((entry, False))
    assets: dict[str, Any] = {}
    started = time.monotonic()
    for index, (entry, is_player) in enumerate(entries, 1):
        object_id = str(entry.get("id", ""))
        print(json.dumps({"event": "asset_start", "index": index, "total": len(entries), "id": object_id, "kind": "player" if is_player else entry.get("type")}, ensure_ascii=False), flush=True)
        asset = generate_one(entry, output_dir, is_player=is_player)
        project_root = runtime_manifest_path.parent.parent.resolve()
        for key in ("png_path", "gif_path", "sheet_path"):
            absolute = Path(str(asset[key])).resolve()
            try:
                relative = absolute.relative_to(project_root)
            except ValueError as exc:
                raise RuntimeError(f"generated asset {absolute} is outside Godot project {project_root}") from exc
            asset[key.replace("_path", "_resource")] = "res://" + relative.as_posix()
        assets[object_id] = asset
        interim = {
            "version": 1,
            "user_prompt": bundle.get("user_prompt"),
            "game_description": bundle.get("game_description"),
            "opening_scene": bundle.get("opening_scene"),
            "scene_plan": plan,
            "assets": assets,
            "complete": False,
            "fallback_used": False,
        }
        runtime_manifest_path.parent.mkdir(parents=True, exist_ok=True)
        runtime_manifest_path.write_text(json.dumps(interim, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"event": "asset_ready", "index": index, "total": len(entries), "id": object_id, "seconds": asset.get("generation_seconds"), "cached": asset.get("cached"), "gif": asset.get("gif_path")}, ensure_ascii=False), flush=True)
    manifest = {
        "version": 1,
        "user_prompt": bundle.get("user_prompt"),
        "game_description": bundle.get("game_description"),
        "opening_scene": bundle.get("opening_scene"),
        "scene_plan": plan,
        "assets": assets,
        "complete": True,
        "fallback_used": False,
        "asset_engine": "thor-sdxl-reviewed-identity-anchored-animation",
        "compiled_seconds": round(time.monotonic() - started, 3),
    }
    runtime_manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest
