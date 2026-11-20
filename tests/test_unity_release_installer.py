"""Buyer installer identity, content and reuse of staging projects from older releases."""
import runpy
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "unity/tools/release/gameplay_suite"
INSTALLER = Path("HPRGameplaySuite/Editor/HprSelectedAbilityInstaller.cs")
META = INSTALLER.with_suffix(".cs.meta")
GUID = "72050056e79458319827a82105e509c8"


class InstallerStagingTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        project = Path(directory.name)
        self.assets = project / "Assets"
        self.stage = runpy.run_path(str(SOURCE / "build_gameplay_suite.py"))["stage_authored_buyer_assets"]
        self.stage.__globals__["PROJECT"] = project
        self.hashes = self.stage(reuse_project=False)
        self.script = self.assets / INSTALLER
        self.meta = self.assets / META

    def test_fresh_staging_and_pre_installer_upgrade_are_identical(self):
        self.script.unlink()
        self.meta.unlink()
        self.assertEqual(self.hashes, self.stage(reuse_project=True))
        self.assertEqual(self.script.read_bytes(), (SOURCE / "buyer_source_assets" / INSTALLER).read_bytes())
        self.assertIn(f"guid: {GUID}", self.meta.read_text())
        self.assertEqual(self.hashes, self.stage(reuse_project=True))

    def test_orphan_meta_is_preserved(self):
        self.script.unlink()
        original = self.meta.read_bytes()
        with self.assertRaisesRegex(RuntimeError, "missing"):
            self.stage(reuse_project=True)
        self.assertFalse(self.script.exists())
        self.assertEqual(original, self.meta.read_bytes())

    def test_orphan_script_is_preserved(self):
        self.meta.unlink()
        original = self.script.read_bytes()
        with self.assertRaisesRegex(RuntimeError, "missing"):
            self.stage(reuse_project=True)
        self.assertEqual(original, self.script.read_bytes())
        self.assertFalse(self.meta.exists())

    def test_conflicting_guid_or_script_is_preserved(self):
        original = self.meta.read_bytes()
        self.meta.write_text("guid: " + "a" * 32)
        with self.assertRaisesRegex(RuntimeError, "GUID differs"):
            self.stage(reuse_project=True)
        self.assertEqual(self.meta.read_text(), "guid: " + "a" * 32)
        self.meta.write_bytes(original)
        self.script.write_text("// Local staging edit")
        with self.assertRaisesRegex(RuntimeError, "differs from source"):
            self.stage(reuse_project=True)
        self.assertEqual(self.script.read_text(), "// Local staging edit")

    def test_missing_pair_is_not_added_before_all_existing_assets_validate(self):
        self.script.unlink()
        self.meta.unlink()
        (self.assets / "HPRGameplaySuite/Samples/FieldMedkit.asset").write_text("Buyer edit")
        with self.assertRaisesRegex(RuntimeError, "differs from source"):
            self.stage(reuse_project=True)
        self.assertFalse(self.script.exists())
        self.assertFalse(self.meta.exists())

    def test_dangling_symlink_is_not_a_missing_installer(self):
        self.script.unlink()
        self.meta.unlink()
        self.script.symlink_to(self.assets.parent / "foreign-script")
        with self.assertRaisesRegex(RuntimeError, "Symlink"):
            self.stage(reuse_project=True)
        self.assertTrue(self.script.is_symlink())
        self.assertFalse(self.script.exists())
        self.assertFalse(self.meta.exists())


class ExportedEditorSourceTests(unittest.TestCase):
    def setUp(self):
        module = runpy.run_path(str(SOURCE / "validate_release.py"))
        self.check = module["validate_editor_sources"]
        self.code = {path: source.read_bytes() for path, source in module["EDITOR_SOURCES"].items()}
        self.key = "Assets/" + INSTALLER.as_posix()

    def test_current_editor_sources_include_the_installer(self):
        self.assertIn(self.key, self.code)
        self.check(self.code)

    def test_omitted_or_extra_editor_script_fails(self):
        with self.assertRaisesRegex(ValueError, "missing buyer Editor scripts"):
            self.check({key: value for key, value in self.code.items() if key != self.key})
        with self.assertRaisesRegex(ValueError, "Unexpected"):
            self.check({**self.code, self.key + ".cs": b"other implementation"})

    def test_archived_prototype_with_right_guid_and_wrong_code_fails(self):
        self.code[self.key] = (SOURCE / "qa/HprSelectedAbilityInstaller.cs").read_bytes()
        with self.assertRaisesRegex(ValueError, "differs from release source"):
            self.check(self.code)
