#!/usr/bin/env python3
"""Deterministic wholly first-party Unity demo package source builder.

Only creates files in previously absent private producer-owned directories.
Actual .unitypackage files MUST be exported by installed Unity, not mocked.
Never publishes, downloads or modifies an existing Unity project or archive.
"""
from pathlib import Path
import hashlib
import json

ROOT=Path('/data/var/marketplace-account-setup/unity-20261121-wave51')
TARGET=ROOT/'original-archive-sample-authoring'
ASSET_ROOT='Assets/HPRUpgradeExample'
TEXT={
 'README.md': '# HPR training archive - publisher update demonstration\n\nThis material is original example content for an archive identity comparison, not evidence of a Unity engine defect.\n',
 'Example.txt': 'HPR example asset. Version one intentionally keeps its GUID and content in the additive update.\n',
 'ADDED_NOTICE.txt': 'New first-party text asset introduced without changing any previous package asset identities or source bytes.\n',
}


def guid(name):
    return hashlib.sha256(('hpr-preimport-educational-example/2026-11-21/'+name).encode()).hexdigest()[:32]


def make(variant):
    target=TARGET/variant
    if target.exists(): raise RuntimeError('Refusing to overwrite previous original Unity sample source: '+str(target))
    source=target/'Assets/HPRUpgradeExample'
    source.mkdir(parents=True)
    names=('README.md','Example.txt') if variant!='additions_only' else ('README.md','Example.txt','ADDED_NOTICE.txt')
    foldermeta=target/'Assets/HPRUpgradeExample.meta'
    foldermeta.write_text('fileFormatVersion: 2\nguid: '+guid('root')+'\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n')
    records={}
    for name in names:
        dest=source/name
        dest.write_text(TEXT[name],encoding='utf-8')
        identity=guid(name if not (variant=='changed_guid' and name=='README.md') else 'README.md-INTENTIONAL-GUID-REPLACEMENT')
        dest.with_name(name+'.meta').write_text('fileFormatVersion: 2\nguid: '+identity+'\nDefaultImporter:\n  externalObjects: {}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n')
        records[name]={'guid':identity,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()}
    assert len(set([guid('root')]+[x['guid'] for x in records.values()]))==len(records)+1
    return {'variant':variant,'root_guid':guid('root'),'source_assets':records}


def main():
    if TARGET.exists():raise RuntimeError('Refusing duplicate generation or existing target tree')
    manifest={'source':'HPR original, deterministic first-party text demonstration', 'variants':[]}
    for variant in ('baseline','additions_only','changed_guid'):
        manifest['variants'].append(make(variant))
    with (TARGET/'source-manifest.json').open('x',encoding='utf-8') as f:
        json.dump(manifest,f,indent=2)
    print('ORIGINAL_SAMPLE_SOURCES_CREATED',len(manifest['variants']),'source manifest',TARGET/'source-manifest.json')

if __name__=='__main__':main()
