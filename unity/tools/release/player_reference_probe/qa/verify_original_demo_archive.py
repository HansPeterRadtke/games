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


def metadata_guid(data:bytes, name:str)->str:
    import re
    hits=re.findall(rb"(?m)^guid: ([0-9a-f]{32})\r?$",data)
    if len(hits)!=1:
        raise ValueError("Invalid original asset GUID metadata: "+name)
    return hits[0].decode("ascii")


def source_inventory(original_root:pathlib.Path)->dict:
    """Every first-party file AND folder must have a unique original meta.

    The top-level folder meta is a sibling of the source root, not inside it.
    Reject symlinks, orphan metadata and unexpected private files before copy.
    """
    if not original_root.is_dir() or original_root.is_symlink():
        raise ValueError("Missing or unsafe source root")
    paths={}
    identities=set()
    entries=[original_root]+sorted(original_root.rglob("*"))
    for source in entries:
        if source.is_symlink():
            raise ValueError("Unexpected symlink in original source: "+str(source))
        if source.name.endswith(".meta"):
            target=source.with_name(source.name[:-5])
            if not source.is_file() or not target.exists() or target.is_symlink():
                raise ValueError("Orphan or unsafe source meta: "+str(source))
            continue
        rel=source.relative_to(original_root).as_posix()
        name=ROOT if rel=="." else ROOT+"/"+rel
        if "/qa/" in name.lower() or "hprprobeqa" in name.lower() or name.lower().endswith(".exe"):
            raise ValueError("Private fixture leaked into customer product")
        if not source.is_file() and not source.is_dir():
            raise ValueError("Unexpected source entry: "+name)
        meta=source.with_name(source.name+".meta")
        if not meta.is_file() or meta.is_symlink():
            raise ValueError("Missing or unsafe source Unity meta: "+name)
        metadata=meta.read_bytes()
        guid=metadata_guid(metadata,name)
        if guid in identities:
            raise ValueError("Duplicate original source GUID: "+name)
        identities.add(guid)
        if source.is_dir() and b"folderAsset: yes" not in metadata.splitlines():
            raise ValueError("Original folder metadata missing folder flag: "+name)
        paths[name]=(source,metadata,guid)
    missing={ROOT+"/"+f for f in REQUIRED}-set(paths)
    if missing:
        raise ValueError("Required buyer files absent: "+str(sorted(missing)))
    return paths


def verify_metadata(source_bytes:bytes,actual_meta:bytes,name:str)->bool:
    if actual_meta==source_bytes:
        return False
    if _accepted_unity2022_monoimporter_default(source_bytes,actual_meta,name):
        return True
    raise ValueError("Packaged import settings differ from original source: "+name)


def verify(archive:pathlib.Path, original_root:pathlib.Path)->dict:
    if not archive.is_file() or archive.is_symlink():
        raise ValueError("Missing genuine archived buyer file")
    if archive.stat().st_size>5_000_000:
        raise ValueError("Unexpectedly large source-only first-party Unity archive")
    expected=source_inventory(original_root)
    paths={}
    guid_dirs=set()
    members={}
    normalized_meta=[]
    expanded=0
    # No extraction: the archive stays byte-for-byte unchanged.
    with tarfile.open(archive,"r:gz") as bundle:
        for count,info in enumerate(bundle,1):
            if count>512:
                raise ValueError("Too many archive entries")
            # Native Unity 2022 uses ./GUID; Unity 6 generally omits ./.
            name=info.name.removeprefix("./")
            if info.isdir():
                if name in ("","."):
                    continue
                name=name.rstrip("/")
                if len(name)!=32 or any(c not in "0123456789abcdef" for c in name):
                    raise ValueError("Unsafe unexpected Unity archive directory")
                guid_dirs.add(name)
                continue
            parts=name.split("/")
            if not info.isfile() or len(parts)!=2:
                raise ValueError("Unsafe or unexpected Unity package layout")
            guid,kind=parts
            if len(guid)!=32 or any(c not in "0123456789abcdef" for c in guid):
                raise ValueError("Malformed GUID directory")
            if kind not in ("pathname","asset","asset.meta","preview.png"):
                raise ValueError("Unexpected archive member")
            if name in members:
                raise ValueError("Duplicate normalized Unity package member")
            expanded+=info.size
            if info.size>5_000_000 or expanded>25_000_000:
                raise ValueError("Archive exceeds expanded source-only size budget")
            if kind=="pathname" and info.size>4096:
                raise ValueError("Excessive archive pathname")
            blob=bundle.extractfile(info).read()
            members[name]=blob
            guid_dirs.add(guid)
            if kind!="pathname":
                continue
            path=blob.decode("utf-8").strip()
            rel=pathlib.PurePosixPath(path)
            if (path!=rel.as_posix() or rel.is_absolute() or ".." in rel.parts or
                not (path==ROOT or path.startswith(ROOT+"/")) or path in paths):
                raise ValueError("Duplicate or unsafe exported archive pathname")
            if "/qa/" in path.lower() or "hprprobeqa" in path.lower() or path.lower().endswith(".exe"):
                raise ValueError("Private fixture leaked into customer product")
            if guid in paths.values():
                raise ValueError("Unity asset GUID reused for multiple exported paths")
            paths[path]=guid
        if set(paths.values())!=guid_dirs:
            raise ValueError("Unreferenced archive GUID files or missing pathname")
        if set(paths)!=set(expected):
            raise ValueError("Incomplete or unexpected archive inventory: missing="+
                str(sorted(set(expected)-set(paths)))+" extra="+str(sorted(set(paths)-set(expected))))
        for name,(source,metadata,guid) in expected.items():
            if paths[name]!=guid:
                raise ValueError("Packaged original asset GUID mismatch: "+name)
            actual_meta=members.get(guid+"/asset.meta")
            if actual_meta is None:
                raise ValueError("Packaged importer metadata missing: "+name)
            if metadata_guid(actual_meta,name)!=guid:
                raise ValueError("Packaged importer GUID mismatch: "+name)
            if verify_metadata(metadata,actual_meta,name):
                normalized_meta.append(name)
            archived=members.get(guid+"/asset")
            if source.is_dir():
                if archived not in (None,b""):
                    raise ValueError("Unexpected file payload for original folder: "+name)
                if b"folderAsset: yes" not in actual_meta.splitlines():
                    raise ValueError("Packaged folder metadata missing folder flag: "+name)
            elif archived is None or archived!=source.read_bytes():
                raise ValueError("Packaged consumer asset does not match original source: "+name)
    return {
        "status":"ORIGINAL_UNITY_CUSTOMER_CONTENT_MATCHES_SOURCE_WITH_EXPLICIT_META_NORMALIZATION",
        "consumer_exported_paths":len(paths),
        "root_folder_guid":paths[ROOT],
        "all_folder_and_file_guids_verified":True,
        "complete_original_inventory_verified":True,
        "unity2022_exact_default_MonoImporter_metadata_normalizations":normalized_meta,
        "all_customer_content_bytes_match_original":True,
        "root":ROOT,
        "buyer_readme_present":True,
        "actual_demo_scene_present":True,
        "independent_original_archive_sha256":hashlib.sha256(archive.read_bytes()).hexdigest(),
        "third_party_code_or_private_test_scripts_included":False,
    }


if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: verify_original_demo_archive.py original.unitypackage source-assets-root")
    print(json.dumps(verify(pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2])),sort_keys=True))
