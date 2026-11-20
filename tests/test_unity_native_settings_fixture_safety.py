from pathlib import Path
import importlib.util
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "unity/tools/release/gameplay_suite/qa/ProjectSettingsPreflight/run_native_settings_fixture.py"
spec = importlib.util.spec_from_file_location("fixture", SOURCE)
qa = importlib.util.module_from_spec(spec); spec.loader.exec_module(qa)


class NativeFixtureOutputSafety(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.runtime = self.root / "runtime"; self.runtime.mkdir()
        self.source = self.runtime / "original-project"; self.source.mkdir()
        self.patcher = patch.object(qa, "RUNTIME_ROOT", self.runtime); self.patcher.start(); self.addCleanup(self.patcher.stop)

    def test_fresh_separate_output_is_valid_without_writes(self):
        target = self.runtime / "new-output"
        qa.validate_output_location(target, self.source)
        self.assertFalse(target.exists())
        self.assertEqual([], list(self.source.iterdir()))

    def test_output_inside_original_template_is_refused(self):
        target = self.source / "new-output"
        with self.assertRaisesRegex(ValueError, "original"):
            qa.validate_output_location(target, self.source)
        self.assertFalse(target.exists())

    def test_existing_output_and_symlink_escape_are_refused(self):
        existing = self.runtime / "used"; existing.mkdir()
        with self.assertRaises(FileExistsError): qa.validate_output_location(existing, self.source)
        outside = self.root / "outside"; outside.mkdir()
        alias = self.runtime / "alias"; alias.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError): qa.validate_output_location(alias / "fresh", self.source)
        self.assertEqual([], list(outside.iterdir()))

    def test_parent_alias_into_original_template_is_refused(self):
        alias = self.runtime / "alias"; alias.symlink_to(self.source, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "original"):
            qa.validate_output_location(alias / "fresh", self.source)
