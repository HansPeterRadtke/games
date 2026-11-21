"""Verify three original Unity-exported training archives from authored text.

Do not substitute synthetic archive generation for real Unity Editor native QA;
those actual author/export and buyer import receipts remain private and
must be checked separately before commercial use.
"""
from pathlib import Path
import hashlib
import importlib.util
import re
import tarfile

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'unity/tools/release/unitypackage_archive_preflight'
VENDOR=PACKAGE/'Assets/HPRArchivePreflight'
SAMPLES=VENDOR/'Samples'
WRITER=PACKAGE/'qa/build_original_sample_sources.py'
PINNED={
 'baseline':'cfce8257e52bb4cc393ee5fb6f09214efbe75a4a5cba537e0e2389340b9fae61',
 'additions_only':'08d66b07a8555e578f42d0f1fe5774a8d9c1f1117d5cc7c792ee31c33cf2df63',
 'changed_guid':'1fadaab248f09c68585c5268cca03050803e3008d349ed03f8c3a81769b00dec'
}


def source_writer():
    spec=importlib.util.spec_from_file_location('hpr_example_source_generator',WRITER)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def inspect_original_unity_archive(variant):
    src=source_writer()
    p=SAMPLES/f'HprExample-{variant}.unitypackage'
    assert p.is_file() and p.stat().st_size>100
    assert hashlib.sha256(p.read_bytes()).hexdigest()==PINNED[variant]
    meta=p.with_name(p.name+'.meta')
    assert meta.is_file()
    files={};bytes_map={};guid_from_meta={}
    with tarfile.open(p,'r:gz') as archive:
        for item in archive:
            if item.isdir():continue
            assert item.isfile() and not item.issym()
            name=item.name.removeprefix('./')
            token=name.split('/')
            assert len(token)==2 and re.fullmatch('[0-9a-f]{32}',token[0])
            stream=archive.extractfile(item)
            assert stream is not None
            b=stream.read()
            if token[1]=='pathname':
                target=b.decode('utf-8').strip()
                assert target.startswith('Assets/HPRUpgradeExample')
                assert target not in files
                files[target]=token[0]
            elif token[1]=='asset':bytes_map[token[0]]=hashlib.sha256(b).hexdigest()
            elif token[1]=='asset.meta':
                assert re.search(rb'(?m)^guid: '+token[0].encode()+rb'\s*$',b)
                guid_from_meta[token[0]]=True
            else:raise AssertionError('Unexpected Unity original archive member type '+name)
    assert len(files)==(4 if variant=='additions_only' else 3)
    assert all(g in guid_from_meta for g in files.values())
    expected=('README.md','Example.txt','ADDED_NOTICE.txt') if variant=='additions_only' else ('README.md','Example.txt')
    for name in expected:
        path='Assets/HPRUpgradeExample/'+name
        guid=src.guid(name if not (variant=='changed_guid' and name=='README.md') else
                      'README.md-INTENTIONAL-GUID-REPLACEMENT')
        assert files[path]==guid
        assert bytes_map[guid]==hashlib.sha256(src.TEXT[name].encode('utf-8')).hexdigest()
    assert files['Assets/HPRUpgradeExample']==src.guid('root')
    return files


def test_actual_unity_exported_samples_are_original_and_intentional():
    results={variant:inspect_original_unity_archive(variant) for variant in PINNED}
    base=results['baseline'];add=results['additions_only'];broken=results['changed_guid']
    assert set(add)-set(base)=={'Assets/HPRUpgradeExample/ADDED_NOTICE.txt'}
    assert all(add[p]==g for p,g in base.items())
    assert set(broken)==set(base)
    assert sum(base[p]!=g for p,g in broken.items())==1
    assert base['Assets/HPRUpgradeExample/README.md']!=broken['Assets/HPRUpgradeExample/README.md']


def test_bundled_original_example_metadata_unique_and_buyer_qa_required():
    allmeta=[PACKAGE/'Assets/HPRArchivePreflight.meta'] + [p for p in (PACKAGE/'Assets/HPRArchivePreflight').rglob('*.meta')]
    guids=[]
    for p in allmeta:
        match=re.search(r'(?m)^guid: ([0-9a-f]{32})',p.read_text())
        assert match
        guids.append(match.group(1))
    assert len(guids)==len(set(guids))==11
    examples=sum(p.stat().st_size for p in SAMPLES.glob('*.unitypackage'))
    functional=sum(p.stat().st_size for p in (VENDOR/'Editor').glob('*.cs'))
    assert examples < functional // 5  # transparent samples cannot obscure majority of code
    qa=(PACKAGE/'qa/HprArchivePreflightNativeQa.cs').read_text()
    for name in ('all_three_first_party_archives_installed',
                 'three_genuine_unity_authored_example_archives_parse',
                 'included_example_explains_one_addition_not_an_engine_error',
                 'included_example_warns_about_intentionally_replaced_guid',
                 'included_genuine_sample_archive_bytes_not_edited_by_comparison'):
        assert name in qa
    assert 'Directory.GetParent(Application.dataPath)' in qa
    assert 'HPR_COEXISTENCE_MOVED_ARCHIVE' in qa
    assert 'File.Delete(' not in qa


def test_source_reproducibility_without_replaying_existing_origins():
    source=WRITER.read_text()
    assert 'TARGET.exists()' in source
    assert 'source-manifest.json' in source
    install=(PACKAGE/'qa/install_verified_original_example_archives.py').read_text()
    assert 'Refusing to overwrite existing vendor example assets' in install
    assert 'UNITY_NATIVE_EXPORT_VERIFIED.json' in install
    assert 'HPR_FIRST_PARTY_TRAINING_EXAMPLE_EXPORTED' in install
    assert 'Refusing to overwrite existing vendor example assets' in install
    runner=(PACKAGE/'qa/resume_original_example_exports_after_fixture_failure.sh').read_text()
    assert 'Unexpected first-party training example asset scope' in runner
    assert 'HPR_FIRST_PARTY_TRAINING_EXAMPLE_EXPORTED' in runner
