#!/usr/bin/env python3
"""Compare two complete first-party native Unity import receipts, create-only output.

This is a reviewer aid, NOT automated proof that asset serialization or runtime
behavior remains compatible. No project files or original receipts are modified.
"""
from __future__ import annotations
import argparse
import json
import os
import re
from pathlib import Path

GUID = re.compile(r"[a-f0-9]{32}\Z")
SHA256 = re.compile(r"[a-f0-9]{64}\Z")
MAX_BYTES = 8_000_000


def load_receipt(path):
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ValueError("Source receipt missing or above bounded maximum")
    report = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(report, dict) or report.get("schema") != 2 or report.get("failureReason") not in (None, "") or report.get("incomplete") is not False or report.get("status") != "SNAPSHOT_COMPLETE":
        raise ValueError("Cannot compare incomplete or non-final importer receipts")
    roots = report.get("rootFolders")
    version = report.get("unityVersion")
    rows = report.get("assets")
    if not isinstance(roots, str) or not roots.startswith("Assets/") or not isinstance(version, str) or not version or not isinstance(rows,list) or not 1 <= len(rows) <= 4000 or report.get("assetCount") != len(rows):
        raise ValueError("Malformed receipt metadata")
    if len(roots) > 2000 or any(not x.startswith("Assets/") or ".." in x or "\\" in x for x in roots.split(';')):
        raise ValueError("Invalid publisher root")
    names = {}
    guids = set()
    for row in rows:
        if not isinstance(row, dict): raise ValueError("Non-object imported asset")
        name = row.get("path")
        guid = row.get("guid")
        deps = row.get("directDependencies")
        source_hash = row.get("sourceFileSha256")
        meta_hash = row.get("metaFileSha256")
        if not isinstance(name, str) or len(name)>1200 or not name.startswith('Assets/') or ".." in name or "\\" in name or not isinstance(guid,str) or not GUID.fullmatch(guid) or guid in guids or not isinstance(source_hash,str) or not SHA256.fullmatch(source_hash) or not isinstance(meta_hash,str) or not SHA256.fullmatch(meta_hash) or not isinstance(deps,list) or len(deps)>4000 or any(not isinstance(x,str) or not x or len(x)>1200 for x in deps) or len(set(deps))!=len(deps) or name in names:
            raise ValueError("Malformed or duplicate asset path, GUID, or dependency")
        if not any(name.startswith(root+'/') for root in roots.split(';')):
            raise ValueError("Asset outside publisher roots")
        guids.add(guid)
        names[name] = (guid, sorted(deps), source_hash, meta_hash)
    return report, names


def compare(first, second):
    a,old=load_receipt(Path(first))
    b,new=load_receipt(Path(second))
    if a['rootFolders']!=b['rootFolders']:
        raise ValueError("Different package roots; refusing misleading comparison")
    if a['unityVersion']==b['unityVersion']:
        raise ValueError("Expected two different real Unity versions")
    deleted=sorted(set(old)-set(new))
    added=sorted(set(new)-set(old))
    guid_changed=sorted(k for k in set(old)&set(new) if old[k][0]!=new[k][0])
    deps_changed=sorted(k for k in set(old)&set(new) if old[k][1]!=new[k][1])
    source_changed=sorted(k for k in set(old)&set(new) if old[k][2]!=new[k][2])
    meta_changed=sorted(k for k in set(old)&set(new) if old[k][3]!=new[k][3])
    return {
        'schema':2,'status':'MATCHED_IMPORT_INPUT_BYTES_AND_METADATA' if not (deleted or added or guid_changed or deps_changed or source_changed or meta_changed) else 'REVIEW_DIFFERENCES',
        'tested_unity_versions':[a['unityVersion'],b['unityVersion']],
        'exact_publisher_roots':a['rootFolders'],
        'source_receipts':[str(Path(first).resolve()),str(Path(second).resolve())],
        'asset_counts':[a['assetCount'],b['assetCount']],
        'missing_from_second':deleted,'new_in_second':added,
        'guid_changes':guid_changed,'direct_dependency_changes':deps_changed,
        'source_file_changes':source_changed,'importer_meta_changes':meta_changed,
        'limitation':'Matching imported paths, GUIDs, original asset bytes, .meta bytes and direct dependencies cannot prove imported object field values, behavior, scripts, player builds, Play Mode, rendering, complete compatibility, or Asset Store approval.'
    }


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('first');parser.add_argument('second')
    parser.add_argument('--output',required=True)
    args=parser.parse_args(argv)
    out=Path(args.output).expanduser()
    if not out.is_absolute(): parser.error('--output requires an absolute path')
    if out.resolve() in (Path(args.first).resolve(),Path(args.second).resolve()):
        parser.error('Output must not replace source receipt')
    result=compare(args.first,args.second)
    fd=os.open(out,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w',encoding='utf-8') as fp:
        json.dump(result,fp,sort_keys=True,indent=2);fp.write('\n')
    print(result['status'],'assets',*result['asset_counts'],'different_fields',len(result['missing_from_second'])+len(result['new_in_second'])+len(result['guid_changes'])+len(result['direct_dependency_changes'])+len(result['source_file_changes'])+len(result['importer_meta_changes']))
    return 0 if result['status']=='MATCHED_IMPORT_INPUT_BYTES_AND_METADATA' else 2

if __name__=='__main__':
    raise SystemExit(main())
