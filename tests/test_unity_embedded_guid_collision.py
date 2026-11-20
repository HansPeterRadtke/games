"""Protect customer-owned embedded UPM package GUIDs before HPR import.

Unity's AssetDatabase uses GUIDs from .meta files for assets across the
project, including embedded packages. A collision under Packages/com.customer
is just as dangerous as one under Assets/MyGame.
"""
import io
from pathlib import Path
import tarfile
import tempfile
import unittest
import importlib.util

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"unity/tools/release/gameplay_suite/qa/customer_integrity.py"
SPEC=importlib.util.spec_from_file_location("hpr_embedded_guid_collision",SOURCE)
validator=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)

VENDOR_GUID="b264fbccf54cda999a913fe5c4089240"
NON_VENDOR_GUID="abababababababababababababababab"

class PackageGuidCollisionPreflight(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="hpr_embedded_guid_collision_")
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.project=self.root/"game"
        (self.project/"Assets/MyGame").mkdir(parents=True)
        (self.project/"Assets/MyGame/Controller.cs").write_text("class Controller {}")
        self.customer=self.project/"Packages/com.customer.game/Runtime"
        self.customer.mkdir(parents=True)
        self.archive=self.root/"hpr.unitypackage"
        with tarfile.open(self.archive,"w:gz") as a:
            entry=tarfile.TarInfo(VENDOR_GUID+"/pathname")
            payload=b"Assets/HPRGameplaySuite/Modules/com.hpr.abilities/Runtime/AbilityRunnerComponent.cs"
            entry.size=len(payload)
            a.addfile(entry,io.BytesIO(payload))

    def test_customer_meta_inside_embedded_package_conflicts(self):
        f=self.customer/"AbilityIntegration.asmref.meta"
        f.write_text("fileFormatVersion: 2\nguid: "+VENDOR_GUID+"\n")
        result=validator.find_customer_guid_collisions(self.project,self.archive)
        self.assertEqual(["Packages/com.customer.game/Runtime/AbilityIntegration.asmref.meta"],result)

    def test_uppercase_hex_meta_guid_still_conflicts(self):
        f=self.customer/"AbilityIntegration.asmref.meta"
        f.write_text("fileFormatVersion: 2\nguid: "+VENDOR_GUID.upper()+"\n")
        result=validator.find_customer_guid_collisions(self.project,self.archive)
        self.assertEqual(["Packages/com.customer.game/Runtime/AbilityIntegration.asmref.meta"],result)

    def test_unrelated_package_meta_guid_does_not_conflict(self):
        (self.customer/"Other.cs.meta").write_text("guid: "+NON_VENDOR_GUID+"\n")
        self.assertEqual([],validator.find_customer_guid_collisions(self.project,self.archive))

    def test_own_hpr_embedded_source_does_not_self_block(self):
        p=self.project/"Packages/com.hpr.abilities/Runtime"
        p.mkdir(parents=True)
        (p/"HprSource.cs.meta").write_text("guid: "+VENDOR_GUID+"\n")
        self.assertEqual([],validator.find_customer_guid_collisions(self.project,self.archive))

    def test_other_hpr_prefix_customer_package_vendor_guid_conflict_not_skipped(self):
        path=self.project/"Packages/com.hpr.customerbridge/Runtime"
        path.mkdir(parents=True)
        (path/"OwnIntegration.cs.meta").write_text("guid: "+VENDOR_GUID+"\n")
        self.assertEqual(
            ["Packages/com.hpr.customerbridge/Runtime/OwnIntegration.cs.meta"],
            validator.find_customer_guid_collisions(self.project,self.archive))

    def test_embedded_package_meta_symlink_escape_refused(self):
        outside=self.root/"private-source"
        outside.write_text("do-not-touch")
        (self.customer/"Leaky.cs.meta").symlink_to(outside)
        with self.assertRaises(ValueError):
            validator.find_customer_guid_collisions(self.project,self.archive)
        self.assertEqual("do-not-touch",outside.read_text())

    def test_packages_root_symlink_refused(self):
        import shutil
        shutil.rmtree(self.project/"Packages")
        outside=self.root/"elsewhere"
        outside.mkdir()
        (self.project/"Packages").symlink_to(outside)
        with self.assertRaises(ValueError):
            validator.find_customer_guid_collisions(self.project,self.archive)

    def test_malformed_embedded_customer_meta_requires_review(self):
        file=self.customer/"CustomerAbility.cs.meta"
        for invalid in ("fileFormatVersion: 2\n", "guid: not-an-id\n",
                        "guid: 0123456789\n"):
            with self.subTest(invalid=invalid):
                file.write_text(invalid)
                with self.assertRaisesRegex(ValueError,"malformed.*GUID"):
                    validator.find_customer_guid_collisions(self.project,self.archive)

    def test_duplicate_customer_guid_in_two_embedded_packages_requires_review(self):
        a=self.customer/"BridgeA.cs.meta"
        b=self.customer/"BridgeB.cs.meta"
        a.write_text("guid: "+NON_VENDOR_GUID+"\n")
        b.write_text("guid: "+NON_VENDOR_GUID+"\n")
        with self.assertRaisesRegex(ValueError,"duplicate.*customer.*GUID"):
            validator.find_customer_guid_collisions(self.project,self.archive)

    def test_multiple_root_guid_entries_in_one_meta_refused(self):
        file=self.customer/"Odd.cs.meta"
        file.write_text("guid: "+NON_VENDOR_GUID+"\nguid: "+VENDOR_GUID+"\n")
        with self.assertRaisesRegex(ValueError,"multiple.*GUID"):
            validator.find_customer_guid_collisions(self.project,self.archive)

    def test_large_embedded_customer_metadata_fails_before_unbounded_read(self):
        file=self.customer/"HugeModel.fbx.meta"
        with file.open("wb") as output:
            output.truncate(4_194_305)
        with self.assertRaisesRegex(ValueError,"exceeds bounded safety scan"):
            validator.find_customer_guid_collisions(self.project,self.archive)

    def test_invalid_utf8_embedded_metadata_refused(self):
        file=self.customer/"Invalid.cs.meta"
        file.write_bytes(b"guid: "+NON_VENDOR_GUID.encode()+b"\n\xff")
        with self.assertRaisesRegex(ValueError,"not valid UTF-8"):
            validator.find_customer_guid_collisions(self.project,self.archive)

    def test_real_reviewed_seller_archive_guids_detect_disposable_customer_collision(self):
        original=Path("/data/var/marketplace-account-setup/hpr-unity-copy-race-reviewed-private-archive-20261102/internal-not-tested-in-unity.unitypackage")
        if not original.is_file():
            self.skipTest("Actual private vendor candidate is not mounted")
        (self.customer/"VendorConflict.cs.meta").write_text("guid: "+VENDOR_GUID+"\n")
        result=validator.find_customer_guid_collisions(self.project,original)
        self.assertEqual(["Packages/com.customer.game/Runtime/VendorConflict.cs.meta"],result)


if __name__=="__main__":unittest.main()
