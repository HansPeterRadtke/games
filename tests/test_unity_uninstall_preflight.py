"""Regression safety contract for a purely read-only Unity HPR uninstall preflight."""
from pathlib import Path
import importlib.util
import io
import json
import tarfile
import tempfile
import unittest

SRC = Path(__file__).resolve().parents[1] / "unity/tools/release/gameplay_suite/qa/unity_uninstall_preflight.py"
SPEC = importlib.util.spec_from_file_location("hpr_uninstall_preflight", SRC)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

VENDOR_GUID = "b264fbccf54cda999a913fe5c4089240"
OTHER_GUID = "aabbccddeeff00112233445566778899"


class UninstallSafety(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="hpr_uninstall_preflight_")
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name) / "project"
        (self.project / "Assets/MyGame").mkdir(parents=True)
        self.vendor = self.project / "Assets/HPRGameplaySuite"
        self.vendor.mkdir()
        (self.vendor / "AbilityRunner.cs").write_text("namespace HPR {}")
        (self.project / "Assets/MyGame/Player.cs").write_text(
            "namespace Customer { class Player {} }\n")
        self.archive = Path(self.tmp.name) / "hpr.unitypackage"
        with tarfile.open(self.archive, "w:gz") as tar:
            for guid, path in ((VENDOR_GUID, "Assets/HPRGameplaySuite/AbilityRunner.cs"),
                               (OTHER_GUID, "Assets/HPRGameplaySuite/Samples/Heal.asset")):
                raw = path.encode()
                entry = tarfile.TarInfo(guid + "/pathname")
                entry.size = len(raw)
                tar.addfile(entry, io.BytesIO(raw))

    def test_actual_unitypackage_contains_vendor_root_folder_identity(self):
        with tarfile.open(self.archive, "w:gz") as tar:
            for guid, pathname in ((VENDOR_GUID, "Assets/HPRGameplaySuite/AbilityRunner.cs"),
                                   (OTHER_GUID, "Assets/HPRGameplaySuite")):
                raw = pathname.encode()
                member = tarfile.TarInfo(guid + "/pathname")
                member.size = len(raw)
                tar.addfile(member, io.BytesIO(raw))
        self.assertEqual("no_direct_reference_detected",
                         MODULE.inspect(self.project, self.archive)["classification"])

    def test_unrelated_customer_game_no_references(self):
        result = MODULE.inspect(self.project, self.archive)
        self.assertEqual("no_direct_reference_detected", result["classification"])
        self.assertEqual([], result["dependencies"])
        self.assertEqual([], result["unknowns"])
        self.assertTrue(result["read_only"])
        self.assertFalse(result["deletion_permitted"])

    def test_scene_direct_mono_script_reference_detected(self):
        scene = self.project / "Assets/MyGame/Original.unity"
        scene.write_text("%YAML 1.1\nm_Script: {fileID: 11500000, guid: " +
                         VENDOR_GUID + ", type: 3}\n")
        result = MODULE.inspect(self.project, self.archive)
        self.assertEqual("customer_dependencies_found", result["classification"])
        self.assertTrue(any(x["path"] == "Assets/MyGame/Original.unity"
                            and x["kind"] == "serialized_vendor_guid"
                            for x in result["dependencies"]))
        self.assertFalse(result["deletion_permitted"])

    def test_vendor_script_using_and_fully_qualified_name_detected(self):
        (self.project / "Assets/MyGame/Player.cs").write_text(
            "using HPR;\nnamespace Customer { HPR.AbilityRunnerComponent x; }\n")
        result = MODULE.inspect(self.project, self.archive)
        self.assertTrue(any(x["kind"] == "csharp_hpr_reference" for x in result["dependencies"]))

    def test_assembly_definition_reference_detected(self):
        (self.project / "Assets/MyGame/Customer.asmdef").write_text(json.dumps(
            {"name": "Customer.Runtime", "references": ["HPR.Abilities.Runtime"]}))
        result = MODULE.inspect(self.project, self.archive)
        self.assertTrue(any(x["kind"] == "asmdef_reference" for x in result["dependencies"]))

    def test_package_manager_hpr_dependency_detected(self):
        folder = self.project / "Packages"
        folder.mkdir()
        (folder / "manifest.json").write_text(json.dumps(
            {"dependencies": {"com.hpr.abilities": "file:./foo"}}))
        result = MODULE.inspect(self.project, self.archive)
        self.assertTrue(any(x["kind"] == "package_manifest_reference"
                            for x in result["dependencies"]))

    def test_historical_package_lock_dependency_detected(self):
        folder = self.project / "Packages"
        folder.mkdir()
        (folder / "packages-lock.json").write_text(json.dumps(
            {"dependencies": {"com.hpr.abilities": {"version": "1.0.0"}}}))
        result = MODULE.inspect(self.project, self.archive)
        self.assertTrue(any(x["kind"] == "package_lock_reference" for x in result["dependencies"]))
        self.assertEqual("customer_dependencies_found", result["classification"])

    def test_removed_vendor_root_references_still_detected(self):
        import shutil
        shutil.rmtree(self.vendor)
        (self.project / "Assets/MyGame/Original.prefab").write_text(
            "m_Script: {fileID: 11500000, guid: " + VENDOR_GUID + ", type: 3}\n")
        result = MODULE.inspect(self.project, self.archive)
        self.assertEqual("customer_dependencies_found", result["classification"])

    def test_hpr_vendor_root_does_not_self_block(self):
        (self.vendor / "Original.unity").write_text(
            "m_Script: {fileID: 11500000, guid: " + VENDOR_GUID + ", type: 3}")
        result = MODULE.inspect(self.project, self.archive)
        self.assertEqual("no_direct_reference_detected", result["classification"])

    def test_malformed_yaml_or_unknown_binary_returns_review_not_safe(self):
        (self.project / "Assets/MyGame/Surprise.prefab").write_bytes(b"\x00\x01binary")
        result = MODULE.inspect(self.project, self.archive)
        self.assertEqual("unknown_project_content_requires_review", result["classification"])
        self.assertTrue(result["unknowns"])

    def test_symlink_escape_refused(self):
        outside = Path(self.tmp.name) / "private.dat"
        outside.write_text("private")
        (self.project / "Assets/MyGame/Leak.asset").symlink_to(outside)
        with self.assertRaises(ValueError):
            MODULE.inspect(self.project, self.archive)

    def test_invalid_vendor_package_or_project_refused(self):
        with self.assertRaises(FileNotFoundError):
            MODULE.inspect(self.project, Path(self.tmp.name) / "missing.unitypackage")
        with self.assertRaises(ValueError):
            MODULE.inspect(Path(self.tmp.name) / "missing", self.archive)

    def test_unexpected_asset_file_too_large_fails_closed(self):
        # Check max bytes using a tiny artificial bound, no large allocation.
        (self.project / "Assets/MyGame/Large.dat").write_text("important vendor reference")
        result = MODULE.inspect(self.project, self.archive, max_file_bytes=5)
        self.assertEqual("unknown_project_content_requires_review", result["classification"])
        self.assertTrue(result["unknowns"])

    def test_archive_traversal_path_refused(self):
        bad = Path(self.tmp.name) / "bad.unitypackage"
        with tarfile.open(bad, "w:gz") as tar:
            raw = b"Assets/../../other.cs"
            entry = tarfile.TarInfo(VENDOR_GUID + "/pathname")
            entry.size = len(raw)
            tar.addfile(entry, io.BytesIO(raw))
        with self.assertRaises(ValueError):
            MODULE.inspect(self.project, bad)


if __name__ == "__main__":
    unittest.main()
