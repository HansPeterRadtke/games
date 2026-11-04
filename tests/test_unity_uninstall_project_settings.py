"""Dependency-only ProjectSettings fixtures must not be silently skipped."""
from pathlib import Path
import importlib.util
import io
import json
import tarfile
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "unity/tools/release/gameplay_suite/qa/unity_uninstall_preflight.py"
spec = importlib.util.spec_from_file_location("preflight", SOURCE)
qa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa)
GUID = "4da0644b7fd1cbd7b9f70bd2b208b822"


class ProjectSettingsDependencies(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / "project"
        (self.project / "Assets").mkdir(parents=True)
        self.settings = self.project / "ProjectSettings"
        self.settings.mkdir()
        self.archive = self.root / "candidate.unitypackage"
        with tarfile.open(self.archive, "w:gz") as tar:
            raw = b"Assets/HPRGameplaySuite/Demo/GameplaySuiteShowcase.unity"
            entry = tarfile.TarInfo(GUID + "/pathname")
            entry.size = len(raw)
            tar.addfile(entry, io.BytesIO(raw))

    def test_settings_only_guid_dependencies_detected_without_mutation(self):
        for filename, field in (("EditorBuildSettings.asset", "guid"), ("GraphicsSettings.asset", "m_CustomRenderPipeline"), ("QualitySettings.asset", "customRenderPipeline")):
            with self.subTest(filename=filename):
                path = self.settings / filename
                raw = ("%YAML 1.1\n" + field + ": {fileID: 11400000, guid: " + GUID + ", type: 2}\n").encode()
                path.write_bytes(raw)
                result = qa.inspect(self.project, self.archive)
                self.assertEqual("customer_dependencies_found", result["classification"])
                self.assertTrue(any(row["path"] == "ProjectSettings/" + filename and row["guid"] == GUID and row["kind"] == "project_settings_vendor_guid" for row in result["dependencies"]))
                self.assertFalse(result["deletion_permitted"])
                self.assertEqual(raw, path.read_bytes())
                path.unlink()

    def test_settings_root_and_child_symlink_are_refused(self):
        external = self.root / "outside"; external.mkdir()
        self.settings.rmdir(); self.settings.symlink_to(external, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            qa.inspect(self.project, self.archive)
        self.settings.unlink(); self.settings.mkdir()
        outside = external / "config.asset"; outside.write_text("guid: " + GUID)
        (self.settings / "Alias.asset").symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "symlink"):
            qa.inspect(self.project, self.archive)

    def test_oversized_binary_and_invalid_encoding_settings_require_review(self):
        path = self.settings / "GraphicsSettings.asset"
        for raw, limit in ((b"x" * 200, 100), (b"binary\0data", 100), (b"\xff\xfe", 100)):
            with self.subTest(raw=raw[:10]):
                path.write_bytes(raw)
                result = qa.inspect(self.project, self.archive, max_file_bytes=limit)
                self.assertEqual("unknown_project_content_requires_review", result["classification"])
                self.assertTrue(any(row["path"] == "ProjectSettings/GraphicsSettings.asset" for row in result["unknowns"]))

    def test_settings_share_the_single_traversal_budget(self):
        for number in range(5):
            (self.settings / (str(number) + ".asset")).write_text("ordinary: setting")
        result = qa.inspect(self.project, self.archive, max_scanned_paths=2)
        self.assertEqual("unknown_project_content_requires_review", result["classification"])
        self.assertTrue(any("traversal limit" in row["reason"] for row in result["unknowns"]))
        self.assertEqual(3, result["examined_asset_paths"])

    def test_absent_or_unrelated_settings_do_not_invent_dependencies(self):
        (self.settings / "EditorSettings.asset").write_text("m_EnterPlayModeOptions: 1")
        self.assertEqual("no_direct_reference_detected", qa.inspect(self.project, self.archive)["classification"])
        (self.settings / "EditorSettings.asset").unlink(); self.settings.rmdir()
        self.assertEqual("no_direct_reference_detected", qa.inspect(self.project, self.archive)["classification"])

    def test_non_directory_settings_root_is_refused(self):
        self.settings.rmdir(); self.settings.write_text("not a directory")
        with self.assertRaises(ValueError): qa.inspect(self.project, self.archive)
