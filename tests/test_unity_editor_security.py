"""Provider-free policy tests for October 2026 Unity Editor security patches."""
from pathlib import Path
import importlib.util
import unittest
import sys
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
QA = ROOT / 'unity/tools/release/gameplay_suite/qa/editor_security.py'
spec = importlib.util.spec_from_file_location('unity_editor_security', QA)
security = importlib.util.module_from_spec(spec)
spec.loader.exec_module(security)


class UnitySecurityPatchTests(unittest.TestCase):
    def test_documented_patched_streams(self):
        for version in ('6000.0.85f2', '6000.3.27f2', '6000.6.8f1',
                        '6000.6.9f1', '6000.7.0b7', '7000.0.0a16'):
            self.assertTrue(security.version_is_patched(version), version)

    def test_vulnerable_or_unverified_versions_rejected(self):
        for version in ('6000.0.85f1', '6000.3.27f1', '6000.6.7f1',
                        '6000.7.0b6', '7000.0.0a15',
                        '6000.4.0f1', '6000.5.11f1',
                        '6000.8.0f1', 'invalid', ''):
            self.assertFalse(security.version_is_patched(version), version)

    def test_binary_version_check_accepts_only_documented_patch(self):
        file = Path(sys.executable)
        with mock.patch.object(security.subprocess, 'run',
                               return_value=mock.Mock(returncode=0,
                                                      stdout='6000.6.8f1\n',
                                                      stderr='')) as run:
            self.assertEqual(security.require_patched_editor(file), '6000.6.8f1')
            run.assert_called_once()

    def test_binary_check_rejects_old_or_unknown(self):
        file = Path(sys.executable)
        with mock.patch.object(security.subprocess, 'run',
                               return_value=mock.Mock(returncode=0,
                                                      stdout='6000.6.7f1\n',
                                                      stderr='')):
            with self.assertRaisesRegex(RuntimeError, 'not verified'):
                security.require_patched_editor(file)

    def test_builder_checks_security_before_creating_release(self):
        text = (ROOT / 'unity/tools/release/gameplay_suite/build_gameplay_suite.py').read_text()
        self.assertLess(text.index('require_patched_editor(UNITY)'),
                        text.index('RELEASE.mkdir(parents=True'))
        self.assertIn('HPR_UNPATCHED_EDITOR_INTERNAL_QA', text)

    def test_all_release_tools_default_to_patched_editor(self):
        base = ROOT / 'unity/tools/release/gameplay_suite'
        for file in ('build_gameplay_suite.py', 'validate_cleanroom.sh',
                     'validate_playmode.sh', 'capture_media.sh'):
            text = (base / file).read_text()
            self.assertIn('/6000.6.8f1/Editor/Unity', text, file)
            self.assertNotIn('/6000.4.0f1/Editor/Unity', text, file)
        builder = (base / 'build_gameplay_suite.py').read_text()
        self.assertIn('require_patched_editor(UNITY)', builder)


if __name__ == '__main__':
    unittest.main()
