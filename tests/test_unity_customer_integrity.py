"""Regression tests for preservation of real Unity customers' unrelated project files."""
import importlib.util
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "unity/tools/release/gameplay_suite/qa/customer_integrity.py"
spec = importlib.util.spec_from_file_location("hpr_customer_integrity", MODULE)
customer_integrity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(customer_integrity)


class CustomerIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="hpr_customer_integrity_test_")
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name) / "game"
        self.customer = self.project / "Assets/ExternalCustomerGame"
        self.customer.mkdir(parents=True)
        self.scene = self.customer / "Scenes/ExistingLevel.unity"
        self.scene.parent.mkdir()
        self.scene.write_text("%YAML 1.1\n--- !u!1 &101\nGameObject:\n  m_Name: ExistingPlayer\n")
        (self.scene.parent / "ExistingLevel.unity.meta").write_text(
            "fileFormatVersion: 2\nguid: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n")
        self.controller = self.customer / "ExistingPlayer.cs"
        self.controller.write_text("namespace Customer { public class ExistingPlayer {} }\n")
        (self.customer / "ExistingPlayer.cs.meta").write_text(
            "fileFormatVersion: 2\nguid: bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\n")
        self.settings = self.project / "ProjectSettings"
        self.settings.mkdir(parents=True)
        (self.settings / "InputManager.asset").write_text("customer input axes and bindings\n")
        (self.settings / "GraphicsSettings.asset").write_text("customer pipeline and materials\n")
        (self.settings / "EditorSettings.asset").write_text("customer play settings\n")
        self.packages = self.project / "Packages"
        self.packages.mkdir(parents=True)
        (self.packages / "manifest.json").write_text('{"dependencies": {"com.unity.inputsystem":"1.20.1"}}\n')

    def test_import_with_only_vendor_additions_preserves_scene_meta_scripts_and_settings(self):
        before = customer_integrity.snapshot_customer_project(self.project)
        vendor = self.project / "Assets/HPRGameplaySuite/Runtime"
        vendor.mkdir(parents=True)
        (vendor / "HprEventBus.cs").write_text("namespace HPR {}")
        self.assertEqual([], customer_integrity.compare_customer_snapshot(self.project, before))
        self.assertGreaterEqual(len(before), 7)

    def test_changed_existing_scene_and_input_settings_are_detected(self):
        before = customer_integrity.snapshot_customer_project(self.project)
        self.scene.write_text("an imported product accidentally rewrote the customer's level\n")
        (self.settings / "InputManager.asset").write_text("input axes overwritten\n")
        differences = customer_integrity.compare_customer_snapshot(self.project, before)
        self.assertIn("Assets/ExternalCustomerGame/Scenes/ExistingLevel.unity", differences)
        self.assertIn("ProjectSettings/InputManager.asset", differences)

    def test_removed_or_regenerated_customer_meta_is_detected(self):
        before = customer_integrity.snapshot_customer_project(self.project)
        (self.scene.parent / "ExistingLevel.unity.meta").unlink()
        self.assertIn("Assets/ExternalCustomerGame/Scenes/ExistingLevel.unity.meta",
                      customer_integrity.compare_customer_snapshot(self.project, before))
        (self.scene.parent / "ExistingLevel.unity.meta").write_text(
            "fileFormatVersion: 2\nguid: cccccccccccccccccccccccccccccccc\n")
        self.assertIn("Assets/ExternalCustomerGame/Scenes/ExistingLevel.unity.meta",
                      customer_integrity.compare_customer_snapshot(self.project, before))

    def test_customer_symlink_escape_refused(self):
        external = Path(self.tmp.name) / "private.txt"
        external.write_text("should never be hashed through a project symlink")
        (self.customer / "escaping-file.txt").symlink_to(external)
        with self.assertRaises(ValueError):
            customer_integrity.snapshot_customer_project(self.project)

    def test_matching_vendor_guid_with_unrelated_customer_is_rejected(self):
        archive = Path(self.tmp.name) / "candidate.unitypackage"
        with tarfile.open(archive, "w:gz") as handle:
            for guid, pathname in (
                ("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", "Assets/HPRGameplaySuite/HprEventBus.cs"),
                ("dddddddddddddddddddddddddddddddd", "Assets/HPRGameplaySuite/Sample.asset"),
            ):
                content = (pathname + "\n").encode()
                entry = tarfile.TarInfo(guid + "/pathname")
                entry.size = len(content)
                handle.addfile(entry, io.BytesIO(content))
        conflicts = customer_integrity.find_customer_guid_collisions(self.project, archive)
        self.assertEqual(["Assets/ExternalCustomerGame/ExistingPlayer.cs.meta"], conflicts)

    def test_missing_customer_baseline_is_not_a_false_pass(self):
        self.controller.unlink()
        self.scene.unlink()
        for meta in self.customer.rglob("*.meta"):
            meta.unlink()
        with self.assertRaises(ValueError):
            customer_integrity.snapshot_customer_project(
                self.project, customer_roots=("Assets/DoesNotExist",))


    def test_symlinked_assets_parent_cannot_escape_root(self):
        original_assets = self.project / "Assets"
        outside_assets = Path(self.tmp.name) / "outside-assets"
        original_assets.rename(outside_assets)
        original_assets.symlink_to(outside_assets, target_is_directory=True)
        with self.assertRaises(ValueError):
            customer_integrity.snapshot_customer_project(self.project)

    def test_added_unrequested_customer_asset_detected(self):
        before = customer_integrity.snapshot_customer_project(self.project)
        (self.customer / "InjectedSettings.asset").write_text("unrequested mutation")
        self.assertIn("Assets/ExternalCustomerGame/InjectedSettings.asset",
                      customer_integrity.compare_customer_snapshot(self.project, before))


    def test_existing_vendor_root_meta_is_not_customer_collision(self):
        archive = Path(self.tmp.name) / "vendor-v2.unitypackage"
        guid = "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
        with tarfile.open(archive, "w:gz") as handle:
            body = b"Assets/HPRGameplaySuite\n"
            member = tarfile.TarInfo(guid + "/pathname")
            member.size = len(body)
            handle.addfile(member, io.BytesIO(body))
        (self.project / "Assets/HPRGameplaySuite.meta").write_text(
            "fileFormatVersion: 2\nguid: " + guid + "\n")
        self.assertEqual([], customer_integrity.find_customer_guid_collisions(
            self.project, archive))


if __name__ == "__main__":
    unittest.main()
