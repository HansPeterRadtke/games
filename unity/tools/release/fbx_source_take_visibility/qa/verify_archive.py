#!/usr/bin/env python3
"""Fail-closed exact original first-party Unity-exported archive verifier."""
from pathlib import Path
import argparse, hashlib, json, re, tarfile
ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT/'Assets/HPRFbxSourceTakes'
ALLOWED={
 'Assets/HPRFbxSourceTakes',
 'Assets/HPRFbxSourceTakes/Editor',
 'Assets/HPRFbxSourceTakes/Editor/HprFbxSourceTakeAudit.cs',
 'Assets/HPRFbxSourceTakes/Editor/HprFbxSourceTakeWindow.cs',
 'Assets/HPRFbxSourceTakes/Samples',
 'Assets/HPRFbxSourceTakes/Samples/HPRTwoTakeCube.fbx',
 'Assets/HPRFbxSourceTakes/Samples/HPRTwoTakeCustomMissing.fbx',
 'Assets/HPRFbxSourceTakes/Samples/Prefabs',
 'Assets/HPRFbxSourceTakes/Samples/Prefabs/OriginalAutoTwoTake.prefab',
 'Assets/HPRFbxSourceTakes/Samples/Prefabs/OriginalConfiguredMissingTake.prefab',
 'Assets/HPRFbxSourceTakes/Samples/Scenes',
 'Assets/HPRFbxSourceTakes/Samples/Scenes/SourceTakeVisibilityDemo.unity',
 'Assets/HPRFbxSourceTakes/README.md',
 'Assets/HPRFbxSourceTakes/LICENSE.md',
}
MEMBER=re.compile(r'([0-9a-f]{32})/(pathname|asset|asset.meta)$')

def verify(archive:Path):
    if not archive.is_file() or archive.stat().st_size<5000:
        raise ValueError('No original real Unity archive')
    content={}
    total=0
    with tarfile.open(archive,'r:gz') as t:
        for m in t:
            name=m.name.removeprefix('./')
            if m.isdir():
                if name!='.' and not re.fullmatch(r'[0-9a-f]{32}/?',name):
                    raise ValueError('unexpected directory')
                continue
            if not m.isfile() or not MEMBER.fullmatch(name) or m.size>2_500_000 or name in content:
                raise ValueError('unexpected/oversized/duplicate Unity package member '+name)
            stream=t.extractfile(m)
            if stream is None:raise ValueError('unreadable asset member')
            content[name]=stream.read();total+=len(content[name])
            if total>10_000_000:raise ValueError('overall importer content limit exceeded')
    paths={}
    for name,data in content.items():
        match=MEMBER.fullmatch(name)
        if match.group(2)!='pathname':continue
        guid=match.group(1);path=data.decode('utf8').strip()
        if path not in ALLOWED or path in paths:raise ValueError('unexpected/duplicate vendor path')
        local=ROOT/'Assets'/Path(path).relative_to('Assets')
        meta=Path(str(local)+'.meta')
        if not local.exists() or not meta.is_file():raise ValueError('missing original source/meta')
        if not re.search(r'^guid: '+guid+r'\s*$',meta.read_text(),re.M):
            raise ValueError('asset guid differs from source')
        if content.get(guid+'/asset.meta')!=meta.read_bytes():
            raise ValueError('asset meta differs from original exact bytes')
        if local.is_file() and content.get(guid+'/asset')!=local.read_bytes():
            raise ValueError('source payload differs from original exact bytes')
        if local.is_dir() and guid+'/asset' in content:
            raise ValueError('unexpected directory asset payload')
        paths[path]=guid
    if set(paths)!=ALLOWED or len(set(paths.values()))!=len(paths):
        raise ValueError('missing/duplicate/extra original source')
    sample=VENDOR/'Samples/HPRTwoTakeCube.fbx'
    negative=VENDOR/'Samples/HPRTwoTakeCustomMissing.fbx'
    if sample.read_bytes()!=negative.read_bytes():
        raise ValueError('original two demonstration FBX examples do not match exact first-party source')
    healthyMeta=Path(str(sample)+'.meta').read_text()
    negativeMeta=Path(str(negative)+'.meta').read_text()
    if ('    clipAnimations: []' not in healthyMeta or
            negativeMeta.count('      takeName: ') != 1):
        raise ValueError('real authored positive/negative importer sample metadata changed')
    return {'result':'PASS','verified_vendor_paths':len(paths),'editor_scripts':2,
            'original_blender_two_take_fbx_sha256':hashlib.sha256(sample.read_bytes()).hexdigest(),
            'two_first_party_examples_same_source_bytes':sample.read_bytes()==(VENDOR/'Samples/HPRTwoTakeCustomMissing.fbx').read_bytes(),
            'all_origins_guid_and_source_meta_preserved':True,
            'original_package_sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--archive',required=True,type=Path)
    args=ap.parse_args();print(json.dumps(verify(args.archive),indent=2))
