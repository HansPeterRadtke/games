#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import html
import json
import shutil
from pathlib import Path

from PIL import Image, ImageSequence

ROOT = Path(__file__).resolve().parents[1]
APPROVED = ROOT / "docs" / "verification" / "2026-07-30" / "player-walk-mimicmotion"
OUTPUT = ROOT / "web" / "gif_inspector"
GIF_DIR = OUTPUT / "gifs"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_bundle() -> tuple[dict[str, object], Path]:
    manifest = json.loads((APPROVED / "manifest.json").read_text())
    if manifest.get("ok") is not True or manifest.get("benchmark") != "mimicmotion-player-walk":
        raise RuntimeError("approved MimicMotion walk bundle is invalid")
    if manifest.get("engine") != "Tencent MimicMotion 1.1":
        raise RuntimeError("approved walk uses the wrong engine")
    if manifest.get("model_used_for_frames") is not True or manifest.get("looping") is not False:
        raise RuntimeError("approved walk model or looping declaration is invalid")
    for relative, expected in manifest["files"].items():
        path = APPROVED / relative
        if not path.is_file():
            raise RuntimeError(f"missing approved file: {relative}")
        if path.stat().st_size != expected["bytes"] or sha256(path) != expected["sha256"]:
            raise RuntimeError(f"approved file hash mismatch: {relative}")
    metrics = manifest["metrics"]
    pose = manifest["dwpose_metrics"]
    identity = manifest["identity"]
    review = manifest["review"]
    provenance = manifest["provenance"]
    if metrics.get("frame_count") != 24 or metrics.get("dimensions") != [512, 768]:
        raise RuntimeError("walk frame count or dimensions are invalid")
    if metrics.get("duration_ms") != 70 or metrics.get("loop") is not None:
        raise RuntimeError("walk must be an intentional nonlooping pass")
    if metrics.get("unique_frames") != 24 or metrics.get("shared_palette") is not True:
        raise RuntimeError("walk frame or palette validation failed")
    if metrics.get("left_stance_x_std", 999.0) >= 4.0 or metrics.get("right_stance_x_std", 999.0) >= 4.0:
        raise RuntimeError("stance foot is not planted horizontally")
    if metrics.get("left_stance_y_std", 999.0) >= 2.0 or metrics.get("right_stance_y_std", 999.0) >= 2.0:
        raise RuntimeError("stance foot is not planted vertically")
    if metrics.get("ground_std", 999.0) >= 1.0 or metrics.get("body_center_std", 999.0) >= 8.0:
        raise RuntimeError("walk normalization is unstable")
    if metrics.get("alpha_border_max") != 0.0 or metrics.get("largest_component_min", 0.0) < 0.98:
        raise RuntimeError("walk matte is contaminated or fragmented")
    if metrics.get("alpha_soft_min", 0.0) < 0.005 or metrics.get("fallback_used") is not False:
        raise RuntimeError("walk lacks recurrent soft alpha or used fallback")
    if pose.get("frames") != 24 or pose.get("min_body_confident") != 17 or pose.get("support_crossings", 0) < 1:
        raise RuntimeError("DWPose gait validation failed")
    if pose.get("left_ankle_y_range", 0.0) < 0.08 or pose.get("right_ankle_y_range", 0.0) < 0.04:
        raise RuntimeError("both feet do not move through the walk pass")
    if identity.get("min_reference_cosine", 0.0) < 0.60 or identity.get("min_adjacent_cosine", 0.0) < 0.90:
        raise RuntimeError("walk identity consistency failed")
    required_true = [
        "same_person", "complete_head", "face_visible", "face_stable", "face_sharp_enough",
        "complete_hands", "complete_feet", "natural_walk_pass", "support_transfers_once",
        "planted_stance_foot", "natural_knees", "natural_arms", "stable_torso_shape",
        "stable_body_position", "stable_colors", "overall_pass",
    ]
    for key in required_true:
        if review.get(key) is not True:
            raise RuntimeError(f"approved visual review failed: {key}")
    for key in [
        "red_face_noise", "blurred_face", "back_of_head_substitution", "belly_wobble_or_stretch",
        "limb_distortion", "foot_sliding", "body_position_jump", "sparkling_border",
        "black_rectangle", "background_flicker",
    ]:
        if review.get(key) is not False:
            raise RuntimeError(f"approved visual review defect present: {key}")
    if review.get("confidence_percent", 0) < 70:
        raise RuntimeError("approved visual review confidence is too low")
    coverage = provenance.get("checkpoint_coverage", {})
    if coverage != {"unet_keys": 1428, "pose_net_keys": 19, "missing_unet": 0, "missing_pose_net": 0, "unexpected": 0}:
        raise RuntimeError("MimicMotion checkpoint coverage is incomplete")
    compatibility = provenance.get("compatibility", {})
    for key in ["network_code_changed", "weights_changed", "pose_preprocessing_changed", "denoising_changed", "tile_fusion_changed"]:
        if compatibility.get(key) is not False:
            raise RuntimeError(f"unsupported compatibility change: {key}")
    return manifest, APPROVED / manifest["gif"]


def render(record: dict[str, object]) -> str:
    metrics = record["metrics"]
    pose = record["dwpose_metrics"]
    identity = record["identity"]
    review = record["review"]
    provenance = record["provenance"]
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Player Walk — MimicMotion Test</title>
<style>
:root {{ color-scheme:dark; font-family:system-ui,sans-serif; background:#101010; color:#eee; }}
* {{ box-sizing:border-box; }} body {{ margin:0; padding:24px; }} main {{ max-width:1500px; margin:auto; }}
h1 {{ font-size:clamp(30px,6vw,60px); margin:0 0 8px; }} p {{ color:#bbb; line-height:1.5; }}
.warning {{ color:#ffd68a; font-weight:700; }}
.panels {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(380px,1fr)); gap:18px; margin:28px 0; }}
.panel {{ border:1px solid #444; border-radius:12px; overflow:hidden; background:#1b1b1b; }}
.panel h2 {{ margin:0; padding:12px 16px; font-size:18px; }} .stage {{ min-height:800px; display:flex; align-items:center; justify-content:center; padding:12px; }}
.checker {{ background-color:#aaa; background-image:linear-gradient(45deg,#777 25%,transparent 25%),linear-gradient(-45deg,#777 25%,transparent 25%),linear-gradient(45deg,transparent 75%,#777 75%),linear-gradient(-45deg,transparent 75%,#777 75%); background-size:24px 24px; background-position:0 0,0 12px,12px -12px,-12px 0; }}
.dark {{ background:#181818; }} .light {{ background:#eee; }} img {{ max-width:100%; height:auto; display:block; image-rendering:auto; }}
dl {{ display:grid; grid-template-columns:290px 1fr; gap:8px 16px; padding:18px; background:#191919; border-radius:10px; }} dt {{ color:#aaa; }} dd {{ margin:0; overflow-wrap:anywhere; }}
a {{ color:#8ecbff; }} code {{ font-size:12px; }}
</style>
</head>
<body><main>
<h1>Player Walk — MimicMotion 1.1</h1>
<p>Exactly one GIF. The deterministic mesh-rig benchmark and every earlier inspector GIF were deleted.</p>
<p>Tencent MimicMotion 1.1 copied a real frontal walking motion into the reviewed player reference. The result was recurrently matted with Robust Video Matting, normalized to a fixed body scale and ground line, and continuously anchored to the support foot.</p>
<p class="warning">This is intentionally one nonlooping walking pass. The real generated seam was {metrics['loop_ratio']:.2f} times a normal adjacent-frame change, so no crossfade, reversal or fake loop was used. Reload the page to replay it.</p>
<p><a href="{record['public_path']}" target="_blank" rel="noreferrer">Open the GIF directly</a> · <a href="manifest.json">Manifest, provenance, gait metrics and review</a></p>
<div class="panels">
<div class="panel"><h2>Checkerboard</h2><div class="stage checker"><img src="{record['public_path']}" alt="Player walking"></div></div>
<div class="panel"><h2>Dark background</h2><div class="stage dark"><img src="{record['public_path']}" alt="Player walking"></div></div>
<div class="panel"><h2>Light background</h2><div class="stage light"><img src="{record['public_path']}" alt="Player walking"></div></div>
</div>
<dl>
<dt>Engine</dt><dd>{html.escape(str(record['engine']))}</dd>
<dt>Frames</dt><dd>{record['frames']}</dd>
<dt>Dimensions</dt><dd>{record['width']} × {record['height']}</dd>
<dt>Frame duration</dt><dd>{record['duration_ms']} ms</dd>
<dt>Loop extension</dt><dd>none</dd>
<dt>File size</dt><dd>{record['bytes']:,} bytes</dd>
<dt>SHA-256</dt><dd><code>{record['sha256']}</code></dd>
<dt>Model checkpoint</dt><dd><code>{html.escape(str(provenance['checkpoint_sha256']))}</code></dd>
<dt>Checkpoint coverage</dt><dd>UNet {provenance['checkpoint_coverage']['unet_keys']} keys, pose network {provenance['checkpoint_coverage']['pose_net_keys']} keys, zero missing or unexpected model keys</dd>
<dt>Identity similarity</dt><dd>reference minimum {identity['min_reference_cosine']:.3f}, adjacent minimum {identity['min_adjacent_cosine']:.3f}</dd>
<dt>DWPose body joints</dt><dd>{pose['min_body_confident']} of 17 in every frame</dd>
<dt>Support transfer</dt><dd>{pose['support_crossings']} clear transfer; stance x deviation {metrics['left_stance_x_std']:.2f}/{metrics['right_stance_x_std']:.2f} px, stance y deviation {metrics['left_stance_y_std']:.2f}/{metrics['right_stance_y_std']:.2f} px</dd>
<dt>Matte</dt><dd>soft-alpha minimum {metrics['alpha_soft_min']:.3f}, border contamination {metrics['alpha_border_max']:.3f}, connected silhouette {metrics['largest_component_min']:.4f}</dd>
<dt>Face review</dt><dd>visible={review['face_visible']}, stable={review['face_stable']}, sharp enough={review['face_sharp_enough']}, red noise={review['red_face_noise']}, blur={review['blurred_face']}, back-of-head substitution={review['back_of_head_substitution']}</dd>
<dt>Motion review</dt><dd>natural walk={review['natural_walk_pass']}, planted stance={review['planted_stance_foot']}, natural knees={review['natural_knees']}, natural arms={review['natural_arms']}, belly wobble/stretch={review['belly_wobble_or_stretch']}, foot sliding={review['foot_sliding']}</dd>
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
    if loop is not None:
        raise RuntimeError("approved walk unexpectedly contains a GIF loop extension")
    record = {
        "slug": "player-walk",
        "title": "Player Walk — MimicMotion 1.1",
        "category": "Single controlled model test",
        "public_path": "gifs/player-walk.gif",
        "bytes": destination.stat().st_size,
        "width": width,
        "height": height,
        "frames": len(frames),
        "duration_ms": duration,
        "loop": loop,
        "sha256": sha256(destination),
        "engine": approved["engine"],
        "model_used_for_frames": True,
        "looping": False,
        "metrics": approved["metrics"],
        "dwpose_metrics": approved["dwpose_metrics"],
        "identity": approved["identity"],
        "review": approved["review"],
        "provenance": approved["provenance"],
        "approved_bundle_sha256": sha256(APPROVED / "manifest.json"),
    }
    manifest = {
        "ok": True,
        "count": 1,
        "all_previous_gifs_deleted": True,
        "engine": approved["engine"],
        "model_used_for_frames": True,
        "looping": False,
        "gifs": [record],
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (OUTPUT / "index.html").write_text(render(record))
    print(json.dumps({"ok": True, "count": 1, "gif": str(destination), "sha256": record["sha256"], "looping": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
