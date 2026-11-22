#!/usr/bin/env python3
"""Strict original first-party only Unity native package byte/metadata verification."""
from pathlib import Path
import sys,tarfile,re,json,hashlib
SOURCE=Path(__file__).resolve().parents[1]/'Assets/HPRImportedPrefabParity'

def verify(package):
    expected={}
    for item in [SOURCE,*SOURCE.rglob('*')]:
        if item.is_file() and item.suffix=='.meta': continue
        if not (item.is_file() or item.is_dir()):continue
        meta=Path(str(item)+'.meta');m=re.search(r'(?m)^guid: ([a-f0-9]{32})$',meta.read_text())
        if not m:raise ValueError('Missing first-party Unity GUID')
        name='Assets/'+str(item.relative_to(SOURCE.parent))
        expected[name]=(m.group(1),meta.read_bytes(),item.read_bytes() if item.is_file() else None)
    seen={}
    with tarfile.open(package,'r:gz') as archive:
        for entry in archive:
            name=entry.name[2:] if entry.name.startswith('./') else entry.name
            if entry.isdir() and (name in ('','.','./') or re.fullmatch('[a-f0-9]{32}',name)):
                continue
            part=name.split('/')
            if len(part)!=2 or not re.fullmatch('[a-f0-9]{32}',part[0]) or part[1] not in ('pathname','asset','asset.meta') or not entry.isfile():
                raise ValueError('Unexpected archive entry')
            payload=archive.extractfile(entry).read()
            if len(payload)>16000000:raise ValueError('Unexpected asset size')
            if part[1] in seen.setdefault(part[0],{}):raise ValueError('Duplicate archive record')
            seen[part[0]][part[1]]=payload
    rows={}
    for guid,data in seen.items():
        if not {'pathname','asset.meta'}.issubset(data):raise ValueError('Missing metadata or pathname')
        path=data['pathname'].decode('utf8')
        if path in rows:raise ValueError('Duplicate original Unity asset path')
        rows[path]=(guid,data)
    if set(rows)!=set(expected):raise ValueError('Foreign, omitted or rewritten buyer source path')
    for path,(id,meta,source) in expected.items():
        got,data=rows[path]
        if got!=id or data['asset.meta']!=meta or data.get('asset')!=source:
            raise ValueError('Original Unity .meta GUID or source bytes rewritten at '+path)
    return {'status':'PASS','original_first_party_asset_paths':len(rows),
        'source_sha256':hashlib.sha256((SOURCE/'Editor/HprImportedPrefabStateParity.cs').read_bytes()).hexdigest(),
        'package_sha256':hashlib.sha256(Path(package).read_bytes()).hexdigest()}

if __name__=='__main__':
    print(json.dumps(verify(Path(sys.argv[1])),sort_keys=True))
