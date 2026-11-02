#!/usr/bin/env python3
"""Read-only Unity Asset Store key artwork dimension compliance check.

The original first-party Unity publisher manual specifies icon 160×160,
card 420×280, cover 1950×1300 and social 1200×630 pixels. Requirements
must still be checked in the live publisher form at actual submission.

This gate cannot establish attractive design, text-safe areas, image
copyright, authenticity of Unity gameplay, transparency policy or
whether a listing image violates AI-generated content restrictions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, UnidentifiedImageError


KEY_IMAGE_SIZES = {
    "icon": (160, 160),
    "card": (420, 280),
    "cover": (1950, 1300),
    "social": (1200, 630),
}


def verify_image(path: Path, role: str) -> dict:
    if role not in KEY_IMAGE_SIZES:
        raise ValueError("Unknown Unity key image role: " + role)
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError("Key art must exist as a non-symlink image file")
    if path.suffix.lower() not in (".png", ".jpg", ".jpeg"):
        raise ValueError("Only PNG/JPEG key artwork is accepted")
    with Image.open(path) as image:
        if image.format not in ("PNG", "JPEG"):
            raise ValueError("Invalid PNG/JPEG image format")
        observed = list(image.size)
        mode = image.mode
    expected = list(KEY_IMAGE_SIZES[role])
    reasons = []
    if observed != expected:
        reasons.append(f"Expected exactly {expected[0]} x {expected[1]} pixels for {role}, got {observed[0]} x {observed[1]}")
    if mode not in ("RGB", "RGBA"):
        reasons.append("Image is not an ordinary RGB/RGBA marketing picture")
    return {
        "role": role,
        "filename": path.name,
        "status": "FAIL" if reasons else "PASS",
        "expected_dimensions": expected,
        "observed_dimensions": observed,
        "image_mode": mode,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "reasons": reasons,
        "human_visual_content_review_completed": False,
        "verified_origin_from_unity_editor": False,
        "is_approved_for_publication": False,
    }


def verify_set(art: dict[str, Path]) -> dict:
    if not isinstance(art, dict):
        raise ValueError("Key images must be supplied as a role-to-path mapping")
    roles = set(art)
    required = set(KEY_IMAGE_SIZES)
    unknown = sorted(roles - required)
    missing = sorted(required - roles)
    if unknown:
        raise ValueError("Unknown key image roles: " + ", ".join(unknown))
    images = {role: verify_image(art[role], role) for role in sorted(roles)}
    paths = [str(Path(art[role]).resolve()) for role in roles]
    reused = len(set(paths)) != len(paths)
    status = ("PASS" if not missing and not reused and
              all(image["status"] == "PASS" for image in images.values()) else "FAIL")
    return {
        "status": status,
        "required_roles": sorted(required),
        "missing_roles": missing,
        "reused_image_path_across_roles": reused,
        "images": images,
        "publisher_portal_media_review_completed": False,
        "warning": ("Dimensions and file format only. Pixel detail, origin, visual design, "
                    "honest functionality and live publisher requirements need separate review."),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for role in KEY_IMAGE_SIZES:
        parser.add_argument("--" + role, type=Path)
    parser.add_argument("--output", type=Path, help="create-only private JSON receipt")
    args = parser.parse_args()
    try:
        supplied = {role: getattr(args, role) for role in KEY_IMAGE_SIZES
                    if getattr(args, role) is not None}
        result = verify_set(supplied)
        payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.output is not None:
            if args.output.resolve(strict=False) in {
                Path(path).resolve() for path in supplied.values()}:
                raise ValueError("Refusing to overwrite input marketing artwork")
            args.output.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as writer:
                writer.write(payload)
            args.output.chmod(0o600)
        print(payload, end="")
        return 0 if result["status"] == "PASS" else 2
    except (ValueError, UnidentifiedImageError, OSError) as err:
        print(json.dumps({"status": "ERROR", "message": str(err),
                          "assets_modified": False,
                          "not_publisher_approval": True}))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
