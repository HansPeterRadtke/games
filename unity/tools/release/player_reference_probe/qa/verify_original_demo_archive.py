#!/usr/bin/env python3
"""Read-only independently verify first-party customer Unity archive and original source parity."""
from __future__ import annotations

import hashlib
import json
import pathlib
import tarfile
import sys


ROOT='Assets/HPRPlayerReferenceProbe'
REQUIRED={
    'README.md',
    'Runtime/HprPlayerReferenceProbe.cs',
    'Editor/HprPlayerReferenceProbeWindow.cs',
    'Demo/README.md',
    'Demo/Scripts/HprPlayerReferenceDemoItem.cs',
    'Demo/Scenes/HPR_Player_Reference_Probe_Demo.unity',
    'Demo/Resources/HPRSample/AssignedItem.asset',
    'Demo/Resources/HPRSample/OptionalItem.asset',
    'Demo/Resources/HPRSample/HPR_Demo_Reference.prefab',
}


def _accepted_unity2022_monoimporter_default(source_bytes:bytes, archive_bytes:bytes,
                                            original_name:str)->bool:
    """Strictly permit only Unity 2022's auto-filled default MonoImporter block.

    No GUID, script content, execution-order, icon, bundle, or non-script metadata
    modifications are accepted. This is a *documented byte difference* and not
    a claim that 2022's .meta archive exactly matches the first-party source.
    """
    if not original_name.endswith('.cs'):
        return False
    try:
        src=source_bytes.decode('utf-8').replace('\r\n','\n').rstrip('\n')
        built=archive_bytes.decode('utf-8').replace('\r\n','\n').rstrip('\n')
    except UnicodeDecodeError:
        return False
    expected=(src+'\nMonoImporter:\n'
              '  externalObjects: {}\n'
              '  serializedVersion: 2\n'
              '  defaultReferences: []\n'
              '  executionOrder: 0\n'
              '  icon: {instanceID: 0}\n'
              '  userData: \n'
              '  assetBundleName: \n'
              '  assetBundleVariant: ')
    return src.startswith('fileFormatVersion: 2\nguid: ') and \
        len(src.splitlines())==2 and built==expected


def verify(archive:pathlib.Path, original_root:pathlib.Path)->dict:
    if not archive.is_file() or not original_root.is_dir():
        raise ValueError('Missing genuine archived buyer file or source tree')
    if archive.stat().st_size>5_000_000:
        raise ValueError('Unexpectedly large source-only first-party Unity archive')
    paths={}
    guid_dirs=set()
    members={}
    normalized_meta=[]
    with tarfile.open(archive,'r:gz') as bundle:
        for info in bundle.getmembers():
            # Unity 2022 emits safe ./GUID/... paths and physical directory
            # entries; Unity 6 commonly omits both. Neither is unsafe.
            parts=pathlib.PurePosixPath(info.name).parts
            if not parts:
                if info.isdir():continue
                raise ValueError('Unsafe root file in Unity archive')
            if len(parts)==1 and info.isdir():
                guid=parts[0]
                if len(guid)!=32 or any(c not in '0123456789abcdef' for c in guid):
                    raise ValueError('Unsafe unexpected Unity archive directory')
                continue
            if not info.isfile() or len(parts)!=2 or '..' in parts:
                raise ValueError('Unsafe or unexpected Unity package layout')
            guid,kind=parts
            if len(guid)!=32 or any(c not in '0123456789abcdef' for c in guid):
                raise ValueError('Malformed GUID directory')
            if kind not in ('pathname','asset','asset.meta','preview.png'):
                raise ValueError('Unexpected archive member')
            key=guid+'/'+kind
            if key in members:
                raise ValueError('Duplicate normalized Unity package member')
            members[key]=info
            guid_dirs.add(guid)
            if kind!='pathname':continue
            raw=bundle.extractfile(info).read()
            name=raw.decode('utf-8').strip()
            relative=pathlib.PurePosixPath(name)
            if not (relative==pathlib.PurePosixPath(ROOT) or
                    str(relative).startswith(ROOT+'/')):
                raise ValueError('Unapproved external archive root')
            if relative.is_absolute() or '..' in relative.parts or name in paths:
                raise ValueError('Duplicate or unsafe exported archive pathname')
            if '/qa/' in name.lower() or 'hprprobeqa' in name.lower() or name.lower().endswith('.exe'):
                raise ValueError('Private fixture leaked into customer product')
            if guid in paths.values():
                raise ValueError('Unity asset GUID reused for multiple exported paths')
            paths[name]=guid
        if set(paths.values())!=guid_dirs:
            raise ValueError('Unreferenced archive GUID files or missing pathname')
        for name,guid in paths.items():
            source=original_root/str(pathlib.PurePosixPath(name).relative_to(ROOT))
            if not source.exists():
                raise ValueError('Missing original author-owned source or directory: '+name)
            if source.is_dir():continue
            if not source.is_file():raise ValueError('Unexpected symlink or non-file in buyer tree')
            archived=bundle.extractfile(members[guid+'/asset']) if guid+'/asset' in members else None
            if archived is None:
                raise ValueError('Asset data missing from Unity package: '+name)
            if archived.read()!=source.read_bytes():
                raise ValueError('Packaged consumer asset does not match original source: '+name)
            meta=source.with_name(source.name+'.meta')
            assert meta.is_file(),('Missing source Unity meta',str(meta))
            if 'guid: '+guid not in meta.read_text(encoding='utf-8').splitlines():
                raise ValueError('Packaged original asset GUID mismatch: '+name)
            packaged_meta=(bundle.extractfile(members[guid+'/asset.meta'])
                           if guid+'/asset.meta' in members else None)
            if packaged_meta is None:
                raise ValueError('Packaged importer metadata missing: '+name)
            actual_meta=packaged_meta.read()
            if actual_meta!=meta.read_bytes():
                if not _accepted_unity2022_monoimporter_default(meta.read_bytes(),actual_meta,name):
                    raise ValueError('Packaged import settings differ from original source: '+name)
                normalized_meta.append(name)
        missing={ROOT+'/'+f for f in REQUIRED}-set(paths)
        if missing:
            raise ValueError('Required buyer files absent: '+str(sorted(missing)))
    return {
        'status':'ORIGINAL_UNITY_CUSTOMER_CONTENT_MATCHES_SOURCE_WITH_EXPLICIT_META_NORMALIZATION',
        'consumer_exported_paths':len(paths),
        'unity2022_exact_default_MonoImporter_metadata_normalizations':normalized_meta,
        'all_customer_content_bytes_match_original':True,
        'root':ROOT,
        'buyer_readme_present':True,
        'actual_demo_scene_present':True,
        'independent_original_archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
        'third_party_code_or_private_test_scripts_included':False,
    }


if __name__=='__main__':
    if len(sys.argv)!=3:raise SystemExit('usage: verify_original_demo_archive.py original.unitypackage source-assets-root')
    print(json.dumps(verify(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2])),sort_keys=True))
