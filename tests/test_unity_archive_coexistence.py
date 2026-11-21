"""Independent source/fixture contracts for two-package coexistence preflight.

This is not a substitute for actual installed Unity native author/buyer QA.
The real moved-path archive fixture is generated via Unity's ExportPackage.
"""
from pathlib import Path
import tarfile
import re

ROOT=Path(__file__).resolve().parents[1]
PKG=ROOT/'unity/tools/release/unitypackage_archive_preflight'
VENDOR=PKG/'Assets/HPRArchivePreflight'
SAMPLE=VENDOR/'Samples'
COMPARE=VENDOR/'Editor/HprArchiveCoexistence.cs'
UI=VENDOR/'Editor/HprUnitypackageArchiveWindow.cs'


def _assets(which):
    out={}
    with tarfile.open(SAMPLE/f'HprExample-{which}.unitypackage','r:gz') as z:
        for m in z:
            name=m.name.removeprefix('./')
            if not m.isfile() or not name.endswith('/pathname'): continue
            guid=name.split('/')[0]
            assert re.fullmatch('[0-9a-f]{32}',guid)
            path=z.extractfile(m).read().decode('utf-8').strip()
            assert path not in out
            out[path]=guid
    return out


def test_real_unity_exported_training_assets_demonstrate_independent_path_collision():
    baseline=_assets('baseline');addition=_assets('additions_only');replacement=_assets('changed_guid')
    assert len(baseline)==3 and len(addition)==4 and len(replacement)==3
    assert all(addition[p]==guid for p,guid in baseline.items())
    assert set(baseline)==set(replacement)
    assert sum(replacement[p]!=guid for p,guid in baseline.items())==1
    # Source data proves one overlapping path with differing GUIDs, not a Unity bug.
    assert sum(p in replacement and replacement[p]!=guid for p,guid in baseline.items())==1


def test_comparison_only_counts_distinct_collision_classes_and_fails_closed():
    s=COMPARE.read_text()
    for token in ('GUID_REUSED_AT_DIFFERENT_PATH', 'PATH_REUSED_WITH_DIFFERENT_GUID',
                  'SHARED_GUID_PATH_DIFFERENT_BYTES', 'identicalSharedAssets',
                  'guidCollisions++', 'pathCollisions++', 'overwriteRisks++',
                  'caseOnlyPathCollisions', 'CASE_ONLY_ASSET_PATH_COLLISION',
                  'NO_OVERLAP_CONFLICTS_IN_CHECKED_ARCHIVES',
                  'REVIEW_INDEPENDENT_PACKAGE_COLLISIONS',
                  'result.incomplete = true', 'FileMode.CreateNew'):
        assert token in s
    for token in ('AssetDatabase.ImportPackage(', 'AssetDatabase.DeleteAsset(',
                  'AssetDatabase.MoveAsset(', 'UnityWebRequest', 'File.Delete(',
                  'FileMode.Create,'):
        assert token not in s
    assert 'GuidRegex.IsMatch' in s and 'report.pathsChecked != report.assets.Length' in s
    assert 'byPath.Add' in s and 'byGuid.Add' in s
    assert 'StringComparer.OrdinalIgnoreCase' in s
    assert 'secondByCaseFoldedPath' in s
    assert 'foreach (var a in first.assets.OrderBy' in s


def test_gui_keeps_upgrade_and_coexistence_distinct_instead_of_relabeling():
    s=UI.read_text()
    for token in ('Review an UPGRADE (old replaced by new)',
                  'Check COEXISTENCE (both packages together)',
                  'BeginScan(false)', 'BeginScan(true)',
                  'Try coexistence: competing packages use the same path',
                  'HprArchiveCoexistence.Compare(previous, updated)',
                  'HprUnitypackageArchiveReader.Compare(previous, updated)',
                  'DrawCoexistence()', 'Export coexistence review to a NEW JSON file'):
        assert token in s
    for token in ('AssetDatabase.ImportPackage(', 'AssetDatabase.DeleteAsset(',
                  'File.WriteAllBytes(', 'WWW(', 'UnityWebRequest'):
        assert token not in s


def test_private_native_probe_requires_real_unity_path_move_source_and_fresh_customer():
    export=(PKG/'qa/HprCoexistenceMovedRealExporter.cs').read_text()
    runner=(PKG/'qa/run_original_moved_guid_fixture.sh').read_text()
    native=(PKG/'qa/HprArchivePreflightNativeQa.cs').read_text()
    for token in ('AssetDatabase.ExportPackage', 'AssetDatabase.AssetPathToGUID(newPath)',
                  'HPR_REAL_MOVED_GUID_EXPORTED', 'File.Exists(target)'):
        assert token in export
    case_export=(PKG/'qa/HprCoexistenceCaseOnlyRealExporter.cs').read_text()
    case_script=(PKG/'qa/run_original_case_only_fixture.sh').read_text()
    assert 'AssetDatabase.ExportPackage' in case_export
    assert 'HPR_REAL_CASE_ONLY_PATH_EXPORTED' in case_export
    assert 'verified-real-case-only-source.json' in case_script
    assert 'case-only-path-distinct-guid.unitypackage' in case_script
    for token in ('real-moved-guid-fixture', 'Refusing duplicate',
                  'moved-path-same-guid.unitypackage', 'verified-original-move.json'):
        assert token in runner
    for token in ('genuine_renamed_path_reusing_guid_is_collision_if_both_installed',
                  'same_renamed_guid_can_be_upgrade_migration_not_safe_coexistence',
                  'actual_Unity_case_only_distinct_guid_collision_warns_and_input_unchanged',
                  'case_only_duplicate_paths_in_serialized_caller_snapshot_fail_closed',
                  'independent_packages_different_bytes_warn_overwrite',
                  'independent_collision_report_export_create_only',
                  'actual-independent-coexistence-preview.json'):
        assert token in native
