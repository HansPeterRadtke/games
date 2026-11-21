#!/usr/bin/env python3
"""Fail-closed Unity package scope/GUID/source identity check; no extraction."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import tarfile
import json

ROOT = Path(__file__).resolve().parents[1] / 'Assets'
ALLOWED = {
    'Assets/HPRPackageBoundary',
    'Assets/HPRPackageBoundary/Editor',
    'Assets/HPRPackageBoundary/Editor/HprPackageBoundaryWindow.cs',
    'Assets/HPRPackageBoundary/LICENSE.md',
    'Assets/HPRPackageBoundary/README.md',
}
MEMBER = re.compile(r'^([0-9a-f]{32})/(pathname|asset|asset.meta)$')


def inspect(path: Path) -> dict:
    if not path.is_file() or path.stat().st_size < 4000:
        raise ValueError('Missing/nontrivial real Unity package required')
    blobs = {}
    with tarfile.open(path, 'r:gz') as package:
        for member in package:
            name = member.name.removeprefix('./')
            if member.isdir():
                if name not in ('.', '') and not re.fullmatch(r'[0-9a-f]{32}/?', name):
                    raise ValueError('Unexpected Unity archive directory')
                continue
            if not member.isfile() or not MEMBER.fullmatch(name) or name in blobs or member.size > 6_000_000:
                raise ValueError('Invalid/duplicate/unexpected archive member: ' + name)
            reader = package.extractfile(member)
            if reader is None:
                raise ValueError('Archive member cannot be read')
            blobs[name] = reader.read()
    paths = {}
    for name, raw in blobs.items():
        match = MEMBER.fullmatch(name)
        if match is None or match.group(2) != 'pathname':
            continue
        guid = match.group(1)
        try:
            asset_path = raw.decode('utf-8').strip()
        except UnicodeDecodeError as exc:
            raise ValueError('Invalid UTF8 archive pathname') from exc
        if asset_path not in ALLOWED or asset_path in paths:
            raise ValueError('Unexpected or duplicate buyer asset: ' + asset_path)
        local = ROOT / Path(asset_path).relative_to('Assets')
        meta = Path(str(local) + '.meta')
        if not local.exists() or not meta.is_file():
            raise ValueError('Missing authored asset/meta: ' + asset_path)
        if not re.search(rb'(?m)^guid:\s*' + guid.encode() + rb'\s*$', meta.read_bytes()):
            raise ValueError('Archive GUID is not the authored GUID: ' + asset_path)
        archived_meta = blobs.get(guid + '/asset.meta')
        if archived_meta != meta.read_bytes():
            raise ValueError('Authored metadata differs: ' + asset_path)
        payload = blobs.get(guid + '/asset')
        if local.is_file() and payload != local.read_bytes():
            raise ValueError('Authored buyer source changed in export: ' + asset_path)
        if local.is_dir() and payload not in (None, b''):
            raise ValueError('Folder has unexpected serialized payload: ' + asset_path)
        paths[asset_path] = guid
    if set(paths) != ALLOWED:
        raise ValueError('Buyer package asset set is not exactly approved: ' + repr(sorted(ALLOWED - set(paths))))
    if len(set(paths.values())) != len(paths):
        raise ValueError('Duplicate asset GUIDs')
    return {'status': 'PASS', 'assets': len(paths), 'source_scripts': 1,
            'single_export_root': True, 'meta_guids_and_payloads_match': True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.archive), indent=2))


if __name__ == '__main__':
    main()
