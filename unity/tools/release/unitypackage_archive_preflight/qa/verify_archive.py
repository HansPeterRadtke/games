#!/usr/bin/env python3
"""Exact Unity-authored .unitypackage scope/GUID/source verification."""
from pathlib import Path
import tarfile
import re
import json
import argparse
VENDOR=Path(__file__).resolve().parents[1]/'Assets'
ALLOWED={
'Assets/HPRArchivePreflight',
'Assets/HPRArchivePreflight/Editor',
'Assets/HPRArchivePreflight/Editor/HprUnitypackageArchiveReader.cs',
'Assets/HPRArchivePreflight/Editor/HprUnitypackageArchiveWindow.cs',
'Assets/HPRArchivePreflight/Editor/HprArchiveCoexistence.cs',
'Assets/HPRArchivePreflight/README.md',
'Assets/HPRArchivePreflight/LICENSE.md',
'Assets/HPRArchivePreflight/Samples',
'Assets/HPRArchivePreflight/Samples/HprExample-baseline.unitypackage',
'Assets/HPRArchivePreflight/Samples/HprExample-additions_only.unitypackage',
'Assets/HPRArchivePreflight/Samples/HprExample-changed_guid.unitypackage'
}
MEMBER=re.compile(r'([0-9a-f]{32})/(pathname|asset|asset.meta)$')

def verify(p:Path):
    if not p.is_file() or p.stat().st_size < 4000:raise ValueError('Missing real Unity archive')
    extracted={}
    with tarfile.open(p,'r:gz') as archive:
        for item in archive:
            name=item.name.removeprefix('./')
            if item.isdir():
                if name!='.' and not re.fullmatch(r'[0-9a-f]{32}/?',name):
                    raise ValueError('Unexpected archive directory '+name)
                continue
            if not item.isfile() or not MEMBER.fullmatch(name) or item.size>5_000_000 or name in extracted:
                raise ValueError('Extra, duplicate, or oversized archive member '+name)
            stream=archive.extractfile(item)
            if stream is None:raise ValueError('Unreadable member')
            extracted[name]=stream.read()
    by_path={}
    for name,raw in extracted.items():
        m=MEMBER.fullmatch(name)
        if not m or m.group(2)!='pathname':continue
        guid=m.group(1)
        path=raw.decode('utf-8').strip()
        if path not in ALLOWED or path in by_path:raise ValueError('Invalid/duplicate vendor path')
        local=VENDOR/Path(path).relative_to('Assets')
        meta=Path(str(local)+'.meta')
        if not local.exists() or not meta.is_file():raise ValueError('Missing expected first-party source or meta')
        if re.search(r'^guid: '+guid+r'\s*$',meta.read_text(),re.M) is None:
            raise ValueError('GUID identity does not match vendor metadata')
        if extracted.get(guid+'/asset.meta')!=meta.read_bytes():
            raise ValueError('Buyer archive changed first-party metadata bytes')
        if local.is_file() and extracted.get(guid+'/asset')!=local.read_bytes():
            raise ValueError('Buyer archive changed first-party source bytes')
        if local.is_dir() and guid+'/asset' in extracted:
            raise ValueError('Unexpected folder asset payload')
        by_path[path]=guid
    if set(by_path)!=ALLOWED or len(set(by_path.values()))!=len(by_path):
        raise ValueError('Missing/extra/duplicate buyer assets')
    return {'result':'PASS','verified_vendor_paths':len(by_path),
            'editor_scripts':3,'unity_exported_training_archives':3,
            'source_and_meta_guid_bytes':'PASS'}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--archive',type=Path,required=True)
    a=parser.parse_args();print(json.dumps(verify(a.archive),indent=2))
