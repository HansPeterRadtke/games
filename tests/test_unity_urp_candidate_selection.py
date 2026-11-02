"""Source and immutable-archive identity tests for the NEW seven-change HPR package.

Run no Unity Editor, no broker, no external writes. A successful result
means only the worker can select the intended newer archive for QA.
"""
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase, mock

ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/"unity/tools/release/gameplay_suite/qa"
sys.path.insert(0,str(QA))
import unity_urp_broker_retry as worker


class SourceArchiveIdentity(TestCase):
    def test_readonly_report_accepts_explicit_new_candidate_hash(self):
        with tempfile.TemporaryDirectory(prefix="hpr_archive_identity_") as folder:
            archive=Path(folder)/"new.unitypackage"
            archive.write_bytes(b"private new archive, no actual Unity operation")
            new_hash=hashlib.sha256(archive.read_bytes()).hexdigest()
            with mock.patch.object(sys,"argv",["worker","--mode","report","--archive",
                                              str(archive),"--expected-archive-sha256",new_hash]):
                args=worker.parse_args()
                self.assertEqual(new_hash,args.expected_archive_sha256)
                self.assertEqual(new_hash,worker.verify_archive(args.archive,
                                                               args.expected_archive_sha256))
            with mock.patch.object(sys,"argv",["worker","--mode","report","--archive",
                                              str(archive),"--expected-archive-sha256","0"*64]):
                args=worker.parse_args()
                with self.assertRaises(ValueError):
                    worker.verify_archive(args.archive,args.expected_archive_sha256)

    def test_worker_records_exact_requested_hash_not_older_default(self):
        with tempfile.TemporaryDirectory(prefix="hpr_archive_worker_") as folder:
            archive=Path(folder)/"new.unitypackage"
            archive.write_bytes(b"new HPR selected archive version")
            target=hashlib.sha256(archive.read_bytes()).hexdigest()
            output=Path(folder)/"never-existed-worker"
            args=SimpleNamespace(
                archive=archive,expected_archive_sha256=target,
                output_root=output,fixture=Path(folder)/"fixture",
                editor=Path("/usr/bin/python3"),qa=Path(folder),
                owner="unity-commercial/source-only-identity-test",
                poll_seconds=20,required_samples=2,max_wait_seconds=1,
            )
            with mock.patch.object(worker,"_read_broker_api",return_value=object()),\
                 mock.patch.object(worker,"sample_live",return_value={
                     "cpu_count":8,"one_min_load":35.0,"pressure_percent":92.0}),\
                 mock.patch.object(worker,"no_other_unity",return_value=True),\
                 mock.patch.object(worker.time,"monotonic",side_effect=[0,3]):
                result=worker.run_worker(args)
            self.assertEqual(2,result) # no Unity attempt; bounded busy CPU
            receipt=json.loads((output/"status.json").read_text())
            self.assertEqual(target,receipt["archive_sha256"])
            self.assertEqual(0,receipt["attempts_started"])
            self.assertFalse((output/"attempt-001").exists())

    def test_old_archive_remains_default_and_custom_mismatch_not_permitted(self):
        with mock.patch.object(sys,"argv",["worker","--mode","report"]):
            args=worker.parse_args()
        self.assertEqual(worker.DEFAULT_ARCHIVE,args.archive)
        self.assertEqual(worker.EXPECTED_ARCHIVE_SHA256,args.expected_archive_sha256)
        with tempfile.TemporaryDirectory(prefix="hpr_archive_wrong_hash_") as folder:
            archive=Path(folder)/"wrong.unitypackage"
            archive.write_bytes(b"different archive")
            with mock.patch.object(sys,"argv",["worker","--mode","report","--archive",
                                              str(archive)]):
                args=worker.parse_args()
                with self.assertRaises(ValueError):
                    worker.verify_archive(args.archive,args.expected_archive_sha256)

    def test_real_new_qa_archive_pinned_sha_matches_preserved_build_receipt(self):
        folder=Path("/data/var/marketplace-account-setup/hpr-unity-private-seven-source-repack-20261102")
        archive=folder/"internal-not-tested-by-unity.unitypackage"
        receipt=folder/"BUILD_RECEIPT.json"
        if not archive.is_file() or not receipt.is_file():
            self.skipTest("private source archive absent on test machine")
        record=json.loads(receipt.read_text())
        self.assertEqual(record["archive_sha256"],
                         hashlib.sha256(archive.read_bytes()).hexdigest())
        self.assertEqual(161,record["asset_count"])
        self.assertEqual(7,len(record["changed_asset_paths"]))


if __name__=="__main__":
    import unittest
    unittest.main()
