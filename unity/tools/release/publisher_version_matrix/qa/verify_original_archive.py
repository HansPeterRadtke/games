#!/usr/bin/env python3
"""Exact original first-party Unity exported archive and stable GUID verification."""
from pathlib import Path
import argparse,tarfile,re,json,hashlib,sys

SOURCE=Path(__file__).resolve().parents[1]/'Assets/HPRPublisherVersionMatrix'


def verify(path):
    expected={}
    for item in [SOURCE,*SOURCE.rglob('*')]:
        if item.is_file() and item.suffix=='.meta':continue
        if not item.is_file() and not item.is_dir():continue
        meta=Path(str(item)+'.meta')
        m=re.search(r'(?m)^guid: ([a-f0-9]{32})$',meta.read_text())
        if not m:raise ValueError('No original guid: '+str(item))
        name='Assets/'+str(item.relative_to(SOURCE.parent))
        expected[name]=(m.group(1),meta.read_bytes(),item.read_bytes() if item.is_file() else None)
    observed={}
    with tarfile.open(path,'r:gz') as tar:
        for ent in tar:
            # Unity native exports use a harmless leading ./ and directory records.
            name=ent.name[2:] if ent.name.startswith('./') else ent.name
            if ent.isdir() and (name in ('.','') or re.fullmatch('[a-f0-9]{32}',name)):
                continue
            parts=name.split('/')
            if len(parts)!=2 or not re.fullmatch('[a-f0-9]{32}',parts[0]) or parts[1] not in ('pathname','asset','asset.meta') or not ent.isfile():
                raise ValueError('Unexpected or unsafe archive entry: '+ent.name)
            data=tar.extractfile(ent).read()
            if len(data)>16_000_000:raise ValueError('Unexpected large archive record')
            slot=observed.setdefault(parts[0],{})
            if parts[1] in slot:raise ValueError('Duplicate archive entry')
            slot[parts[1]]=data
    paths={}
    for guid,parts in observed.items():
        if 'pathname' not in parts or 'asset.meta' not in parts:raise ValueError('Missing Unity asset pathname or metadata')
        name=parts['pathname'].decode('utf8')
        if name in paths:raise ValueError('Duplicate pathname')
        paths[name]=(guid,parts)
    if set(paths)!=set(expected):raise ValueError('Archive source paths mismatch')
    for name,(guid,meta,data) in expected.items():
        observed_guid,parts=paths[name]
        if observed_guid!=guid or parts['asset.meta']!=meta or parts.get('asset')!=data:
            raise ValueError('Original source or GUID rewritten at '+name)
    return {'status':'PASS','asset_paths':len(paths),'source_sha256':hashlib.sha256(SOURCE.joinpath('Editor/HprPublisherVersionMatrix.cs').read_bytes()).hexdigest(),'package_sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest()}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('package');args=parser.parse_args()
    print(json.dumps(verify(args.package),sort_keys=True))
