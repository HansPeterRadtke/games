"""Read-only source and independent Unity archive policy for HPR boundary product."""
import io
import importlib.util
from pathlib import Path
import re
import tarfile

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = ROOT/'unity/tools/release/package_boundary_audit'
VENDOR = PRODUCT/'Assets/HPRPackageBoundary'
CS = VENDOR/'Editor/HprPackageBoundaryWindow.cs'


def _verifier():
    path = PRODUCT/'qa/verify_archive.py'
    spec = importlib.util.spec_from_file_location('hpr_boundary_verify', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_scanner_has_explicit_limits_no_automatic_repair_or_account_access():
    src = CS.read_text()
    for must in ('Tools/HPR/Package Boundary Inspector', 'AssetDatabase.GetDependencies(asset, false)',
                 'DefaultMaxAssets = 10000', 'DefaultMaxFindings = 1500',
                 'AssetDatabase.IsValidFolder', 'INCOMPLETE', 'THIRD_PARTY_PACKAGE',
                 'REVIEW_UNITY_PACKAGE_DECLARATIONS', 'REVIEW_EXTERNAL_DEPENDENCIES',
                 'FileMode.CreateNew', 'EditorUtility.SaveFilePanel',
                 'DisplayCancelableProgressBar', 'EditorApplication.delayCall',
                 'HprBoundaryUpgradeReview.Compare(previous, last)'):
        assert must in src
    for forbidden in ('AssetDatabase.DeleteAsset(', 'AssetDatabase.MoveAsset(',
                      'AssetDatabase.SaveAssets(', 'AssetDatabase.ImportPackage(',
                      'PlayerSettings.', 'EditorUserBuildSettings.', 'UnityWebRequest',
                      'System.Diagnostics.Process', 'FileMode.Create,'):
        assert forbidden not in src


def test_vendor_only_one_root_and_stable_unique_guids():
    metadata = [VENDOR.parent/'HPRPackageBoundary.meta',
                VENDOR/'Editor.meta', VENDOR/'README.md.meta', VENDOR/'LICENSE.md.meta',
                VENDOR/'Editor/HprPackageBoundaryWindow.cs.meta',
                VENDOR/'Editor/HprBoundaryUpgradeReview.cs.meta']
    guids = []
    for path in metadata:
        assert path.is_file()
        m = re.search(r'(?m)^guid: ([0-9a-f]{32})$', path.read_text())
        assert m, path
        guids.append(m.group(1))
    assert len(set(guids)) == 6
    assert not list(PRODUCT.rglob('*.dll'))
    assert 'read-only' in (VENDOR/'README.md').read_text().lower()


def _create_synthetic_tar(path, *, tamper=False, extra=False):
    """Policy unit fixture; NOT a native Unity export acceptance test."""
    v = _verifier()
    with tarfile.open(path, 'w:gz') as tar:
        for relative in sorted(v.ALLOWED):
            local = PRODUCT/'Assets'/Path(relative).relative_to('Assets')
            meta = Path(str(local)+'.meta')
            guid = re.search(r'(?m)^guid: ([0-9a-f]{32})$', meta.read_text()).group(1)
            for name, blob in (
                ('pathname',relative.encode()),
                ('asset.meta',meta.read_bytes()),
                ('asset',local.read_bytes() + (b'UNAUTHORIZED' if tamper and local.suffix=='.cs' else b''))
                    if local.is_file() else ('',b''),
            ):
                if not name:continue
                item = tarfile.TarInfo(guid+'/'+name)
                item.size = len(blob)
                tar.addfile(item,io.BytesIO(blob))
        if extra:
            blob = b'Assets/Foreign/Extra.cs'
            t = tarfile.TarInfo('a'*32+'/pathname'); t.size=len(blob);tar.addfile(t,io.BytesIO(blob))


def test_archive_scope_and_content_rejects_manipulation(tmp_path):
    v = _verifier()
    good = tmp_path/'good.unitypackage'
    _create_synthetic_tar(good)
    assert v.inspect(good)['assets'] == 6
    evil = tmp_path/'modified.unitypackage'
    _create_synthetic_tar(evil, tamper=True)
    try:v.inspect(evil)
    except ValueError as err: assert 'source' in str(err).lower()
    else: assert False, 'Tampered product was accepted'
    foreign = tmp_path/'foreign.unitypackage'
    _create_synthetic_tar(foreign, extra=True)
    try:v.inspect(foreign)
    except ValueError as err: assert 'unexpected' in str(err).lower()
    else: assert False, 'Unexpected files were accepted'


def test_real_unity_qa_has_two_external_cases_and_fail_closed():
    fixture=(PRODUCT/'qa/HprPackageBoundaryNativeQa.cs').read_text()
    assert 'PrefabUtility.SaveAsPrefabAsset' in fixture
    for fragment in ('OutsideOne', 'OutsideTwo', 'UsesInside', 'ExportNewJson',
                     'findingsCapped.incomplete', 'capped.incomplete',
                     'NO_RESOLVED_EXTERNAL_DEPENDENCIES_FOUND', 'HPR_BOUNDARY_NATIVE_QA_PASS'):
        assert fragment in fixture
    exporter=(PRODUCT/'qa/HprPackageBoundaryExporter.cs').read_text()
    assert 'ExportPackageOptions.Recurse' in exporter
    assert 'File.Exists(output)' in exporter
    assert 'HPR_BOUNDARY_RELEASE_EXPORT_PASS' in exporter


def test_upgrade_snapshot_contract_and_native_coverage():
    source = (VENDOR/'Editor/HprBoundaryUpgradeReview.cs').read_text()
    for piece in ('GUID_REPLACED_AT_PATH', 'ASSET_REMOVED', 'PATH_MOVED_WITH_SAME_GUID',
                  'ASSET_ADDED', 'REVIEW_SERIALIZED_IDENTITY_BREAKAGE', 'INCOMPLETE',
                  'report.schemaVersion != 1', 'FileMode.CreateNew', 'oldByPath', 'nowByGuid'):
        assert piece in source
    scanner = CS.read_text()
    for piece in ('public int schemaVersion;', 'BoundaryIdentity[] identities;',
                  'AssetDatabase.AssetPathToGUID(asset)', 'cancelRequested(index, scanned)',
                  'result.incomplete = true'):
        assert piece in scanner
