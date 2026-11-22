#!/usr/bin/env python3
"""Independent byte-for-byte verifier for real Unity native publisher receipts.

Read-only and fail-closed. It checks the actual imported source and .meta files
against the original Unity Editor SHA-256 hashes; no fabricated Unity evidence.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

MAX_FILE = 1 << 30
MAX_TOTAL = 4 << 30


def file_digest(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"Missing or linked imported file: {path}")
    if path.stat().st_size > MAX_FILE:
        raise ValueError(f"Oversized imported file: {path}")
    sha = hashlib.sha256()
    with path.open('rb') as stream:
        while chunk := stream.read(1 << 20):
            sha.update(chunk)
    return sha.hexdigest()


def verify(project: Path, report: Path) -> dict:
    if not project.is_dir() or not (project/'Assets').is_dir():
        raise ValueError('Expected an existing original Unity project')
    if report.stat().st_size > 8_000_000:
        raise ValueError('Receipt exceeds the safe maximum')
    data = json.loads(report.read_text(encoding='utf-8'))
    if (data.get('schema') != 2 or data.get('status') != 'SNAPSHOT_COMPLETE'
            or data.get('incomplete') is not False or data.get('failureReason') not in (None, '')
            or data.get('assetCount') != len(data.get('assets') or [])):
        raise ValueError('Receipt is not a complete native version-two scan')
    paths = set()
    total = 0
    for entry in data['assets']:
        path = entry.get('path', '')
        if (not path.startswith('Assets/') or '..' in path or '\\' in path
                or path in paths):
            raise ValueError('Unsafe or duplicate reported Unity asset path')
        paths.add(path)
        for suffix, expected_key in (('', 'sourceFileSha256'), ('.meta', 'metaFileSha256')):
            source = (project / (path + suffix)).resolve(strict=True)
            if not source.is_relative_to(project.resolve()):
                raise ValueError('Source escapes tested Unity project')
            digest = file_digest(source)
            if digest != entry.get(expected_key):
                raise ValueError(f'Native source fingerprint mismatch at {path}{suffix}')
            total += source.stat().st_size
            if total > MAX_TOTAL:
                raise ValueError('Source fingerprint verification exceeds total bound')
    if not paths:
        raise ValueError('No original vendor files to independently verify')
    return {'status': 'PASS', 'actual_imported_files': len(paths),
            'actual_source_and_meta_files': len(paths) * 2, 'verified_bytes': total,
            'original_Unity_version': data['unityVersion']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project', type=Path)
    parser.add_argument('receipt', type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.project, args.receipt), sort_keys=True))


if __name__ == '__main__':
    main()
