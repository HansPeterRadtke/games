#!/usr/bin/env python3
"""Read-only objective QA for actual Unity-generated PNG demo screenshots.

Catches near-black, very low-detail, tiny and duplicate captures.
It never creates images, pretends images were rendered with Unity, or
claims subjective visual quality. Genuine Unity Editor capture logs
must establish origin separately; this audits only existing PNG pixels.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, UnidentifiedImageError

Image.MAX_IMAGE_PIXELS = 35_000_000

MIN_WIDTH = 1280
MIN_HEIGHT = 720
MIN_LUMINANCE_MEAN = 0.11
MIN_LUMINANCE_STD = 0.075
MIN_CENTER_LUMINANCE_STD = 0.045
MAX_NEARBLACK_FRACTION = 0.25
MIN_EDGE_FRACTION = 0.0045
MIN_DISTINCT_MEAN_RGB_DELTA = 0.02
MIN_DISTINCT_PIXEL_FRACTION = 0.10


def _rgb(path: Path) -> np.ndarray:
    if path.is_symlink() or not path.is_file():
        raise ValueError("Image must be an existing non-symlink file: " + str(path))
    if path.suffix.lower() != ".png":
        raise ValueError("This audit accepts only lossless .png captures")
    with Image.open(path) as image:
        if image.format != "PNG":
            raise ValueError("Invalid PNG file")
        width, height = image.size
        if width <= 0 or height <= 0 or width * height > 35_000_000:
            raise ValueError("Unsafe image dimensions")
        converted = image.convert("RGB")
        return np.asarray(converted, dtype=np.float32) / np.float32(255.0)


def analyze_image(path: Path) -> dict:
    path = Path(path)
    image = _rgb(path)
    height, width = image.shape[:2]
    lum = (np.float32(0.2126) * image[:, :, 0] +
           np.float32(0.7152) * image[:, :, 1] +
           np.float32(0.0722) * image[:, :, 2])
    center = lum[int(.2*height):int(.8*height),
                 int(.2*width):int(.8*width)]
    edges = (np.mean(np.abs(np.diff(lum, axis=0)) > .09) +
             np.mean(np.abs(np.diff(lum, axis=1)) > .09)) / 2.
    metrics = {
        "width": width, "height": height,
        "luminance_mean": round(float(lum.mean()), 5),
        "luminance_std": round(float(lum.std()), 5),
        "center_luminance_std": round(float(center.std()), 5),
        "nearblack_fraction": round(float((lum < .035).mean()), 5),
        "strong_edge_fraction": round(float(edges), 5),
        "png_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    reasons = []
    if width < MIN_WIDTH or height < MIN_HEIGHT:
        reasons.append("resolution below expected professional demo capture size")
    if metrics["luminance_mean"] < MIN_LUMINANCE_MEAN:
        reasons.append("mean luminance is too dark")
    if metrics["luminance_std"] < MIN_LUMINANCE_STD:
        reasons.append("whole-frame contrast is insufficient")
    if metrics["center_luminance_std"] < MIN_CENTER_LUMINANCE_STD:
        reasons.append("center detail / contrast is insufficient")
    if metrics["nearblack_fraction"] > MAX_NEARBLACK_FRACTION:
        reasons.append("excessive near-black pixels")
    if metrics["strong_edge_fraction"] < MIN_EDGE_FRACTION:
        reasons.append("insufficient spatial detail or edges")
    return {
        "filename": path.name,
        "status": "FAIL" if reasons else "PASS",
        "reasons": reasons,
        **metrics,
    }


def analyze_gallery(paths: list[Path]) -> dict:
    if len(paths) < 2:
        raise ValueError("A commercial image gallery requires at least two independent views")
    if len(set(str(Path(x).resolve()) for x in paths)) != len(paths):
        raise ValueError("Input lists the same image multiple times")
    results = [analyze_image(Path(path)) for path in paths]
    images = [_rgb(Path(path)) for path in paths]
    pairs = []
    for i in range(len(paths)):
        for j in range(i+1, len(paths)):
            a, b = images[i], images[j]
            if a.shape != b.shape:
                pair = {"left": results[i]["filename"], "right": results[j]["filename"],
                        "distinct_views": True,
                        "comparison_note": "Different capture dimensions; cannot compare pixelwise"}
            else:
                delta = np.abs(a-b)
                mean = float(delta.mean())
                changed_fraction = float((delta.max(axis=2) > .03).mean())
                pair = {"left": results[i]["filename"], "right": results[j]["filename"],
                        "mean_absolute_rgb_difference": round(mean, 5),
                        "changed_pixel_fraction": round(changed_fraction, 5),
                        "distinct_views": mean >= MIN_DISTINCT_MEAN_RGB_DELTA and
                                          changed_fraction >= MIN_DISTINCT_PIXEL_FRACTION}
            pairs.append(pair)
    status = ("PASS" if all(x["status"] == "PASS" for x in results) and
              all(x["distinct_views"] for x in pairs) else "FAIL")
    return {
        "status": status,
        "is_subjective_visual_approval": False,
        "is_proof_captured_using_unity": False,
        "images": results,
        "pairs": pairs,
        "note": ("Nonblack/detail/duplicate pixel checks only. A human must still "
                 "review Unity Editor provenance, composition, lighting, text and features."),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, help="new private JSON receipt, must not already exist")
    args = parser.parse_args()
    try:
        result = analyze_gallery(args.images)
        raw = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.output is not None:
            if any(args.output.resolve(strict=False) == image.resolve()
                   for image in args.images):
                raise ValueError("Refusing to overwrite any input screenshot")
            args.output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with args.output.open("x", encoding="utf-8") as fp:
                fp.write(raw)
            args.output.chmod(0o600)
        print(raw, end="")
        return 0 if result["status"] == "PASS" else 2
    except (ValueError, OSError, UnidentifiedImageError) as exc:
        print(json.dumps({"status": "ERROR", "reason": str(exc),
                          "images_modified": False}))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
