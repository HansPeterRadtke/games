#!/usr/bin/env python3
"""Independent private verifier of real loaded prefab receipts; never edits inputs."""
import argparse
import json
import os
import re
from pathlib import Path

SHA = re.compile('[0-9a-f]{64}\\Z')
GUID = re.compile('[0-9a-f]{32}\\Z')


def load(path: Path):
    if not path.is_file() or path.stat().st_size > 8_000_000:
        raise ValueError('Missing or oversized original Unity prefab snapshot')
    data = json.loads(path.read_text(encoding='utf-8'))
    if (data.get('schema') != 2 or data.get('status') != 'CAPTURED_COVERED_PREFAB_VALUES'
            or data.get('incomplete') is not False or data.get('failureReason') not in (None, '')
            or not isinstance(data.get('unityVersion'), str)
            or not isinstance(data.get('inputs'), list) or not 1 <= len(data['inputs']) <= 24
            or not isinstance(data.get('dependencies'), list) or len(data['dependencies']) > 512
            or not isinstance(data.get('unverifiedDependencyPaths'), list) or len(data['unverifiedDependencyPaths']) > 64
            or not isinstance(data.get('values'), list) or not data['values']
            or len(data['values']) > 25000 or data.get('valuesCaptured') != len(data['values'])
            or not isinstance(data.get('unsupportedComponents'), int)
            or data['unsupportedComponents'] < 0):
        raise ValueError('No full native prefab-state data for comparison')
    inputs = {}
    for row in data['inputs']:
        p = row.get('path')
        if (not isinstance(p, str) or not p.startswith('Assets/') or not p.endswith('.prefab')
                or '..' in p or '\\' in p or p in inputs or len(p) > 500
                or not all(isinstance(row.get(k), str) and SHA.fullmatch(row[k])
                           for k in ('sourceSha256', 'metaSha256'))):
            raise ValueError('Unsafe or duplicate original prefab input')
        inputs[p] = (row['sourceSha256'], row['metaSha256'])
    verified = {}
    for dep in data['dependencies']:
        name = dep.get('path')
        if (not isinstance(name, str) or len(name)>500 or not name.startswith('Assets/')
                or '..' in name or '\\' in name or ':' in name or '//' in name
                or name in verified or name in inputs or
                not isinstance(dep.get('guid'),str) or not GUID.fullmatch(dep['guid']) or
                not all(isinstance(dep.get(k),str) and SHA.fullmatch(dep[k])
                        for k in ('sourceSha256','metaSha256'))):
            raise ValueError('Invalid or ambiguous referenced dependency hash evidence')
        verified[name] = (dep['guid'],dep['sourceSha256'],dep['metaSha256'])
    unverified = set()
    for name in data['unverifiedDependencyPaths']:
        if (not isinstance(name,str) or not name or len(name)>500 or
                name in unverified or name in verified or name in inputs):
            raise ValueError('Invalid unverified dependency path')
        unverified.add(name)
    prefixes = tuple('Prefab/'  + __import__('urllib.parse', fromlist=['quote']).quote(p, safe='') + '/'
                     for p in inputs)
    values = {}
    for row in data['values']:
        key, value = row.get('key'), row.get('value')
        if (not isinstance(key, str) or not isinstance(value, str) or not key
                or len(key) > 1100 or len(value) > 1100 or key in values
                or not key.startswith(prefixes)):
            raise ValueError('Invalid or duplicate imported prefab field')
        values[key] = value
    return data, inputs, values


def compare(first: Path, second: Path):
    a, ain, av = load(first)
    b, bin_, bv = load(second)
    if a['unityVersion'] == b['unityVersion'] or set(ain) != set(bin_):
        raise ValueError('Two Editor versions and same original prefab scope required')
    original_changed = sorted(k for k in ain if ain[k] != bin_[k])
    a_dependencies = {x['path']:(x['guid'],x['sourceSha256'],x['metaSha256'])
                      for x in a['dependencies']}
    b_dependencies = {x['path']:(x['guid'],x['sourceSha256'],x['metaSha256'])
                      for x in b['dependencies']}
    dependency_changed = sorted(k for k in set(a_dependencies)|set(b_dependencies)
                                if a_dependencies.get(k) != b_dependencies.get(k))
    unverified_paths = sorted(set(a['unverifiedDependencyPaths']) |
                              set(b['unverifiedDependencyPaths']))
    removed = sorted(set(av) - set(bv))
    added = sorted(set(bv) - set(av))
    changed = sorted(k for k in set(av) & set(bv) if av[k] != bv[k])
    return {
        'status': ('SOURCE_BYTES_DIFFER_NO_EDITOR_INFERENCE' if original_changed else
                   'DEPENDENCY_INPUTS_DIFFER_NO_EDITOR_INFERENCE' if dependency_changed else
                   'DEPENDENCIES_UNVERIFIED_NO_EDITOR_INFERENCE' if unverified_paths else
                   'REVIEW_IMPORTED_PREFAB_VALUE_DIFFERENCES' if (removed or added or changed) else
                   'COVERED_VALUES_MATCH_UNINSPECTED_COMPONENTS' if (a['unsupportedComponents']+b['unsupportedComponents']>0) else
                   'MATCHED_COVERED_IMPORTED_PREFAB_VALUES'),
        'first_unity_version': a['unityVersion'], 'second_unity_version': b['unityVersion'],
        'prefabs': sorted(ain), 'source_differences': original_changed,
        'dependency_differences': dependency_changed,
        'unverified_dependency_paths': unverified_paths,
        'removed_keys': removed, 'added_keys': added, 'changed_keys': changed,
        'unsupported_component_types': a['unsupportedComponents'] + b['unsupportedComponents'],
        'limitation': 'Only captured component fields and hashable referenced Assets input bytes. Builtin/package dependencies, project settings and runtime may be unverified.'
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('first', type=Path)
    parser.add_argument('second', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if not args.output.is_absolute() or args.output.resolve() in (args.first.resolve(), args.second.resolve()):
        parser.error('New absolute output path required; cannot overwrite sources')
    result = compare(args.first, args.second)
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write('\n')
    print(result['status'], 'source', len(result['source_differences']),
          'loaded differences', sum(len(result[k]) for k in ('removed_keys','added_keys','changed_keys')))
    return 0 if result['status'] == 'MATCHED_COVERED_IMPORTED_PREFAB_VALUES' else 2


if __name__ == '__main__':
    raise SystemExit(main())
