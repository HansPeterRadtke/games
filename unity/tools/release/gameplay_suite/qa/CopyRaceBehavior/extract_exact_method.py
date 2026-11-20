#!/usr/bin/env python3
"""Extract ONLY the actual reviewed HPR Editor copier method into mock build.

This creates a single source file in a fresh private output directory.
The original source file and all Unity projects remain untouched. A fake
UnityEditor API executes deterministic collision scenarios; it is NOT a real
Unity Editor test, nor proof of cross-process atomic race safety.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re


def extract(source: Path, dest: Path):
    if not source.is_file() or source.is_symlink():
        raise ValueError("Exact non-symlink C# source required")
    if dest.exists() or dest.is_symlink():
        raise FileExistsError("Refusing existing fake Editor method output")
    raw = source.read_bytes()
    text = raw.decode('utf-8')
    identity = 'internal static UnityEngine.Object CopySampleToCustomerPath('
    if text.count(identity) != 1:
        raise ValueError("Cannot identify exactly one product Editor copy method")
    start = text.index(identity)
    brace = text.index('{', start)
    level = 0
    end = None
    for i in range(brace, len(text)):
        if text[i] == '{': level += 1
        elif text[i] == '}':
            level -= 1
            if level == 0:
                end = i + 1
                break
    if end is None:
        raise ValueError("Unterminated copier method")
    match = re.search(r'private const string Root\s*=\s*"([^"\\]+)";',text)
    if match is None or match.group(1) != 'Assets/HPRGameplaySuite':
        raise ValueError("Unexpected original Unity source package root")
    method = text[start:end]
    if not all(s in method for s in ('AssetDatabase.CopyAsset(', 'AssetDatabase.SaveAssetIfDirty(',
                                    'lastAttemptedTarget = target;', 'No automatic cleanup was performed')):
        raise ValueError("Unexpected source: new guard or fail-forward missing")
    prefix = '''// Exact method text extracted from a private HPR product-source proposal.
// The rest of the assembly is a FAKE Unity Editor; not a real Unity test.
using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEditor;
namespace HPR.GameplaySuite {
  public static class HprSuiteIntegrationGuide {
    private const string Root = "Assets/HPRGameplaySuite";
'''
    dest.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    dest.write_text(prefix + method + '\n  }\n}\n')
    return {'original_source_sha256':hashlib.sha256(raw).hexdigest(),
            'method_sha256':hashlib.sha256(method.encode()).hexdigest(),
            'copied_method_bytes':len(method.encode()),
            'source_only_no_editor_launched':True}


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--receipt',type=Path,required=True)
    a=p.parse_args()
    if a.receipt.exists() or a.receipt.is_symlink():raise FileExistsError('Receipt exists')
    info=extract(a.source,a.output)
    with a.receipt.open('x',encoding='utf-8') as out:
        json.dump(info,out,indent=2)
        out.write('\n')
    a.receipt.chmod(0o600)
    print(json.dumps(info,sort_keys=True))
