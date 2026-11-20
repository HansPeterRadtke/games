"""Regression safety contract for a purely read-only Unity HPR uninstall preflight."""
from pathlib import Path
import importlib.util
import io
import json
import tarfile
import tempfile
import unittest
from unittest import mock

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

    def test_findings_include_readable_review_actions_not_delete_commands(self):
        (self.project / "Assets/MyGame/Game.unity").write_text(
            "m_Script: {fileID: 11500000, guid: " + VENDOR_GUID + ", type: 3}\n")
        (self.project / "Assets/MyGame/Logic.cs").write_text("using HPR;\n")
        result = MODULE.inspect(self.project, self.archive)
        labels = result["review_actions"]
        self.assertTrue(any("scene" in label.lower() for label in labels))
        self.assertTrue(any("C#" in label for label in labels))
        for label in labels:
            self.assertNotIn("rm -", label)
            self.assertNotIn("DeleteAsset", label)
        self.assertFalse(result["deletion_permitted"])

    def test_unrelated_customer_game_no_references(self):
        result = MODULE.inspect(self.project, self.archive)
        self.assertEqual("no_direct_reference_detected", result["classification"])
        self.assertEqual([], result["dependencies"])
        self.assertEqual([], result["unknowns"])
        self.assertTrue(result["read_only"])
        self.assertFalse(result["deletion_permitted"])

    def test_customer_importer_meta_vendor_reference_detected(self):
        metadata = self.project / "Assets/MyGame/ImportedModel.fbx.meta"
        metadata.write_text(
            "fileFormatVersion: 2\nguid: 11111111111111111111111111111111\n"
            "ModelImporter:\n  externalObjects:\n  - first: {type: Material}\n"
            "    second: {fileID: 11400000, guid: " + OTHER_GUID + ", type: 2}\n")
        result = MODULE.inspect(self.project, self.archive)
        self.assertTrue(any(x["kind"] == "importer_meta_vendor_guid" for x in result["dependencies"]))
        self.assertEqual("customer_dependencies_found", result["classification"])

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

    def test_addressable_reference_identifies_the_vendor_asset_once_per_file(self):
        prefab = self.project / "Assets/MyGame/Loadout.prefab"
        for field in ("m_AssetGUID", "m_assetGUID"):
            for quote in ("", "'", '"'):
                with self.subTest(field=field, quote=quote):
                    content = (f"  primary:\r\n    {field}: {quote}{VENDOR_GUID.upper()}{quote}\r\n"
                               f"  alternatives:\r\n  - {field}: {VENDOR_GUID}\r\n")
                    prefab.write_bytes(content.encode())
                    report = MODULE.inspect(self.project, self.archive)
                    self.assertEqual("customer_dependencies_found", report["classification"])
                    self.assertEqual([{"kind": "addressable_asset_reference",
                                       "path": "Assets/MyGame/Loadout.prefab", "guid": VENDOR_GUID,
                                       "vendor_asset": "Assets/HPRGameplaySuite/AbilityRunner.cs"}],
                                     report["dependencies"])
                    self.assertTrue(any("Addressables" in action for action in report["review_actions"]))
                    self.assertFalse(report["deletion_permitted"])
                    self.assertEqual(content.encode(), prefab.read_bytes())

    def test_addressable_prefab_override_in_embedded_customer_package(self):
        package = self.project / "Packages/com.customer.world"
        package.mkdir(parents=True)
        scene = package / "Encounters.unity"
        for path in ("m_assetGUID", "encounters.Array.data[3].m_AssetGUID"):
            with self.subTest(path=path):
                scene.write_text("    - target: {fileID: 1001}\n"
                                 f"      propertyPath: {path}\n"
                                 f"      value: '{OTHER_GUID}'\n"
                                 "      objectReference: {fileID: 0}\n")
                report = MODULE.inspect(self.project, self.archive)
                self.assertEqual([{"kind": "addressable_asset_reference", "guid": OTHER_GUID,
                                   "path": "Packages/com.customer.world/Encounters.unity",
                                   "vendor_asset": "Assets/HPRGameplaySuite/Samples/Heal.asset"}],
                                 report["dependencies"])

    def test_addressable_lookalikes_and_unrelated_values_are_not_references(self):
        scene = self.project / "Assets/MyGame/Encounters.unity"
        scene.write_text(
            "    m_AssetGUID: 112233445566778899aabbccddeeff00\n"
            f"    old_m_AssetGUID: {VENDOR_GUID}\n"
            f"    m_AssetGUID: {VENDOR_GUID}bad\n"
            f"    m_SubObjectGUID: {VENDOR_GUID}\n"
            f"    # m_AssetGUID: {VENDOR_GUID}\n"
            "      propertyPath: label.m_AssetGUIDSuffix\n"
            f"      value: {VENDOR_GUID}\n"
            "      propertyPath: item.m_AssetGUID\n"
            "      value:\n"
            "    - target: {fileID: 1001}\n"
            "      propertyPath: description\n"
            f"      value: {VENDOR_GUID}\n")
        (scene.parent / "Notes.txt").write_text(f"m_AssetGUID: {VENDOR_GUID}\n")
        report = MODULE.inspect(self.project, self.archive)
        self.assertEqual("no_direct_reference_detected", report["classification"])
        self.assertEqual([], report["dependencies"])

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

    def test_bounded_project_path_inventory_fails_closed(self):
        for i in range(5):
            (self.project / "Assets/MyGame" / f"Extra{i}.cs").write_text("// unrelated")
        result = MODULE.inspect(self.project, self.archive, max_scanned_paths=1)
        self.assertEqual("unknown_project_content_requires_review", result["classification"])
        self.assertTrue(any("traversal limit" in x["reason"] for x in result["unknowns"]))
        self.assertFalse(result["deletion_permitted"])

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


    def test_invalid_manifest_dependency_versions_require_review(self):
        folder = self.project / "Packages"
        folder.mkdir()
        manifest = folder / "manifest.json"
        for deps in ({"com.customer.game": None}, {"com.customer.game": 1},
                     {"com.customer.game": {}}, {"com.customer.game": []},
                     {"com.customer.game": ""}, {"com.customer.game": "   "},
                     {"": "1.0.0"}, {"   ": "1.0.0"}):
            with self.subTest(dependencies=deps):
                manifest.write_text(json.dumps({"dependencies": deps}))
                before = manifest.read_bytes()
                result = MODULE.inspect(self.project, self.archive)
                self.assertEqual("unknown_project_content_requires_review", result["classification"])
                self.assertTrue(any(x["path"] == "Packages/manifest.json" for x in result["unknowns"]))
                self.assertEqual(before, manifest.read_bytes())
                self.assertFalse(result["deletion_permitted"])

    def test_invalid_lock_dependency_entries_require_review(self):
        folder = self.project / "Packages"
        folder.mkdir()
        lock = folder / "packages-lock.json"
        for entry in (None, "1.0.0", [], {}, {"version": None}, {"version": " "},
                      {"version": "1.0.0", "dependencies": []},
                      {"version": "1.0.0", "dependencies": {"com.hpr.stats": None}}):
            with self.subTest(entry=entry):
                lock.write_text(json.dumps({"dependencies": {"com.customer.game": entry}}))
                before = lock.read_bytes()
                result = MODULE.inspect(self.project, self.archive)
                self.assertEqual("unknown_project_content_requires_review", result["classification"])
                self.assertTrue(any(x["path"] == "Packages/packages-lock.json" for x in result["unknowns"]))
                self.assertEqual(before, lock.read_bytes())
                self.assertFalse(result["deletion_permitted"])

    def test_transitive_lock_reference_is_not_silently_ignored(self):
        folder = self.project / "Packages"
        folder.mkdir()
        lock = folder / "packages-lock.json"
        lock.write_text(json.dumps({"dependencies": {"com.customer.bridge": {
            "version": "file:com.customer.bridge", "dependencies": {"com.hpr.stats": "1.0.0"}}}}))
        result = MODULE.inspect(self.project, self.archive)
        self.assertEqual("customer_dependencies_found", result["classification"])
        self.assertTrue(any(x["kind"] == "package_lock_reference" for x in result["dependencies"]))
        self.assertFalse(result["deletion_permitted"])

    def test_valid_unrelated_package_versions_and_exact_read_limit(self):
        folder = self.project / "Packages"
        folder.mkdir()
        manifest = folder / "manifest.json"
        lock = folder / "packages-lock.json"
        for version in ("1.0.0", "file:../customer", "https://example.invalid/game.git#pinned"):
            manifest.write_text(json.dumps({"dependencies": {"com.customer.game": version}}))
            lock.write_text(json.dumps({"dependencies": {"com.customer.game": {
                "version": version, "dependencies": {"com.customer.base": "2.0.0"}}}}))
            result = MODULE.inspect(self.project, self.archive)
            self.assertEqual("no_direct_reference_detected", result["classification"])
            self.assertEqual([], result["unknowns"])
        lock.unlink()  # Disposable fixture only, not owner project data.
        manifest.write_bytes(b'{"dependencies": {}}'.ljust(128, b' '))
        self.assertEqual("no_direct_reference_detected",
                         MODULE.inspect(self.project, self.archive, max_file_bytes=128)["classification"])

    def test_package_metadata_growth_is_bounded_and_requires_review(self):
        folder = self.project / "Packages"
        folder.mkdir()
        original_open = Path.open
        for name in ("manifest.json", "packages-lock.json"):
            metadata = folder / name
            metadata.write_text('{"dependencies": {}}')
            calls = []
            class GrowingFile(io.BytesIO):
                def read(self, size=-1):
                    calls.append(size)
                    return super().read(size)
            def open_growing(path, mode='r', *args, **kwargs):
                if path == metadata and mode == 'rb':
                    return GrowingFile(b'{"dependencies": {}}' + b' ' * 256)
                return original_open(path, mode, *args, **kwargs)
            with self.subTest(name=name):
                with mock.patch.object(Path, "open", open_growing):
                    result = MODULE.inspect(self.project, self.archive, max_file_bytes=128)
                self.assertEqual("unknown_project_content_requires_review", result["classification"])
                self.assertEqual([129], calls)
                self.assertTrue(any(x["path"] == "Packages/" + name for x in result["unknowns"]))
            metadata.unlink()  # Only this test's TemporaryDirectory.


if __name__ == "__main__":
    unittest.main()
