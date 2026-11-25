#!/usr/bin/env python3
"""Stage original source and its root sibling .meta before Unity imports it.

Offline filesystem operations only. No Unity invocation, no changes to an
existing product tree. The optional existing-tree check is read-only.
"""
import argparse
from pathlib import Path
import shutil
from verify_original_demo_archive import ROOT, source_inventory, verify_metadata


def verify_existing(source:Path, assets:Path)->dict:
    original=source_inventory(source)
    candidate=source_inventory(assets/source.name)
    if set(candidate)!=set(original):
        raise ValueError("Existing product inventory differs from original")
    for name,(path,meta,guid) in original.items():
        actual,other_meta,other_guid=candidate[name]
        if other_guid!=guid:
            raise ValueError("Existing product GUID mismatch: "+name)
        if path.is_dir()!=actual.is_dir():
            raise ValueError("Existing product file/folder mismatch: "+name)
        verify_metadata(meta,other_meta,name)
        if path.is_file() and path.read_bytes()!=actual.read_bytes():
            raise ValueError("Existing product payload mismatch: "+name)
    return {"root_guid":original[ROOT][2],"verified_paths":len(original)}


def stage(source:Path, assets:Path)->dict:
    original=source_inventory(source)
    if source.name!=Path(ROOT).name:
        raise ValueError("Unexpected product source folder")
    if not assets.is_dir() or assets.is_symlink():
        raise ValueError("Fresh Assets folder required")
    dest=assets/source.name
    meta=assets/(source.name+".meta")
    if dest.exists() or dest.is_symlink() or meta.exists() or meta.is_symlink():
        raise FileExistsError("Refusing to replace existing product folder or root metadata")
    # Exclusive creation, no overwrite of prior work. A partial stage is not
    # accepted: caller must abandon the disposable project and use a new one.
    with meta.open("xb") as f:
        f.write(original[ROOT][1])
    shutil.copytree(source,dest,symlinks=True)
    return verify_existing(source,assets)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group()
    mode.add_argument("--root-guid",action="store_true")
    mode.add_argument("--verify-existing",action="store_true")
    parser.add_argument("source",type=Path)
    parser.add_argument("assets",type=Path,nargs="?")
    args=parser.parse_args()
    if args.root_guid:
        if args.assets is not None:parser.error("--root-guid takes one source")
        print(source_inventory(args.source)[ROOT][2])
    elif args.assets is None:parser.error("Assets directory required")
    else:
        import json
        print(json.dumps((verify_existing if args.verify_existing else stage)(args.source,args.assets)))
