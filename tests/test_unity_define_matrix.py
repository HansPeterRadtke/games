"""Offline source/packaging safety checks for the private Define Matrix add-on."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'unity/tools/release/define_matrix'
ASSETS = SRC / 'Assets/HPRDefineMatrix'

class DefineMatrixTest(unittest.TestCase):
    def test_complete_stable_meta_tree(self):
        guids = set()
        for file in [ASSETS, *ASSETS.rglob('*')]:
            if file.name.endswith('.meta'):
                continue
            meta = Path(str(file) + '.meta')
            self.assertTrue(meta.is_file(), str(meta))
            found = re.search(r'(?m)^guid: ([0-9a-f]{32})$', meta.read_text())
            self.assertIsNotNone(found, str(meta))
            self.assertNotIn(found.group(1), guids)
            guids.add(found.group(1))
        self.assertEqual(len(guids), 6)

    def test_editor_only_no_buyer_qa(self):
        source = (ASSETS / 'Editor/HprDefineMatrix.cs').read_text()
        self.assertIn('#if UNITY_EDITOR', source)
        self.assertIn('[MenuItem("Tools/HPR/Define Matrix")]', source)
        self.assertIn('BuildProfile', source)
        self.assertIn('scriptingDefines', source)
        self.assertNotIn('BindingFlags', source)
        self.assertNotIn('CreateBuildProfile(', source)
        self.assertNotIn('AssetDatabase.ImportPackage', source)
        self.assertNotIn('PlayerSettings.Set', source)
        self.assertNotIn('SetActiveBuildProfile', source)
        self.assertNotIn('HttpClient', source)

    def test_native_qa_runs_real_editor(self):
        script = (SRC / 'qa/run_native_acceptance.sh').read_text()
        for value in ('-importPackage', '-createProject', 'HprDefineMatrixQa.Run',
                      'HPR_DEFINES_NATIVE_ACCEPTANCE_PASS', 'verify_archive.py'):
            self.assertIn(value, script)
        self.assertNotIn('cp -a "$qa"', script)

    def test_csv_is_create_only_and_scans_are_read_only(self):
        script = (ASSETS / 'Editor/HprDefineMatrix.cs').read_text()
        self.assertIn('FileMode.CreateNew', script)
        self.assertIn('AssetDatabase.FindAssets("t:BuildProfile"', script)
        self.assertIn('Profile symbol list exceeds', script)
        self.assertIn('Repeated scripting define', script)
        self.assertIn('Entry " + (n + 1)', script)
        self.assertIn('Player Settings, csc.rsp', script)
        self.assertIn('Only symbols explicitly added', script)

    def test_private_qa_excluded_and_has_critical_checks(self):
        fixture = (SRC / 'qa/HprDefineMatrixQa.cs').read_text()
        for value in ('HPR_DEFINES_NATIVE_PASS', 'Native Unity did not create a profile', 'RELEASE_BUILD',
                      'DEMO_BUILD', 'AssetDatabase.CreateAsset', 'original_assets_unchanged=PASS',
                      'HprDefineMatrixWindow.OpenWindow'):
            self.assertIn(value, fixture)
        self.assertFalse((ASSETS / 'qa').exists())

if __name__ == '__main__': unittest.main()
