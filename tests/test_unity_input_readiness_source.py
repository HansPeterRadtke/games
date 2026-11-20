"""Source and packaging safety invariants for the separate Unity editor product."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT/'unity/tools/release/input_readiness_audit'
SOURCE = PACK/'Assets/HPRInputReadiness/Editor/HprInputReadinessAudit.cs'
QA = PACK/'qa/HprInputReadinessQa.cs'


class InputAuditSourceSafety(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text()

    def test_no_mutating_asset_or_project_api(self):
        for forbidden in ('AssetDatabase.ImportPackage(', 'AssetDatabase.DeleteAsset(',
                          'AssetDatabase.MoveAsset(', 'AssetDatabase.SaveAssets(',
                          'PlayerSettings.activeInputHandler =', 'File.Delete(',
                          'Directory.Delete(', 'File.WriteAllText(', 'File.WriteAllBytes('):
            self.assertNotIn(forbidden, self.source, forbidden)
        self.assertIn('FileMode.CreateNew', self.source)
        self.assertIn('EditorUtility.SaveFilePanel', self.source)
        self.assertIn('EditorApplication.delayCall', self.source)
        self.assertIn('AssetDatabase.OpenAsset(script, f.line)', self.source)
        # BuildProfile is a Unity 6 API. Unity 2022 LTS must compile without that namespace.
        self.assertIn('#if UNITY_6000_0_OR_NEWER\nusing UnityEditor.Build.Profile;', self.source)
        self.assertIn('report.activeBuildProfile = "Not available in this Unity version";', self.source)

    def test_explicit_limits_and_incomplete_status(self):
        for marker in ('MaximumScripts', 'MaximumScriptBytes', 'MaximumFindings',
                       'findingsTruncated', 'scriptScanTruncated', '"INCOMPLETE"',
                       'FileAttributes.ReparsePoint'):
            self.assertIn(marker, self.source)

    def test_supported_backends_and_guards_are_in_native_source(self):
        for marker in ('Legacy only', 'New only', 'Both', 'Unknown',
                       'ENABLE_INPUT_SYSTEM', 'ENABLE_LEGACY_INPUT_MANAGER',
                       'UNITY_EDITOR', 'LEGACY_API_IN_NEW_ONLY',
                       'NEW_API_IN_LEGACY_ONLY', 'UNKNOWN_INPUT_MODE',
                       'ACTIVE_BUILD_PROFILE_OVERRIDE', 'BuildProfile.GetActiveBuildProfile',
                       'MISSING_INPUT_PACKAGE'):
            self.assertIn(marker, self.source)
        for marker in ('mode0=PASS', 'mode1=PASS', 'mode2=PASS'):
            # Native QA appends the mode result dynamically instead of hardcoding fake receipts.
            self.assertNotIn(marker, QA.read_text())

    def test_package_guid_metadata_complete_and_unique(self):
        base = PACK/'Assets'
        items = [base/'HPRInputReadiness', base/'HPRInputReadiness/Editor',
                 base/'HPRInputReadiness/README.md',
                 base/'HPRInputReadiness/Editor/HprInputReadinessAudit.cs']
        guids = []
        for asset in items:
            meta = Path(str(asset)+'.meta')
            self.assertTrue(meta.is_file(), asset)
            match = re.search(r'(?m)^guid: ([0-9a-f]{32})$', meta.read_text())
            self.assertIsNotNone(match, meta)
            guids.append(match.group(1))
        self.assertEqual(len(set(guids)), 4)

    def test_reusable_product_remains_editor_only(self):
        self.assertTrue(self.source.startswith('// Original'))
        self.assertIn('#if UNITY_EDITOR', self.source)
        self.assertIn('MenuItem("Tools/HPR/Input Compatibility Audit")', self.source)
        self.assertFalse(any((PACK/'Assets/HPRInputReadiness').glob('*.dll')))


if __name__ == '__main__':
    unittest.main()
