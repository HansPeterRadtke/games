#!/usr/bin/env python3
"""Install newly created, author-verified first-party Unity sample inputs.

Every input is an already exported genuine Unity .unitypackage in a unique
producer-owned private authoring folder. This program refuses any existing
consumer file or metadata and never modifies an original author export.
"""
from pathlib import Path
import hashlib
import json
import os
import re
import tarfile

PROOF=Path('/data/var/marketplace-account-setup/unity-20261121-wave51/original-archive-sample-authoring')
SAMPLES=Path(__file__).resolve().parents[1]/'Assets/HPRArchivePreflight/Samples'
VARIANTS=('baseline','additions_only','changed_guid')


def stable_guid(name):
    return hashlib.sha256(('original-hpr-archive-sample-vendor-path/2026-11-21/'+name).encode()).hexdigest()[:32]


def verify_exact_original(source:Path, row:dict, variant:str, source_manifest:dict):
    if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest()!=row['sha256']:
        raise RuntimeError('Original Unity export SHA mismatched: '+variant)
    log=(source.parent/'original-export-resume1.unity.log' if variant=='baseline'
         else source.parent/'original-export.unity.log')
    if 'HPR_FIRST_PARTY_TRAINING_EXAMPLE_EXPORTED' not in log.read_text(errors='replace'):
        raise RuntimeError('No genuine installed Unity export result for '+variant)
    expected_source=next(x for x in source_manifest['variants'] if x['variant']==variant)
    decoded={};contents={};metas={}
    with tarfile.open(source,'r:gz') as archive:
        for member in archive:
            if not member.isfile():continue
            name=member.name.removeprefix('./')
            parts=name.split('/')
            if len(parts)!=2 or not re.fullmatch(r'[a-f0-9]{32}',parts[0]) or name in decoded:
                raise RuntimeError('Unexpected archive member in original Unity example: '+name)
            data=archive.extractfile(member).read()
            decoded[name]=data
            if parts[1]=='pathname':
                path=data.decode('utf8').strip()
                if path in row['assets'] and row['assets'][path]!=parts[0]:
                    raise RuntimeError('Actual exported sample path GUID mismatch')
            if parts[1]=='asset':contents[parts[0]]=hashlib.sha256(data).hexdigest()
            if parts[1]=='asset.meta':metas[parts[0]]=data
    expected_count=3 if variant!='additions_only' else 4
    if len(row['assets'])!=expected_count or len(row['assets'])!=len(metas):
        raise RuntimeError('Original Unity example package scope mismatch')
    for path,guid in row['assets'].items():
        if guid not in metas or decoded.get(guid+'/pathname',b'').decode('utf8').strip()!=path:
            raise RuntimeError('Missing actual source GUID or pathname')
        if not re.search(rb'(?m)^guid: '+guid.encode()+rb'\s*$',metas[guid]):
            raise RuntimeError('Meta GUID mismatch')
    for name,proof in expected_source['source_assets'].items():
        key='Assets/HPRUpgradeExample/'+name
        if row['assets'][key]!=proof['guid'] or contents[proof['guid']]!=proof['sha256']:
            raise RuntimeError('Not the original author educational source')


def main():
    if SAMPLES.exists() or Path(str(SAMPLES)+'.meta').exists():
        raise RuntimeError('Refusing to overwrite existing vendor example assets')
    proof=json.loads((PROOF/'UNITY_NATIVE_EXPORT_VERIFIED.json').read_text())
    origins=json.loads((PROOF/'source-manifest.json').read_text())
    for variant in VARIANTS:
        file=PROOF/variant/f'HprExample-{variant}.unitypackage'
        verify_exact_original(file,proof[variant],variant,origins)
    baseline=proof['baseline']['assets'];add=proof['additions_only']['assets'];changed=proof['changed_guid']['assets']
    if not (all(add.get(p)==g for p,g in baseline.items()) and
            len(add)==len(baseline)+1 and len(changed)==len(baseline) and
            sum(baseline.get(p)!=g for p,g in changed.items())==1):
        raise RuntimeError('Real example upgrade scenarios are not distinct and correctly scoped')
    SAMPLES.mkdir()
    Path(str(SAMPLES)+'.meta').write_text('fileFormatVersion: 2\nguid: '+stable_guid('Samples')+'\nfolderAsset: yes\n')
    for variant in VARIANTS:
        file=PROOF/variant/f'HprExample-{variant}.unitypackage'
        target=SAMPLES/file.name
        with target.open('xb') as dest, file.open('rb') as source:
            while True:
                block=source.read(65536)
                if not block:break
                dest.write(block)
        target.with_name(target.name+'.meta').write_text('fileFormatVersion: 2\nguid: '+stable_guid(file.name)+'\n')
        if hashlib.sha256(target.read_bytes()).hexdigest()!=proof[variant]['sha256']:
            raise RuntimeError('Consumer embedded archive differs from Unity original')
    print('GENUINE_UNITY_SAMPLE_ARCHIVES_INSTALLED',len(VARIANTS),'FIRST_PARTY_ONLY=yes')
    print('SAMPLES_SCOPE',str(SAMPLES))

if __name__=='__main__':main()
