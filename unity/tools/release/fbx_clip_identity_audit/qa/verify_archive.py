#!/usr/bin/env python3
"""Inspect a real Unity .unitypackage: fixed-scope authored bytes/GUIDs only."""
from pathlib import Path
import json
import argparse
import re
import tarfile

VENDOR=Path(__file__).resolve().parents[1]/'Assets'
ALLOWED={
'Assets/HPRFbxClipIdentity',
'Assets/HPRFbxClipIdentity/Editor',
'Assets/HPRFbxClipIdentity/Editor/HprFbxClipIdentityAudit.cs',
'Assets/HPRFbxClipIdentity/Editor/HprFbxClipIdentityWindow.cs',
'Assets/HPRFbxClipIdentity/Samples',
'Assets/HPRFbxClipIdentity/Samples/OriginalMotion.fbx',
'Assets/HPRFbxClipIdentity/README.md',
'Assets/HPRFbxClipIdentity/LICENSE.md',
}
MEMBER=re.compile(r'([0-9a-f]{32})/(pathname|asset|asset.meta)$')

def inspect(path):
    if not path.is_file() or path.stat().st_size<3500:raise ValueError('Missing real nontrivial Unity archive')
    blobs={}
    with tarfile.open(path,'r:gz') as archive:
        for item in archive:
            name=item.name.removeprefix('./')
            if item.isdir():
                if name not in ('.','') and not re.fullmatch(r'[0-9a-f]{32}/?',name):raise ValueError('Unapproved directory')
                continue
            if not item.isfile() or not MEMBER.fullmatch(name) or item.size>3_000_000 or name in blobs:raise ValueError('Unexpected member '+name)
            x=archive.extractfile(item)
            if x is None:raise ValueError('Unreadable archive member')
            blobs[name]=x.read()
    mapped={}
    for name,payload in blobs.items():
        match=MEMBER.fullmatch(name)
        if match is None or match[2]!='pathname':continue
        guid=match[1]
        try:where=payload.decode('utf-8').strip()
        except UnicodeDecodeError:raise ValueError('Invalid path')
        if where not in ALLOWED or where in mapped:raise ValueError('Unexpected/duplicate buyer asset path '+where)
        authored=VENDOR/Path(where).relative_to('Assets')
        meta=Path(str(authored)+'.meta')
        if not authored.exists() or not meta.is_file():raise ValueError('Missing authored asset/meta')
        expected=meta.read_bytes()
        if not re.search(rb'(?m)^guid:\s*'+guid.encode()+rb'\s*$',expected):raise ValueError('GUID changed')
        if blobs.get(guid+'/asset.meta')!=expected:raise ValueError('Asset meta bytes changed')
        real=blobs.get(guid+'/asset')
        if authored.is_file() and real != authored.read_bytes():raise ValueError('Buyer source bytes changed')
        if authored.is_dir() and real not in (None,b''):raise ValueError('Folder payload changed')
        mapped[where]=guid
    if set(mapped)!=ALLOWED or len(set(mapped.values()))!=len(mapped):raise ValueError('Missing/duplicated scope assets')
    return {'result':'PASS','buyer_paths':len(mapped),'editor_source_scripts':2,'first_party_animated_fbx_samples':1,'source_and_guid_identity':'PASS'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--archive',required=True,type=Path);args=ap.parse_args()
    print(json.dumps(inspect(args.archive),indent=2))
if __name__=='__main__':main()
