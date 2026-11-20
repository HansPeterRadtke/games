#!/usr/bin/env python3
"""Read-only, exact Unity bundle archive/import integrity checker; rejects added roots.

Requires an actual package produced by the Unity Editor. Never extracts or
modifies buyer files; requires stable GUID and exact .meta byte preservation.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import tarfile

MEMBER = re.compile(r'^([0-9a-f]{32})/(pathname|asset|asset.meta)$')
ALLOWED = {
    'Assets/HPRInputReadiness',
    'Assets/HPRInputReadiness/Editor',
    'Assets/HPRInputReadiness/Editor/HprInputReadinessAudit.cs',
    'Assets/HPRInputReadiness/README.md',
    'Assets/HPRAnimatorContract',
    'Assets/HPRAnimatorContract/Editor',
    'Assets/HPRAnimatorContract/Editor/HprAnimatorContractAudit.cs',
    'Assets/HPRAnimatorContract/README.md',
    'Assets/HPRProjectPreflight',
    'Assets/HPRProjectPreflight/Editor',
    'Assets/HPRProjectPreflight/Editor/HprProjectPreflightWindow.cs',
    'Assets/HPRProjectPreflight/README.md',
}


def verify(package: Path, project: Path):
    errors, blobs, paths = [], {}, {}
    with tarfile.open(package, 'r:gz') as archive:
        for member in archive:
            # Unity 2022 prefixes members with ./ and emits GUID directories;
            # Unity 6 uses plain GUID paths without explicit directory entries.
            name = member.name[2:] if member.name.startswith('./') else member.name
            if member.isdir():
                if name in ('.', '') or re.fullmatch(r'[0-9a-f]{32}/?', name):
                    continue
                errors.append('Unexpected directory: ' + member.name)
                continue
            if not member.isfile() or not MEMBER.fullmatch(name):
                errors.append('Unexpected member: '+member.name)
                continue
            if name in blobs or member.size > 8 * 1024 * 1024:
                errors.append('Duplicate or too-large member: '+member.name)
                continue
            data = archive.extractfile(member)
            if data is None:
                errors.append('Unreadable member: '+member.name)
                continue
            blobs[name] = data.read()
    for name, raw in blobs.items():
        match = MEMBER.fullmatch(name)
        if not match or match[2] != 'pathname':
            continue
        guid = match[1]
        try:
            path = raw.decode('utf-8').strip()
        except UnicodeDecodeError:
            errors.append('Non-UTF8 pathname');continue
        path_obj = PurePosixPath(path)
        if path not in ALLOWED or '..' in path_obj.parts or path_obj.is_absolute() or '\\' in path:
            errors.append('Unexpected asset pathname: '+path)
            continue
        if path in paths:
            errors.append('Duplicate path: '+path)
            continue
        paths[path] = guid
        payload = blobs.get(guid+'/asset')
        meta = blobs.get(guid+'/asset.meta')
        if meta is None or not re.search(rb'(?m)^guid:\s*'+guid.encode()+rb'\s*$',meta):
            errors.append('Invalid missing metadata/GUID: '+path)
            continue
        target = project/path
        target_meta = Path(str(target)+'.meta')
        if target.is_symlink() or target_meta.is_symlink():
            errors.append('Symlink in target: '+path);continue
        if payload is None:
            if not target.is_dir(): errors.append('Folder missing: '+path)
        elif not target.is_file() or target.read_bytes()!=payload:
            errors.append('Asset bytes differ: '+path)
        if not target_meta.is_file() or target_meta.read_bytes()!=meta:
            errors.append('Meta bytes differ: '+path)
    if set(paths)!=ALLOWED:
        errors.append('Archive path set differs from exactly twelve approved assets: '+str(sorted(ALLOWED-set(paths))))
    return {'status':'PASS' if not errors else 'FAIL','issues':errors,
            'paths_verified':len(paths),
            'source_scripts_verified':sum(x.endswith('.cs') for x in paths),
            'package_sha256':hashlib.sha256(package.read_bytes()).hexdigest()}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,required=True)
    parser.add_argument('--project',type=Path,required=True)
    parser.add_argument('--receipt',type=Path)
    args=parser.parse_args()
    result=verify(args.archive,args.project)
    if args.receipt:
        with args.receipt.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
    print(json.dumps(result,indent=2))
    return 0 if result['status']=='PASS' else 1

if __name__=='__main__':
    raise SystemExit(main())
