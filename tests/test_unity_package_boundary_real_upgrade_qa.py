"""Non-destructive native old-to-new buyer package acceptance contract.

This source policy test is NOT evidence that the native Unity steps passed.
The real independent Editor receipts belong to private buyer workspaces.
"""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/'unity/tools/release/package_boundary_audit/qa'


def test_real_upgrade_has_separate_old_and_new_private_qa_files():
    before=(QA/'HprBoundaryRealUpgradeBeforeQa.cs').read_text()
    after=(QA/'HprBoundaryRealUpgradeAfterQa.cs').read_text()
    for text in ('LoadMainAssetAtPath', 'AssetDatabase.CreateAsset(',
                 'buyer_owned_note', 'BuyerReferences.asset',
                 'HprRealUpgradeBuyerReference', 'HPR_REAL_UPGRADE_BEFORE_NATIVE_PASS',
                 'FileMode.CreateNew', 'AssetDatabase.AssetPathToGUID',
                 'fresh_runtime_customer_script_and_no_uncertain_replay'):
        if text == 'buyer_owned_note':
            assert 'buyer-owned-note.txt' in before
        else:
            assert text in before
    for text in ('HprBoundaryUpgradeReview.Compare',
                 'serialized_customer_asset_reference_still_resolves_after_real_upgrade',
                 'all_customer_file_sha256_and_inventory_unchanged',
                 'legacy_vendor_path_guid_identity_not_preserved',
                 'ADDITIONS_ONLY', 'addedAssets == 1',
                 'replacedGuids == 0', 'removedAssets == 0',
                 'HPR_REAL_BUYER_UPGRADE_NATIVE_PASS', 'FileMode.CreateNew'):
        assert text in after
    runtime=(QA/'HprRealUpgradeBuyerReference.cs').read_text()
    assert 'public sealed class HprRealUpgradeBuyerReference : ScriptableObject' in runtime
    assert 'm_Script' not in runtime  # Unity must serialize actual MonoScript itself.
    assert 'HprRealUpgradeBuyerReference : ScriptableObject' not in before
    assert 'File.Delete(' not in before+after
    assert 'AssetDatabase.DeleteAsset(' not in before+after
    assert 'AssetDatabase.MoveAsset(' not in before+after


def test_runner_requires_old_then_new_exact_archives_and_never_replays():
    script=(QA/'run_real_buyer_upgrade.sh').read_text()
    assert 'Refusing duplicate or uncertain upgrade test' in script
    assert 'original-v1-import' in script
    assert 'original-v1-buyer-baseline' in script
    assert 'existing-buyer-upgrade-to-v2' in script
    assert 'upgraded-v2-buyer-check' in script
    assert 'HPR_REAL_PACKAGE_CUSTOMER_UPGRADE_RESULT=PASS' in script
    assert 'HprRealUpgradeBuyerReference.cs' in script
    assert 'Assets/HprBoundaryUpgradeCustomerFixture' in script
    assert script.index('original-v1-import') < script.index('existing-buyer-upgrade-to-v2')
    assert 'git reset' not in script and 'rm -rf' not in script
    assert 'AssetStore' not in script
    assert re.search(r'timeout [0-9]+ "\$unity" -batchmode', script)


def test_buyer_private_qa_never_in_vendor_archive_scope():
    contents=(QA/'verify_archive.py').read_text()
    assert 'HprBoundaryRealUpgradeBeforeQa' not in contents
    assert 'HprBoundaryRealUpgradeAfterQa' not in contents
    assert (ROOT/'unity/tools/release/package_boundary_audit/Assets/HPRPackageBoundary/Editor/HprBoundaryUpgradeReview.cs').is_file()


def test_independent_verifier_recomputes_archive_and_customer_evidence():
    source=(QA/'verify_native_receipts.py').read_text()
    for marker in ('archive_guids', 'before-native-vendor-identity.json',
                   'actual-native-upgrade-diff.json', 'sha256(',
                   'serialized_runtime_reference', 'customer_files_unchanged',
                   'HPR_REAL_BUYER_UPGRADE_NATIVE_PASS', 'ALLOWED_BASE'):
        assert marker in source
    assert 'tarfile.open' in source
    assert 'File.Delete' not in source and 'rm -rf' not in source
