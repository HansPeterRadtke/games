"""Preserve embedded CUSTOMER package files during a Unity HPR upgrade.

Unity customer code, .asmdef/.asmref and package.json inside Packages/
are source files too. The existing Assets+ProjectSettings hashing must
never silently omit these user-owned files.
"""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"unity/tools/release/gameplay_suite/qa/customer_integrity.py"
SPEC=importlib.util.spec_from_file_location("hpr_customer_embedded_integrity",SOURCE)
monitor=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(monitor)

class CustomerEmbeddedPackageFiles(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="hpr_customer_embedded_hashes_")
        self.addCleanup(self.temp.cleanup)
        self.project=Path(self.temp.name)/"buyer"
        (self.project/"Assets/MyGame").mkdir(parents=True)
        (self.project/"Assets/MyGame/OriginalController.cs").write_text("class OriginalController {}")
        self.pkg=self.project/"Packages/com.customer.game"
        (self.pkg/"Runtime").mkdir(parents=True)
        self.script=self.pkg/"Runtime/CustomAdapter.cs"
        self.script.write_text("class CustomAdapter {}")
        (self.pkg/"package.json").write_text('{"name":"com.customer.game","version":"1.0.0"}')
        self.asmref=self.pkg/"Runtime/CustomGame.asmref"
        self.asmref.write_text('{"reference":"HPR.Abilities.Runtime"}')
        self.meta=self.pkg/"Runtime/CustomAdapter.cs.meta"
        self.meta.write_text("guid: dddddddddddddddddddddddddddddddd")
        (self.project/"Packages/manifest.json").write_text('{"dependencies":{}}')
        (self.project/"Packages/packages-lock.json").write_text('{"dependencies":{}}')

    def test_embed_package_sources_and_meta_in_customer_snapshot(self):
        snapshot=monitor.snapshot_customer_project(self.project)
        for name in ("Packages/com.customer.game/Runtime/CustomAdapter.cs",
                     "Packages/com.customer.game/Runtime/CustomAdapter.cs.meta",
                     "Packages/com.customer.game/Runtime/CustomGame.asmref",
                     "Packages/com.customer.game/package.json",
                     "Packages/manifest.json","Packages/packages-lock.json"):
            with self.subTest(name=name):self.assertIn(name,snapshot)

    def test_modified_embedded_customer_script_cannot_pass_hash_check(self):
        before=monitor.snapshot_customer_project(self.project)
        self.script.write_text("using HPR; class CustomAdapter {}")
        changed=monitor.compare_customer_snapshot(self.project,before)
        self.assertEqual(["Packages/com.customer.game/Runtime/CustomAdapter.cs"],changed)

    def test_new_or_removed_customer_package_file_is_detected(self):
        before=monitor.snapshot_customer_project(self.project)
        extra=self.pkg/"Runtime/NewCode.cs"
        extra.write_text("class NewCode {}")
        self.assertIn("Packages/com.customer.game/Runtime/NewCode.cs",
                      monitor.compare_customer_snapshot(self.project,before))
        extra.unlink()
        self.asmref.unlink()
        self.assertIn("Packages/com.customer.game/Runtime/CustomGame.asmref",
                      monitor.compare_customer_snapshot(self.project,before))

    def test_package_json_changes_are_protected(self):
        before=monitor.snapshot_customer_project(self.project)
        (self.pkg/"package.json").write_text('{"dependencies":{"com.hpr.abilities":"2.0.0"}}')
        self.assertIn("Packages/com.customer.game/package.json",
                      monitor.compare_customer_snapshot(self.project,before))

    def test_original_embedded_hpr_package_does_not_count_as_customer(self):
        vendor=self.project/"Packages/com.hpr.abilities/Runtime"
        vendor.mkdir(parents=True)
        (vendor/"Vendor.cs").write_text("namespace HPR {}")
        (vendor/"Vendor.cs.meta").write_text("guid: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
        snapshot=monitor.snapshot_customer_project(self.project)
        self.assertNotIn("Packages/com.hpr.abilities/Runtime/Vendor.cs",snapshot)
        self.assertNotIn("Packages/com.hpr.abilities/Runtime/Vendor.cs.meta",snapshot)

    def test_similarly_prefixed_customer_package_is_still_protected(self):
        # "com.hpr.customerbridge" is NOT one of the ten HPR seller-owned
        # embedded modules. Prefix matching alone can silently omit a buyer's
        # code and .meta files from the entire upgrade snapshot.
        path=self.project/"Packages/com.hpr.customerbridge/Runtime"
        path.mkdir(parents=True)
        script=path/"OwnIntegration.cs"
        script.write_text("using HPR; class OwnIntegration {}")
        meta=path/"OwnIntegration.cs.meta"
        meta.write_text("guid: " + "c"*32)
        current=monitor.snapshot_customer_project(self.project)
        self.assertIn("Packages/com.hpr.customerbridge/Runtime/OwnIntegration.cs",current)
        self.assertIn("Packages/com.hpr.customerbridge/Runtime/OwnIntegration.cs.meta",current)

    def test_explicit_vendor_module_names_match_exact_frozen_archive(self):
        import tarfile
        package=Path("/data/var/marketplace-account-setup/hpr-unity-internal-selected-installer-20261101/internal-not-published.unitypackage")
        if not package.is_file():
            self.skipTest("Actual frozen HPR Unity export is not accessible")
        module_names=set()
        with tarfile.open(package,"r:gz") as archive:
            for item in archive:
                if not item.name.endswith("/pathname"):
                    continue
                stream=archive.extractfile(item)
                self.assertIsNotNone(stream)
                path=stream.read().decode("utf-8").strip().split("/")
                if len(path)>4 and path[:3]==["Assets","HPRGameplaySuite","Modules"]:
                    module_names.add(path[3])
        self.assertEqual(monitor.HPR_OWNED_EMBEDDED_MODULES,module_names)
        self.assertEqual(10,len(module_names))

    def test_symlink_inside_customer_embedded_package_is_refused(self):
        outside=Path(self.temp.name)/"private-extra"
        outside.write_text("DO_NOT_READ")
        (self.pkg/"Runtime/Linked.cs").symlink_to(outside)
        with self.assertRaises(ValueError):
            monitor.snapshot_customer_project(self.project)
        self.assertEqual("DO_NOT_READ",outside.read_text())

    def test_symlinked_packages_root_is_refused(self):
        import shutil
        shutil.rmtree(self.project/"Packages")
        outside=Path(self.temp.name)/"outside-packages"
        outside.mkdir()
        (self.project/"Packages").symlink_to(outside)
        with self.assertRaises(ValueError):
            monitor.snapshot_customer_project(self.project)


if __name__=="__main__":unittest.main()
