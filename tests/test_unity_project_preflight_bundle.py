"""Source/UI/asset identity contract for the separate original HPR bundle."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT/'unity/tools/release/preflight_bundle'
SRC = BUNDLE/'Assets/HPRProjectPreflight/Editor/HprProjectPreflightWindow.cs'


def test_read_only_and_create_new_manual_export():
    text=SRC.read_text()
    for forbidden in ('AssetDatabase.SaveAssets(', 'AssetDatabase.DeleteAsset(',
                      'AssetDatabase.ImportPackage(', 'File.WriteAllText(',
                      'File.Delete(', 'PlayerSettings.activeInputHandler ='):
        assert forbidden not in text
    assert 'FileMode.CreateNew' in text
    assert 'EditorUtility.SaveFilePanel' in text
    assert 'Tools/HPR/Project Preflight Bundle' in text
    assert 'HprInputReadinessAudit.Analyze(project)' in text
    assert 'HprAnimatorContractAudit.ScanProject()' in text


def test_incomplete_or_uncertain_combined_report_never_looks_clean():
    text=SRC.read_text()
    for marker in ('input.result == "INCOMPLETE"', 'animator.status == "INCOMPLETE"',
                   'input.findingsTruncated', 'input.scriptScanTruncated',
                   'animator.incomplete', 'return "REVIEW_REQUIRED"', 'return "ISSUES_FOUND"'):
        assert marker in text


def test_product_meta_guid_unique_and_stable():
    base=BUNDLE/'Assets/HPRProjectPreflight'
    paths=[base,base/'Editor',base/'README.md',base/'Editor/HprProjectPreflightWindow.cs']
    guids=[]
    for path in paths:
        meta=Path(str(path)+'.meta')
        assert meta.is_file(),meta
        m=re.search(r'(?m)^guid: ([0-9a-f]{32})$',meta.read_text())
        assert m is not None
        guids.append(m.group(1))
    assert len(set(guids))==4


def test_exact_fixed_scope_exporter():
    text=(BUNDLE/'qa/HprProjectPreflightExporter.cs').read_text()
    for name in ('Assets/HPRInputReadiness','Assets/HPRAnimatorContract','Assets/HPRProjectPreflight'):
        assert name in text
    assert 'ExportPackageOptions.Recurse' in text
    assert 'HPR_PREFLIGHT_BUNDLE_OUT' in text
