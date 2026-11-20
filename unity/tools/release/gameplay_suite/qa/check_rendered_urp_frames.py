#!/usr/bin/env python3
"""Read-only QA for real Unity camera PNGs; does not claim artistic approval.

Requires Pillow on the QA machine; never bundled into the Unity buyer archive.
"""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageStat

EXPECTED = {
    '01-icon-actual-unity-camera.png': (160, 160),
    '02-card-actual-unity-camera.png': (420, 280),
    '03-cover-actual-unity-camera.png': (1950, 1300),
    '04-social-actual-unity-camera.png': (1200, 630),
}


def check(folder: Path) -> dict:
    metrics = {}
    errors = []
    for name, expected_size in EXPECTED.items():
        path = folder / name
        if not path.is_file() or path.is_symlink():
            errors.append(f'Missing or symlinked camera capture: {name}')
            continue
        try:
            with Image.open(path) as source:
                if source.format != 'PNG':
                    raise ValueError('Not a PNG')
                source.load()
                size = source.size
                rgb = source.convert('RGB')
            stat = ImageStat.Stat(rgb)
            variance = sum(v**0.5 for v in stat.var) / 3
            # Subsample for bounded work while retaining a reproducible check.
            sample = rgb.resize((min(160, size[0]), min(160, size[1])), Image.Resampling.NEAREST)
            pixels = list(sample.get_flattened_data() if hasattr(sample, "get_flattened_data") else sample.getdata())
            magenta = sum(r > 140 and b > 140 and g < 75 for r, g, b in pixels) / len(pixels)
            near_black = sum(max(p) < 10 for p in pixels) / len(pixels)
            distinct = len(set(pixels))
            metrics[name] = {
                'dimensions': list(size), 'unique_sample_colors': distinct,
                'mean_channel_stddev': round(variance, 3),
                'magenta_fraction': round(magenta, 5),
                'near_black_fraction': round(near_black, 5),
            }
            if size != expected_size:
                errors.append(f'Wrong dimensions: {name}')
            if distinct < 32 or variance < 10:
                errors.append(f'Possible blank or flat frame: {name}')
            if near_black > 0.95:
                errors.append(f'Nearly all black: {name}')
            if magenta > 0.05:
                errors.append(f'Possible missing-shader magenta: {name}')
        except (OSError, ValueError) as exc:
            errors.append(f'Unreadable frame {name}: {exc}')
    return {'status': 'PASS' if not errors else 'FAIL', 'automatic_visual_checks': metrics,
            'errors': errors, 'human_artistic_approval': 'NOT_PERFORMED'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path)
    parser.add_argument('--receipt', type=Path)
    args = parser.parse_args()
    report = check(args.folder)
    if args.receipt:
        if args.receipt.exists() or args.receipt.is_symlink():
            parser.error('Receipt already exists; refusing overwrite')
        args.receipt.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
