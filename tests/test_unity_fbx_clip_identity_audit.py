"""Original read-only FBX clip-ID candidate policy and archive safety tests."""
from pathlib import Path
import io
import hashlib
import importlib.util
import re
import tarfile

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'unity/tools/release/fbx_clip_identity_audit'
VENDOR=BASE/'Assets/HPRFbxClipIdentity'


def _checker():
    spec=importlib.util.spec_from_file_location('hpr_fbx_archive',BASE/'qa/verify_archive.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def test_no_dangerous_or_unintended_buyer_actions():
    code='\n'.join(p.read_text() for p in (VENDOR/'Editor').glob('*.cs'))
    for expected in ('AnalyzeMetaText','internalIDToNameTable:',
                     'DUPLICATE_ANIMATION_CLIP_LOCAL_ID','DisplayCancelableProgressBar',
                     'NO_DUPLICATE_IDS_IN_CHECKED_MODELS','INCOMPLETE',
                     'InspectConfiguredClipIds','DUPLICATE_CONFIGURED_CLIP_INTERNAL_ID',
                     'ModelImporter','AssetDatabase.GetAllAssetPaths','FileMode.CreateNew',
                     'HprFbxClipIdentityAudit.ScanAssets',
                     'HprFbxClipIdentityAudit.ScanSingle',
                     'NO_ANIMATION_CLIPS_IN_CHECKED_MODELS', 'ExampleFbxPath',
                     'Check selected FBX','Check included animated FBX'):
        assert expected in code
    for forbidden in ('AssetDatabase.DeleteAsset(', 'AssetDatabase.MoveAsset(',
                      'SaveAndReimport(', 'AssetDatabase.ImportPackage(',
                      'AssetDatabase.SaveAssets(', 'EditorSettings.',
                      'FileMode.Create,', 'UnityWebRequest',
                      'System.Diagnostics.Process', 'File.Delete('):
        assert forbidden not in code


def test_fbx_vendor_guid_stability_and_fixed_scope():
    guid=[]
    for relative in ('', 'Editor','Editor/HprFbxClipIdentityAudit.cs',
                     'Editor/HprFbxClipIdentityWindow.cs','README.md','LICENSE.md',
                     'Samples','Samples/OriginalMotion.fbx',
                     'Samples/Prefabs','Samples/Prefabs/OriginalMotionTeachingPrefab.prefab'):
        path=VENDOR/relative if relative else VENDOR
        meta=Path(str(path)+'.meta')
        assert meta.is_file()
        match=re.search(r'^guid: ([a-f0-9]{32})$',meta.read_text(),re.M)
        assert match,meta
        guid.append(match.group(1))
    assert len(guid)==len(set(guid))==10
    assert [p.name for p in VENDOR.rglob('*.fbx')]==['OriginalMotion.fbx']
    assert hashlib.sha256((VENDOR/'Samples/OriginalMotion.fbx').read_bytes()).hexdigest()==(
        '31653edfe077ed23821719a361c8baa61626b55c78f20ea340ee148ed3747cc4')
    assert (VENDOR/'Samples/Prefabs/OriginalMotionTeachingPrefab.prefab').is_file()
    assert '45b9992fb14f47829da153fd996cd315' in (VENDOR/'Samples/Prefabs/OriginalMotionTeachingPrefab.prefab').read_text()
    assert not list(VENDOR.rglob('*.dll'))
    assert 'read-only' in (VENDOR/'README.md').read_text().lower()


def _synthetic_package(path,extra=False,tamper=False):
    """Format-only synthetic TAR fixture. Not real Unity acceptance."""
    checker=_checker()
    with tarfile.open(path,'w:gz') as tar:
        for relative in sorted(checker.ALLOWED):
            item=BASE/'Assets'/Path(relative).relative_to('Assets')
            meta=Path(str(item)+'.meta')
            guid=re.search(r'^guid: ([a-f0-9]{32})$',meta.read_text(),re.M).group(1)
            items=(('pathname',relative.encode()),('asset.meta',meta.read_bytes()),
                   ('asset',item.read_bytes()+(b'bad' if tamper and item.name.endswith('Audit.cs') else b'')) if item.is_file() else ('',b''))
            for suffix,data in items:
                if not suffix:continue
                m=tarfile.TarInfo(guid+'/'+suffix);m.size=len(data);tar.addfile(m,io.BytesIO(data))
        if extra:
            data=b'Assets/Other/Bad.cs';m=tarfile.TarInfo('f'*32+'/pathname');m.size=len(data);tar.addfile(m,io.BytesIO(data))


def test_archive_rejects_tamper_and_wrong_package_scope(tmp_path):
    checker=_checker()
    clean=tmp_path/'clean.unitypackage';_synthetic_package(clean)
    assert checker.inspect(clean)['buyer_paths']==10
    changed=tmp_path/'changed.unitypackage';_synthetic_package(changed,tamper=True)
    try:checker.inspect(changed)
    except ValueError as ex:assert 'source' in str(ex).lower()
    else:raise AssertionError('Wrong source accepted')
    expanded=tmp_path/'expanded.unitypackage';_synthetic_package(expanded,extra=True)
    try:checker.inspect(expanded)
    except ValueError as ex:assert 'asset' in str(ex).lower()
    else:raise AssertionError('Nonbuyer files allowed')


def test_native_qa_uses_real_original_fbx_and_negative_checks():
    qa=(BASE/'qa/HprFbxClipIdentityNativeQa.cs').read_text()
    for expected in ('ModelImporter','AssetImporter.GetAtPath',
                     'real_blender_animation_imported_and_checked',
                     'deliberate_duplicate_animation_id_detected',
                     'non_animation_class_id_not_false_positive',
                     'malformed_metadata_fails_closed','modelClipCount >= 1',
                     'Hash(beforeMeta)','HPR_FBX_CLIP_IDENTITY_NATIVE_PASS'):
        assert expected in qa
    exporter=(BASE/'qa/HprFbxClipIdentityExporter.cs').read_text()
    assert 'ExportPackageOptions.Recurse' in exporter
    assert 'HPR_FBX_CLIP_IDENTITY_EXPORT_PASS' in exporter
    script=(BASE/'qa/run_native_acceptance.sh').read_text()
    assert 'buyer-real-model-qa' in script and 'buyer-import' in script
    assert 'buyer-sample-only-native' in script and 'HPR_FBX_SAMPLE_ONLY_QA_OUT' in script


def test_empty_project_and_incomplete_report_are_distinct_from_clean():
    scanner=(VENDOR/'Editor/HprFbxClipIdentityAudit.cs').read_text()
    assert 'NO_FBX_MODELS_SCANNED' in scanner
    assert 'report.modelsChecked == 0' in scanner
    assert 'report.modelsChecked != report.models.Length' in scanner
    qa=(BASE/'qa/HprFbxClipIdentityNativeQa.cs').read_text()
    assert 'empty_project_does_not_claim_a_clean_fbx_scan' in qa
    assert 'malformed_combined_report_fails_closed' in qa


def test_customer_sample_is_documented_and_native_qa_covers_single_model():
    readme=(VENDOR/'README.md').read_text()
    for detail in ('OriginalMotion.fbx','Check included animated FBX',
                   'Check selected FBX', 'Scan all FBX'):
        assert detail in readme
    qa=(BASE/'qa/HprFbxClipIdentityNativeQa.cs').read_text()
    for check in ('sample_model_is_original_blender_animation',
                  'selected_model_single_scan', 'sample_one_click_source_scan',
                  'clipless_scan_not_misreported_clean'):
        assert check in qa


def test_bundled_sample_does_not_make_customer_project_scan_look_clean():
    src=(VENDOR/'Editor/HprFbxClipIdentityAudit.cs').read_text()
    assert '!string.Equals(p, ExampleFbxPath, StringComparison.OrdinalIgnoreCase)' in src
    assert 'RelatedSourceTakeHealthyExample' in src and 'RelatedSourceTakeMissingExample' in src
    assert 'Run the demo check separately' in src
    qa=(BASE/'qa/HprFbxSampleOnlyQa.cs').read_text()
    assert 'independent_buyer_project_contains_only_shipped_fbx_sample' in qa
    assert 'project_scan_must_not_report_bundled_sample_as_customer_model' in qa
    assert 'HPR_FBX_SAMPLE_ONLY_QA_PASS' in qa
    assert 'source_fbx_and_import_metadata_unchanged_by_both_scan_modes' in qa
    assert 'FileMode.CreateNew' in qa
