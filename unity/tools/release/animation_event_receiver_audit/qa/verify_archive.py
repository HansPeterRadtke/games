#!/usr/bin/env python3
"""Independently inspect one real Unity-exported archive against authored source."""
import hashlib
import json
import re
import sys
import tarfile
from pathlib import Path

archive = Path(sys.argv[1]); assets = Path(sys.argv[2]); root = assets / 'HPRAnimationEventAudit'
allowed = {}
for p in (root, *sorted(root.rglob('*'))):
    if p.name.endswith('.meta'): continue
    meta = Path(str(p) + '.meta')
    assert meta.is_file(), f'Missing stable source meta {meta}'
    match = re.search(rb'(?m)^guid:\s*([a-f0-9]{32})\s*$', meta.read_bytes())
    assert match, f'No stable source GUID {meta}'
    guid = match.group(1).decode('ascii')
    assert guid not in allowed, f'Duplicate Unity GUID {guid}'
    allowed[guid] = {'path': 'Assets/' + str(p.relative_to(assets)), 'source': p, 'guid': guid}
with tarfile.open(archive, 'r:*') as tar:
    collected = {}
    declared_directories = set()
    for item in tar:
        # Unity 2022 writes explicit root/GUID directory entries and ./
        # pathname prefixes, whereas 6.6 writes file entries alone. Both
        # formats are accepted ONLY if the exact payload matches source.
        name = item.name[2:] if item.name.startswith('./') else item.name
        if item.isdir():
            if name in ('', '.'):
                assert name not in declared_directories, 'Repeated root directory entry'
            else:
                assert re.fullmatch(r'[a-f0-9]{32}', name), f'Unexpected archive directory {item.name}'
                assert name in allowed, f'Unknown GUID directory {name}'
                assert name not in declared_directories, f'Repeated GUID directory {name}'
            assert item.size == 0, f'Unexpected nonempty directory entry {item.name}'
            declared_directories.add(name)
            continue
        assert item.isfile(), f'Unexpected link/non-file archive member {item.name}'
        assert re.fullmatch(r'[a-f0-9]{32}/(asset|asset.meta|pathname)', name), f'Unexpected archive entry {item.name}'
        guid, typ = name.split('/')
        assert guid in allowed, f'Unknown packaged GUID {guid}'
        assert typ not in collected.setdefault(guid, {}), f'Duplicate tar entry {item.name}'
        value = tar.extractfile(item).read()
        collected[guid][typ] = value
    assert collected.keys() == allowed.keys(), f'Missing asset GUID(s): {allowed.keys() - collected.keys()}'
    for guid, entry in allowed.items():
        row = collected[guid]
        expected_types = {'asset.meta', 'pathname'} if entry['source'].is_dir() else {'asset', 'asset.meta', 'pathname'}
        assert set(row) == expected_types, f'Unexpected contents for {guid}'
        assert row['pathname'].decode('utf-8').strip() == entry['path'], f'Unexpected archived path {guid}'
        assert b'guid: ' + guid.encode() in row['asset.meta'], 'GUID rewritten on packaging'
        if entry['source'].is_file():
            assert row['asset'] == entry['source'].read_bytes(), f'Packaged content differs for {entry["path"]}'
    assert not any(b'HprEventAuditNativeQa' in row['pathname'] for row in collected.values())
print(json.dumps({'status': 'PASS', 'guid_count': len(allowed), 'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'contents_match_source': True, 'buyer_root': 'Assets/HPRAnimationEventAudit'}))
