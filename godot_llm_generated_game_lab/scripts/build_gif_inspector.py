#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import html
import json
import shutil
from pathlib import Path

from PIL import Image, ImageSequence

ROOT = Path(__file__).resolve().parents[1]
APPROVED = ROOT / "docs" / "verification" / "2026-07-30" / "player-walk-rig"
OUTPUT = ROOT / "web" / "gif_inspector"
GIF_DIR = OUTPUT / "gifs"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_bundle() -> tuple[dict[str, object], Path]:
    manifest = json.loads((APPROVED / "manifest.json").read_text())
    if manifest.get("ok") is not True or manifest.get("benchmark") != "deterministic-player-walk":
        raise RuntimeError("approved player-walk bundle is invalid")
    if manifest.get("model_used_for_frames") is not False:
        raise RuntimeError("approved walk unexpectedly used a frame-generation model")
    for relative, expected in manifest["files"].items():
        path = APPROVED / relative
        if not path.is_file():
            raise RuntimeError(f"missing approved file: {relative}")
        if path.stat().st_size != expected["bytes"] or sha256(path) != expected["sha256"]:
            raise RuntimeError(f"approved file hash mismatch: {relative}")
    metrics = manifest["metrics"]
    review = manifest["review"]
    pose = manifest["dwpose_metrics"]
    required_true = [
        "same_person", "head_complete", "face_visible", "face_stable", "hands_complete",
        "feet_complete", "coherent_walk", "alternating_steps", "planted_stance_foot",
        "natural_knees", "natural_arms", "stable_torso", "stable_colors", "overall_pass",
    ]
    for key in required_true:
        if review.get(key) is not True:
            raise RuntimeError(f"approved visual review failed: {key}")
    for key in [
        "red_face_noise", "blurred_face", "back_of_head_instead_of_face", "mesh_tearing",
        "limb_stretching", "sparkling_border", "black_rectangle", "whole_body_position_jump",
        "background_flicker",
    ]:
        if review.get(key) is not False:
            raise RuntimeError(f"approved visual review defect present: {key}")
    if review.get("confidence_percent", 0) < 70:
        raise RuntimeError("approved visual review confidence is too low")
    if metrics.get("aligned_head_unique_hashes") != 1:
        raise RuntimeError("head pixels are not rigid and stable")
    if metrics.get("unique_frames") != 32 or metrics.get("border_visible_max") != 0.0:
        raise RuntimeError("walk frame or alpha validation failed")
    if metrics.get("largest_component_ratio_min", 0.0) < 0.975:
        raise RuntimeError("walk silhouette is fragmented")
    if pose.get("frames") != 32 or pose.get("min_body_confident") != 17:
        raise RuntimeError("DWPose did not retain all body joints")
    return manifest, APPROVED / manifest["gif"]


def render(record: dict[str, object]) -> str:
    metrics = record["metrics"]
    pose = record["dwpose_metrics"]
    review = record["review"]
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Player Walk — Single GIF Test</title>
<style>
:root {{ color-scheme:dark; font-family:system-ui,sans-serif; background:#101010; color:#eee; }}
* {{ box-sizing:border-box; }} body {{ margin:0; padding:24px; }} main {{ max-width:1120px; margin:auto; }}
h1 {{ font-size:clamp(30px,6vw,60px); margin:0 0 8px; }} p {{ color:#bbb; }}
.panels {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:18px; margin:28px 0; }}
.panel {{ border:1px solid #444; border-radius:12px; overflow:hidden; background:#1b1b1b; }}
.panel h2 {{ margin:0; padding:12px 16px; font-size:18px; }} .stage {{ min-height:680px; display:flex; align-items:center; justify-content:center; padding:12px; }}
.checker {{ background-color:#aaa; background-image:linear-gradient(45deg,#777 25%,transparent 25%),linear-gradient(-45deg,#777 25%,transparent 25%),linear-gradient(45deg,transparent 75%,#777 75%),linear-gradient(-45deg,transparent 75%,#777 75%); background-size:24px 24px; background-position:0 0,0 12px,12px -12px,-12px 0; }}
.dark {{ background:#181818; }} .light {{ background:#eee; }} img {{ max-width:100%; height:auto; display:block; image-rendering:auto; }}
dl {{ display:grid; grid-template-columns:260px 1fr; gap:8px 16px; padding:18px; background:#191919; border-radius:10px; }} dt {{ color:#aaa; }} dd {{ margin:0; overflow-wrap:anywhere; }}
a {{ color:#8ecbff; }} code {{ font-size:12px; }}
</style>
</head>
<body><main>
<h1>Player Walk</h1>
<p>Exactly one GIF. The flag and every previous inspector GIF were deleted.</p>
<p>No image-generation or video model created these frames. One reviewed still was matted once, rigged with its detected joints, and deformed deterministically with a piecewise-affine skeletal mesh. The head layer is rigid, so the face pixels are identical after alignment in every frame.</p>
<p><a href="{record['public_path']}" target="_blank" rel="noreferrer">Open the GIF directly</a> · <a href="manifest.json">Manifest, gait metrics and review</a></p>
<div class="panels">
<div class="panel"><h2>Checkerboard</h2><div class="stage checker"><img src="{record['public_path']}" alt="Player walking"></div></div>
<div class="panel"><h2>Dark background</h2><div class="stage dark"><img src="{record['public_path']}" alt="Player walking"></div></div>
<div class="panel"><h2>Light background</h2><div class="stage light"><img src="{record['public_path']}" alt="Player walking"></div></div>
</div>
<dl>
<dt>Frames</dt><dd>{record['frames']}</dd>
<dt>Dimensions</dt><dd>{record['width']} × {record['height']}</dd>
<dt>Frame duration</dt><dd>{record['duration_ms']} ms</dd>
<dt>File size</dt><dd>{record['bytes']:,} bytes</dd>
<dt>SHA-256</dt><dd><code>{record['sha256']}</code></dd>
<dt>Generator</dt><dd>{html.escape(str(metrics['generator']))}</dd>
<dt>Frame-generation model</dt><dd>none</dd>
<dt>Aligned head hashes</dt><dd>{metrics['aligned_head_unique_hashes']}</dd>
<dt>Left/right foot lift</dt><dd>{metrics['left_foot_vertical_range_px']:.1f} / {metrics['right_foot_vertical_range_px']:.1f} source pixels</dd>
<dt>DWPose body joints</dt><dd>{pose['min_body_confident']} of 17 in every frame</dd>
<dt>Face review</dt><dd>visible and stable; red noise={review['red_face_noise']}, blurred={review['blurred_face']}, back-of-head substitution={review['back_of_head_instead_of_face']}</dd>
<dt>Anatomy review</dt><dd>natural knees={review['natural_knees']}, natural arms={review['natural_arms']}, mesh tearing={review['mesh_tearing']}, limb stretching={review['limb_stretching']}</dd>
<dt>Visual-review confidence</dt><dd>{review['confidence_percent']}%</dd>
</dl>
</main></body></html>'''


def main() -> int:
    approved, source = validate_bundle()
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    GIF_DIR.mkdir(parents=True)
    destination = GIF_DIR / "player-walk.gif"
    shutil.copy2(source, destination)
    with Image.open(destination) as image:
        frames = list(ImageSequence.Iterator(image))
        width, height = image.size
        duration = int(image.info.get("duration", 0) or 0)
        loop = image.info.get("loop")
    record = {
        "slug": "player-walk",
        "title": "Player Walk",
        "category": "Single controlled test",
        "public_path": "gifs/player-walk.gif",
        "bytes": destination.stat().st_size,
        "width": width,
        "height": height,
        "frames": len(frames),
        "duration_ms": duration,
        "loop": loop,
        "sha256": sha256(destination),
        "model_used_for_frames": False,
        "metrics": approved["metrics"],
        "dwpose_metrics": approved["dwpose_metrics"],
        "review": approved["review"],
        "source_orientation": approved["source_orientation"],
        "approved_bundle_sha256": sha256(APPROVED / "manifest.json"),
    }
    manifest = {
        "ok": True,
        "count": 1,
        "all_previous_gifs_deleted": True,
        "model_used_for_frames": False,
        "gifs": [record],
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (OUTPUT / "index.html").write_text(render(record))
    print(json.dumps({"ok": True, "count": 1, "gif": str(destination), "sha256": record["sha256"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
