"""Source and GUID invariants for the original standalone Animator contract tool."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'unity/tools/release/animator_contract_audit'
SRC = BASE / 'Assets/HPRAnimatorContract/Editor/HprAnimatorContractAudit.cs'


def test_editor_only_read_only_no_automatic_fixes():
    s = SRC.read_text()
    for forbidden in ('AssetDatabase.DeleteAsset(', 'AssetDatabase.ImportPackage(',
                      'AssetDatabase.SaveAssets(', 'File.WriteAllText(', 'File.Delete(',
                      'Undo.DestroyObjectImmediate(', 'AnimatorController.CreateAnimatorControllerAtPath('):
        assert forbidden not in s
    assert '#if UNITY_EDITOR' in s
    assert 'MenuItem("Tools/HPR/Animator Contract Audit")' in s
    assert 'AssetDatabase.FindAssets(' in s


def test_reference_checks_present():
    s = SRC.read_text()
    for marker in ('MISSING_PARAMETER', 'PARAMETER_TYPE_MISMATCH', 'DUPLICATE_PARAMETER',
                   'EMPTY_PARAMETER', 'INCOMPLETE', 'ScanController', 'anyStateTransitions',
                   'entryTransitions', 'GetStateMachineTransitions',
                   'STATE_PARAMETER_TYPE_MISMATCH', 'ValidateStateValue'):
        assert marker in s


def test_asset_guids_stable_unique():
    p = BASE / 'Assets/HPRAnimatorContract'
    paths = [p, p/'Editor', p/'README.md', p/'Editor/HprAnimatorContractAudit.cs']
    found = []
    for a in paths:
        meta = Path(str(a)+'.meta')
        assert meta.is_file(), meta
        m = re.search(r'(?m)^guid: ([0-9a-f]{32})$', meta.read_text())
        assert m
        found.append(m.group(1))
    assert len(set(found)) == len(paths)
