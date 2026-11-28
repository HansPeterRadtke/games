#!/usr/bin/env python3
"""Independently inspect one real Unity-exported archive against authored source."""
import hashlib
import json
import re
import sys
import tarfile
from pathlib import Path

archive = Path(sys.argv[1]); assets = Path(sys.argv[2]); root = assets / 'HPRDefineMatrix'
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
    for item in tar:
        assert item.isfile(), 'Unexpected archive entry type'
        assert re.fullmatch(r'[a-f0-9]{32}/(asset|asset.meta|pathname)', item.name), f'Unexpected archive entry {item.name}'
        guid, typ = item.name.split('/')
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
    assert not any(b'HprDefineMatrixQa' in row['pathname'] for row in collected.values())
print(json.dumps({'status': 'PASS', 'guid_count': len(allowed), 'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'contents_match_source': True, 'buyer_root': 'Assets/HPRDefineMatrix'}))
