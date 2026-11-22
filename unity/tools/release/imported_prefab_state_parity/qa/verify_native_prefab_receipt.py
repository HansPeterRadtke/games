#!/usr/bin/env python3
"""Independent original-prefab-file hash verifier for native Unity Editor receipts."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os

COMPARATOR=Path(__file__).with_name('compare_native_receipts.py')
MAX_FILE=64*1024*1024
MAX_TOTAL=256*1024*1024


def digest(path: Path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size>MAX_FILE:
        raise ValueError('Original prefab source file missing, linked or oversized')
    sha=hashlib.sha256()
    with path.open('rb') as stream:
        while True:
            data=stream.read(1024*1024)
            if not data:break
            sha.update(data)
    return sha.hexdigest()


def verify(project: Path,receipt: Path):
    if not project.is_dir() or not (project/'Assets').is_dir():
        raise ValueError('Existing original imported Unity project required')
    spec=importlib.util.spec_from_file_location('hpr_prefab_state_comparison',COMPARATOR)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    data,inputs,values=m.load(receipt)
    total=0
    root=project.resolve(strict=True)
    for path,(src,meta) in inputs.items():
        for name,wanted in ((path,src),(path+'.meta',meta)):
            local=project/name
            if local.is_symlink() or not local.is_file():raise ValueError('Missing original file')
            absolute=local.resolve(strict=True)
            if not absolute.is_relative_to(root):raise ValueError('Path escaped Unity project')
            actual=digest(absolute)
            if actual!=wanted:raise ValueError('Original input bytes differ from actual native scan receipt')
            total+=absolute.stat().st_size
            if total>MAX_TOTAL:raise ValueError('Total scanned file size is over bound')
    return {'status':'PASS','original_unity_version':data['unityVersion'],
            'original_prefabs':len(inputs),'native_imported_values':len(values),
            'uncovered_component_types':data['unsupportedComponents'],
            'original_prefab_and_meta_files':2*len(inputs),'total_verified_source_bytes':total}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('project',type=Path);p.add_argument('receipt',type=Path)
    a=p.parse_args()
    print(json.dumps(verify(a.project,a.receipt),sort_keys=True))


if __name__=='__main__':main()
