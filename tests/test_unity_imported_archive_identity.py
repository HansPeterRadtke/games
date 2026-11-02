"""The actual frozen Unity .unitypackage must match imported asset bytes+GUIDs.

No real Unity Editor is started by this test; the existing previously
successful customer project gives actual historical imported-file evidence.
"""
import hashlib
import io
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
QA=Path(__file__).resolve().parents[1]/"unity/tools/release/gameplay_suite/qa"
sys.path.insert(0,str(QA))
import unity_imported_archive_identity as identity

ROOT_GUID="f"*32
CS_GUID="a"*32
ROOT="Assets/HPRGameplaySuite"
CS=ROOT+"/Editor/HprBuyerTool.cs"


def create_valid_archive(path,source=b"namespace HPR {}"):
    with tarfile.open(path,"w:gz") as tar:
        for guid,name,payload in ((ROOT_GUID,ROOT,None),(CS_GUID,CS,source)):
            entries=(("pathname",name.encode()),("asset.meta",("fileFormatVersion: 2\nguid: "+guid+"\n").encode()))
            if payload is not None:
                entries+= (("asset",payload),)
            for filename,blob in entries:
                member=tarfile.TarInfo(guid+"/"+filename)
                member.size=len(blob);tar.addfile(member,io.BytesIO(blob))


class UnityImportedPackage(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="hpr_import_source_identity_")
        self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)
        self.archive=self.base/"test.unitypackage"
        create_valid_archive(self.archive)
        self.sha=hashlib.sha256(self.archive.read_bytes()).hexdigest()
        self.project=self.base/"project"
        self.file=self.project/CS
        self.file.parent.mkdir(parents=True)
        (self.project/"Assets/HPRGameplaySuite.meta").write_text("guid: "+ROOT_GUID+"\n")
        self.file.write_bytes(b"namespace HPR {}")
        (self.project/(CS+".meta")).write_text("guid: "+CS_GUID+"\n")

    def run_check(self,sha=None):
        return identity.verify_import(self.archive,self.project,sha or self.sha)

    def test_exact_assets_and_metadata_pass(self):
        result=self.run_check()
        self.assertEqual("PASS",result["status"])
        self.assertEqual(2,result["asset_paths_verified"])
        self.assertEqual(2,result["guid_identities_verified"])
        self.assertEqual(1,result["asset_payloads_verified"])
        self.assertTrue(result["read_only"])
        self.assertFalse(result["unity_editor_was_executed_by_this_check"])

    def test_missing_source_is_failed_not_silently_accepted(self):
        self.file.unlink()
        result=self.run_check()
        self.assertEqual("FAIL",result["status"])
        self.assertTrue(any(CS in x for x in result["issues"]))

    def test_wrong_file_content_is_failed(self):
        self.file.write_text("older HPR editor version")
        result=self.run_check()
        self.assertEqual("FAIL",result["status"])
        self.assertTrue(any("payload" in x for x in result["issues"]))

    def test_original_meta_guid_changed_fails(self):
        (self.project/(CS+".meta")).write_text("guid: "+("c"*32))
        result=self.run_check()
        self.assertEqual("FAIL",result["status"])
        self.assertTrue(any("GUID" in x for x in result["issues"]))

    def test_new_unexpected_vendor_script_not_ignored(self):
        (self.file.parent/"Surprise.cs").write_text("untracked")
        result=self.run_check()
        self.assertEqual("FAIL",result["status"])
        self.assertTrue(any("unexpected" in x for x in result["issues"]))

    def test_symlinked_asset_is_not_followed(self):
        outside=self.base/"unrelated.txt"
        outside.write_text("private unrelated file")
        self.file.unlink()
        self.file.symlink_to(outside)
        with self.assertRaises(ValueError) as error:
            self.run_check()
        self.assertIn("symlink",str(error.exception))
        self.assertEqual("private unrelated file",outside.read_text())

    def test_explicit_archive_hash_mismatch_refused_before_project_scan(self):
        with self.assertRaises(ValueError):
            self.run_check("0"*64)

    def test_invalid_project_folder_refused(self):
        with self.assertRaises(ValueError):
            identity.verify_import(self.archive,self.base/"missing",self.sha)

    def test_previous_real_unity_import_exactly_matches_frozen_binary(self):
        base=Path("/data/var/marketplace-account-setup/hpr-unity-internal-selected-installer-20261101")
        previous=base/"internal-not-published.unitypackage"
        project=Path("/data/tmp/hpr-caltask2fb-selected-20261101/customer-import-selected-installer")
        if not previous.is_file() or not (project/ROOT).is_dir():
            self.skipTest("historical real Unity customer project is not currently mounted")
        digest=hashlib.sha256(previous.read_bytes()).hexdigest()
        receipt=identity.verify_import(previous,project,digest)
        self.assertEqual("PASS",receipt["status"])
        self.assertEqual(161,receipt["asset_paths_verified"])
        self.assertEqual(161,receipt["guid_identities_verified"])
        self.assertGreater(receipt["asset_payloads_verified"],100)

    def test_new_unimported_candidate_does_not_inherit_old_acceptance(self):
        current=Path("/data/var/marketplace-account-setup/hpr-unity-private-seven-source-repack-20261102/internal-not-tested-by-unity.unitypackage")
        older=Path("/data/tmp/hpr-caltask2fb-selected-20261101/customer-import-selected-installer")
        if not current.is_file() or not (older/ROOT).exists():
            self.skipTest("new private candidate/older imported customer project absent")
        r=identity.verify_import(current,older,hashlib.sha256(current.read_bytes()).hexdigest())
        self.assertEqual("FAIL",r["status"])
        self.assertGreaterEqual(sum("payload" in issue for issue in r["issues"]),5)


if __name__=="__main__":
    unittest.main()
