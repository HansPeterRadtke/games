"""Original two-take FBX source visibility candidate: release boundaries and QA."""
from pathlib import Path
import importlib.util
import io
import hashlib
import re
import tarfile

ROOT=Path(__file__).resolve().parents[1]
PKG=ROOT/'unity/tools/release/fbx_source_take_visibility'
VENDOR=PKG/'Assets/HPRFbxSourceTakes'


def _checker():
    spec=importlib.util.spec_from_file_location('source_takes_verifier',PKG/'qa/verify_archive.py')
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_vendor_scope_original_guid_and_blender_sample():
    checker=_checker()
    assert len(checker.ALLOWED)==14
    guids=[]
    for path in checker.ALLOWED:
        assert path.startswith('Assets/HPRFbxSourceTakes')
        local=PKG/'Assets'/Path(path).relative_to('Assets')
        meta=Path(str(local)+'.meta')
        assert local.exists() and meta.is_file()
        guid=re.search(r'^guid: ([a-f0-9]{32})$',meta.read_text(),re.M)
        assert guid
        guids.append(guid.group(1))
    assert len(set(guids))==14
    original=VENDOR/'Samples/HPRTwoTakeCube.fbx'
    assert hashlib.sha256(original.read_bytes()).hexdigest()==(
        '280dfbfcc7b3288fea028268ed214f3dd36b589e647051c3f051e02dc7b66e1f')
    assert set(VENDOR.rglob('*.fbx'))=={original,VENDOR/'Samples/HPRTwoTakeCustomMissing.fbx'}
    assert original.read_bytes()==(VENDOR/'Samples/HPRTwoTakeCustomMissing.fbx').read_bytes()
    assert not list(VENDOR.rglob('*.dll'))
    assert 'Blender' in (VENDOR/'README.md').read_text()
    assert (VENDOR/'Samples/Prefabs/OriginalAutoTwoTake.prefab').is_file()
    assert (VENDOR/'Samples/Prefabs/OriginalConfiguredMissingTake.prefab').is_file()
    assert (VENDOR/'Samples/Scenes/SourceTakeVisibilityDemo.unity').is_file()


def test_editor_sources_are_readonly_and_classify_automatic_vs_custom():
    scanner=(VENDOR/'Editor/HprFbxSourceTakeAudit.cs').read_text()
    window=(VENDOR/'Editor/HprFbxSourceTakeWindow.cs').read_text()
    for required in ('importer.defaultClipAnimations','importer.clipAnimations','importer.importAnimation',
                     'SOURCE_TAKES_NOT_IN_CUSTOM_LIST','DEFAULT_SOURCE_TAKES_ACTIVE',
                     'NO_CUSTOMER_FBX_MODELS_SCANNED','NO_MISSING_SOURCE_TAKES_IN_INSPECTED_CUSTOM_LISTS',
                     'ExampleOmittedTakeFbxPath',
                     'NO_ENABLED_SOURCE_ANIMATIONS_CHECKED','SourceTakeScanReport',
                     'MaxTakesPerModel','StringComparer.Ordinal','FileMode.CreateNew',
                     'result.incomplete = true','ModelImporterClipAnimation'):
        assert required in scanner
    for dangerous in ('SaveAndReimport(', 'AssetDatabase.DeleteAsset(',
                      'AssetDatabase.MoveAsset(', 'AssetDatabase.ImportPackage(',
                      'AssetDatabase.SaveAssets(', 'UnityWebRequest', 'File.Delete(',
                      'FileMode.Create,', 'Process.Start('):
        assert dangerous not in scanner+'\n'+window
    for required in ('Tools/HPR/FBX Source Take Visibility',
                     'Inspect included original two-take example',
                     'Inspect sample with a deliberately omitted source take',
                     'Inspect selected model without changes',
                     'Scan all customer FBX models (cancelable)',
                     'EditorUtility.ClearProgressBar()',
                     'Export JSON into a NEW report file',
                     'Import Unreferenced Takes'):
        assert required in window


def test_original_unity_probe_and_customer_customization_path_is_private():
    qa=(PKG/'qa/HprFbxSourceTakeNativeQa.cs').read_text()
    runner=(PKG/'qa/run_native_acceptance.sh').read_text()
    for item in ('HPR_SOURCE_TAKE_PROBE_SUCCESS','original_source_take_count',
                 'two_distinct_source_takes_exist','real_missing_source_take_discovered_by_original_scanner',
                 'normal_split_clip_duplicate_take_not_false_positive',
                 'included_deliberately_missing_source_take_detected_by_actual_Unity_import',
                 'empty_custom_list_defaults_not_false_positive',
                 'private_source_fbx_bytes_preserved',
                 'create_only_report_cannot_overwrite'):
        assert item in qa
    assert 'importer.SaveAndReimport()' in qa
    assert 'Assets/HPRPrivateSourceTakes/OriginalTwoTake.fbx' in qa
    assert 'HprFbxSourceTakeAudit.ExampleFbxPath' in qa
    assert 'buyer-original-probe' in runner and 'buyer-private-audit' in runner
    assert 'author-original-export' in runner and 'original-export-verified.json' in runner
    assert 'run_real_case' not in runner
    source_change=(PKG/'qa/run_actual_source_update.sh').read_text()
    for keyword in ('HPRFirstTakeOnly.fbx','PrepareActualSourceChange','AuditActualSourceChange',
                    'first-party-inputs-before.sha256','first-party-inputs-after.sha256'):
        assert keyword in source_change
    assert 'HPR_ACTUAL_FBX_SOURCE_UPDATE_VISIBILITY_PASS' in qa
    assert 'HPR_SOURCE_TAKE_EXPORT_PASS' in (PKG/'qa/HprFbxSourceTakeExporter.cs').read_text()
    author=(PKG/'qa/HprFbxDemoSceneAuthor.cs').read_text()
    assert 'PrefabUtility.SaveAsPrefabAsset(' in author and 'EditorSceneManager.SaveScene(' in author
    assert 'HPR_ORIGINAL_UNITY_SOURCE_TAKE_DEMO_CREATED' in author
    assert 'run_original_demo_author.sh' in str(PKG/'qa/run_original_demo_author.sh')
    assert 'demo_scene_and_both_prefabs_imported_and_resolve' in qa


def _fixture(tar_path,change=False,extra=False):
    allowed=sorted(_checker().ALLOWED)
    with tarfile.open(tar_path,'w:gz') as tar:
        for path in allowed:
            original=PKG/'Assets'/Path(path).relative_to('Assets')
            meta=Path(str(original)+'.meta')
            guid=re.search(r'^guid: ([a-f0-9]{32})$',meta.read_text(),re.M).group(1)
            parts=[('pathname',path.encode()),('asset.meta',meta.read_bytes())]
            if original.is_file():
                b=original.read_bytes()
                if change and original.suffix=='.cs':b+=b'\n// modified source'
                parts.append(('asset',b))
            for kind,data in parts:
                info=tarfile.TarInfo(guid+'/'+kind);info.size=len(data)
                tar.addfile(info,io.BytesIO(data))
        if extra:
            data=b'Assets/Unknown/NotOwned.cs'
            info=tarfile.TarInfo('f'*32+'/pathname');info.size=len(data)
            tar.addfile(info,io.BytesIO(data))


def test_fail_closed_archive_verifier_rejects_tamper_and_extra_content(tmp_path):
    check=_checker()
    clean=tmp_path/'good.unitypackage';_fixture(clean)
    assert check.verify(clean)['verified_vendor_paths']==14
    bad=tmp_path/'tamper.unitypackage';_fixture(bad,change=True)
    try:check.verify(bad)
    except ValueError as e:assert 'source' in str(e).lower()
    else:raise AssertionError('Tampered original script accepted')
    extra=tmp_path/'extra.unitypackage';_fixture(extra,extra=True)
    try:check.verify(extra)
    except ValueError as e:assert 'asset' in str(e).lower() or 'vendor' in str(e).lower()
    else:raise AssertionError('Non-first-party content accepted')


def test_real_editor_authored_scene_prefabs_and_true_importer_sample_identity():
    original=VENDOR/'Samples/HPRTwoTakeCube.fbx'
    missing=VENDOR/'Samples/HPRTwoTakeCustomMissing.fbx'
    assert original.read_bytes()==missing.read_bytes()
    healthy_meta=Path(str(original)+'.meta').read_text()
    missing_meta=Path(str(missing)+'.meta').read_text()
    assert '    clipAnimations: []' in healthy_meta
    assert missing_meta.count('      takeName: ')==1
    assert 'HPR_Original_Two_Take_Cube|HPR_Original_Hop' in missing_meta
    scene=(VENDOR/'Samples/Scenes/SourceTakeVisibilityDemo.unity').read_text()
    assert '%YAML 1.1' in scene
    source_identifiers={}
    for model in (original,missing):
        source_identifiers[model.name]=re.search(r'^guid: ([a-f0-9]{32})$',
            Path(str(model)+'.meta').read_text(),re.M).group(1)
    assert len(set(source_identifiers.values()))==2
    for prefab_name, model in [('OriginalAutoTwoTake','HPRTwoTakeCube.fbx'),
                               ('OriginalConfiguredMissingTake','HPRTwoTakeCustomMissing.fbx')]:
        prefab=VENDOR/f'Samples/Prefabs/{prefab_name}.prefab'
        meta=Path(str(prefab)+'.meta')
        guid=re.search(r'^guid: ([a-f0-9]{32})$',meta.read_text(),re.M).group(1)
        assert guid in scene  # actual nested prefab referenced in genuine scene
        assert source_identifiers[model] in prefab.read_text()  # genuine imported FBX source
    assert 'camera_and_key_light_and_two_model_prefab_instances=PASS' in (
        (PKG/'qa/HprFbxDemoSceneAuthor.cs').read_text())
