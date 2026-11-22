"""Original combined FBX importer preflight, source/identity and safety policy.

These Python tests are SOURCE tests. Only the separately stored native
Unity author+independent buyer receipts justify an installed buyer pass.
"""
from pathlib import Path
import importlib.util
import io
import tarfile

RELEASE = Path(__file__).resolve().parents[1] / 'unity/tools/release'
BUNDLE = RELEASE / 'animation_import_preflight_bundle'
SOURCE = BUNDLE / 'Assets/HPRAnimationImportPreflight'


def module():
    spec = importlib.util.spec_from_file_location('combined_archive_verifier',
        BUNDLE / 'qa/verify_combined_archive.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_new_first_party_combined_root_has_fixed_scope_and_unique_original_guids():
    mod = module()
    assert set(mod.SOURCES) == {
        'HPRFbxClipIdentity','HPRFbxSourceTakes','HPRAnimationImportPreflight'
    }
    seen = set()
    count = 0
    for root in mod.SOURCES.values():
        assert root.is_dir()
        for p in [root,*root.rglob('*')]:
            if not p.is_file() and not p.is_dir():
                continue
            if p.is_file() and p.name.endswith('.meta'):
                continue
            meta = Path(str(p)+'.meta')
            assert meta.is_file(),meta
            import re
            guid = re.search(r'(?m)^guid: ([a-f0-9]{32})$',meta.read_text())
            assert guid and guid.group(1) not in seen
            seen.add(guid.group(1)); count += 1
    assert count == 27
    assert (SOURCE/'Editor/HprAnimationImportPreflight.cs').is_file()
    assert not list(SOURCE.rglob('*.dll'))
    assert 'Documentation' in (SOURCE/'README.md').read_text()


def test_one_combined_window_and_no_buyer_file_mutation_or_network_effects():
    code = (SOURCE/'Editor/HprAnimationImportPreflight.cs').read_text()
    for required in (
        'Tools/HPR/Combined Animation Import Audit',
        'HprFbxClipIdentityAudit.ScanAssets', 'HprFbxSourceTakeAudit.ScanAssets',
        'Try included original healthy and warning examples',
        'HprFbxClipIdentityAudit.ScanSingle','HprFbxSourceTakeAudit.ScanSingle',
        'POTENTIAL_ANIMATION_IMPORT_ISSUES','NO_CUSTOMER_FBX_MODELS_SCANNED',
        'SameCustomerModels(clip,takes)','HashSet<string>(StringComparer.OrdinalIgnoreCase)',
        'NO_TARGETED_FINDINGS_IN_INSPECTED_MODELS','INCOMPLETE',
        'DisplayCancelableProgressBar','ClearProgressBar','FileMode.CreateNew',
        'Import Unreferenced Takes'):
        assert required in code
    for banned in ('SaveAndReimport(', 'AssetDatabase.ImportPackage(',
                   'AssetDatabase.DeleteAsset(', 'AssetDatabase.MoveAsset(',
                   'AssetDatabase.SaveAssets(', 'File.Delete(', 'FileMode.Create,',
                   'UnityWebRequest', 'System.Diagnostics.Process',
                   'EditorSettings.', 'UnityEditorInternal.'):
        assert banned not in code
    assert 'ids.modelsChecked != takes.modelsChecked' in code
    assert 'clip == null || clip.incomplete' in code
    assert 'takes == null || takes.incomplete' in code


def test_genuine_unity_two_generations_qa_isolated_and_buyer_scoped():
    test = (BUNDLE/'qa/HprCombinedAnimationNativeQa.cs').read_text()
    runner = (BUNDLE/'qa/run_native_acceptance.sh').read_text()
    for key in (
        'HPR_COMBINED_ANIMATION_VENDOR_ONLY_NATIVE_PASS',
        'HPR_COMBINED_ANIMATION_CUSTOMER_HEALTHY_NATIVE_PASS',
        'HPR_COMBINED_ANIMATION_CUSTOMER_WARNING_NATIVE_PASS',
        'original_healthy_and_warning_first_use_examples_validated=PASS',
        'equal_count_but_different_FBX_path_must_fail_closed',
        'combined_warning_when_real_customer_custom_clips_omit_source_take',
        'combined_buyer_sees_NO_custom_models_not_fake_clean',
        'private_customer_source_FBX_untouched',
        'JSON_output_create_only_no_overwrite'):
        assert key in test
    assert '2022.3.22f1' in runner and '6000.6.8f1' in runner
    assert 'buyer-import-exact-archive' in runner
    assert 'author-real-customer-warning' in runner
    assert 'buyer-real-customer-warning' in runner
    assert 'strict-original-first-party-package.json' in runner
    assert 'HPR_COMBINED_ANIMATION_NATIVE_EXPORT_PASS' in (
        BUNDLE/'qa/HprCombinedAnimationExporter.cs').read_text()
    assert not list(SOURCE.rglob('HprCombinedAnimationNativeQa.cs'))


def _synthetic_original_archive(path, bad_source=False, extra=False):
    """Structural fixture, NOT an installed/native Unity export."""
    mod = module()
    with tarfile.open(path,'w:gz') as tar:
        import re
        for root in mod.SOURCES.values():
            for asset in [root,*root.rglob('*')]:
                if asset.is_file() and asset.name.endswith('.meta'):
                    continue
                if not (asset.is_dir() or asset.is_file()):
                    continue
                meta = Path(str(asset)+'.meta')
                guid = re.search(r'^guid: ([a-f0-9]{32})$',meta.read_text(),re.M).group(1)
                relative = 'Assets/' + str(asset.relative_to(root.parent))
                content = [('pathname',relative.encode()),('asset.meta',meta.read_bytes())]
                if asset.is_file():
                    payload = asset.read_bytes()
                    if bad_source and asset.name == 'HprAnimationImportPreflight.cs':
                        payload += b'\n// source tampered after export\n'
                    content.append(('asset',payload))
                for kind,raw in content:
                    info = tarfile.TarInfo(guid+'/'+kind)
                    info.size = len(raw)
                    tar.addfile(info,io.BytesIO(raw))
        if extra:
            raw = b'Assets/Foreign/Extra.cs'
            info = tarfile.TarInfo('f'*32+'/pathname')
            info.size=len(raw);tar.addfile(info,io.BytesIO(raw))


def test_archive_inspection_rejects_rewritten_sources_and_foreign_payloads(tmp_path):
    mod = module()
    good = tmp_path/'original-preview.unitypackage'
    _synthetic_original_archive(good)
    valid = mod.verify(good)
    assert valid['result']=='PASS' and valid['actual_original_unity_asset_paths']==27
    bad = tmp_path/'different-source.unitypackage'
    _synthetic_original_archive(bad,bad_source=True)
    import pytest
    with pytest.raises(ValueError): mod.verify(bad)
    foreign = tmp_path/'foreign-file.unitypackage'
    _synthetic_original_archive(foreign,extra=True)
    with pytest.raises(ValueError): mod.verify(foreign)
