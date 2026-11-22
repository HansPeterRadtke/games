"""Independently verify one actual Unity-exported original bundled package.

Never extracts archive content or runs buyer scripts. Fails closed on wrong
bytes, foreign paths, original meta GUID mismatch or hidden QA inclusion.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import tarfile

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parent
SOURCES={
 'HPRFbxClipIdentity': REPO/'fbx_clip_identity_audit/Assets/HPRFbxClipIdentity',
 'HPRFbxSourceTakes': REPO/'fbx_source_take_visibility/Assets/HPRFbxSourceTakes',
 'HPRAnimationImportPreflight': ROOT/'Assets/HPRAnimationImportPreflight',
}
MEMBER=re.compile(r'([a-f0-9]{32})/(pathname|asset|asset.meta)$')


def verify(pkg):
    pkg=Path(pkg)
    if not pkg.is_file() or pkg.stat().st_size<10000 or pkg.stat().st_size>20000000:
        raise ValueError('invalid or unusually large candidate original Unity package')
    original={}
    for name,source in SOURCES.items():
        assert source.is_dir()
        for item in [source,*source.rglob('*')]:
            if item.is_file() and item.name.endswith('.meta'):continue
            if item.is_file() or item.is_dir():
                rel=item.relative_to(source.parent)
                assetpath='Assets/'+str(rel)
                meta=Path(str(item)+'.meta')
                if not meta.is_file():raise ValueError('missing first-party Unity metadata: '+str(item))
                match=re.search(r'(?m)^guid: ([a-f0-9]{32})$',meta.read_text())
                if not match:raise ValueError('missing unique Unity GUID')
                original[assetpath]=(item,meta,match.group(1))
    if len({v[2] for v in original.values()})!=len(original):
        raise ValueError('conflicting original product GUIDs')
    found={}; members={};total=0
    with tarfile.open(pkg,'r:gz') as t:
        for info in t:
            member=info.name.removeprefix('./')
            if info.isdir():
                if member not in ('','.') and not re.fullmatch(r'[0-9a-f]{32}/?',member):
                    raise ValueError('foreign directory entry')
                continue
            if not info.isfile() or not MEMBER.fullmatch(member) or member in members or info.size>2000000:
                raise ValueError('foreign duplicate or oversized archive member')
            data=t.extractfile(info).read();total+=len(data)
            if total>25000000:raise ValueError('decompressed candidate exceeds size budget')
            members[member]=data
    for name,data in members.items():
        mt=MEMBER.fullmatch(name)
        if mt.group(2)=='pathname':
            path=data.decode('utf8').strip()
            if path in found or path not in original:raise ValueError('missing or extra source path '+path)
            found[path]=mt.group(1)
    if set(found)!=set(original):raise ValueError('missing original first-party paths')
    for path,(file,meta,guid) in original.items():
        if found[path]!=guid or members.get(guid+'/asset.meta')!=meta.read_bytes():
            raise ValueError('original GUID or Unity meta changed: '+path)
        if file.is_file() and members.get(guid+'/asset')!=file.read_bytes():
            raise ValueError('original asset bytes changed: '+path)
        if file.is_dir() and guid+'/asset' in members:
            raise ValueError('directory payload is not expected: '+path)
    return {'result':'PASS','actual_Unity_export_size':pkg.stat().st_size,
            'actual_original_unity_asset_paths':len(found),
            'exact_source_meta_and_guid_preserved':True,
            'source_module_roots':sorted(SOURCES),
            'unitypackage_sha256':hashlib.sha256(pkg.read_bytes()).hexdigest()}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--archive',required=True);args=ap.parse_args()
    print(json.dumps(verify(args.archive),indent=2))
