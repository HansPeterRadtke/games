"""Mock Unity process for exact archive identity handoff; NEVER real Editor."""
import contextlib
import hashlib
import io
import json
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

QA = Path(__file__).resolve().parents[1]/"unity/tools/release/gameplay_suite/qa"
sys.path.insert(0,str(QA))
import unity_urp_broker_retry as worker

GUID_ROOT="f"*32
GUID_SOURCE="a"*32
SOURCE_NAME="Assets/HPRGameplaySuite/Editor/HprSelectedAbilityInstaller.cs"
NEW_BYTES=b"// new specific installer source"


def make_archive(path):
    with tarfile.open(path,"w:gz") as tar:
        for guid,name,blob in (
            (GUID_ROOT,"Assets/HPRGameplaySuite",None),
            (GUID_SOURCE,SOURCE_NAME,NEW_BYTES),
        ):
            entries=[("pathname",name.encode()),
                     ("asset.meta",("fileFormatVersion: 2\nguid: "+guid+"\n").encode())]
            if blob is not None:
                entries.append(("asset",blob))
            for suffix,content in entries:
                member=tarfile.TarInfo(guid+"/"+suffix)
                member.size=len(content)
                tar.addfile(member,io.BytesIO(content))


class CandidateWorkerGating(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="hpr_candidate_worker_identity_")
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.archive=self.root/"new.unitypackage"
        make_archive(self.archive)
        self.digest=hashlib.sha256(self.archive.read_bytes()).hexdigest()
        self.args=SimpleNamespace(
            output_root=self.root/"fresh-attempt-only",
            archive=self.archive,expected_archive_sha256=self.digest,
            fixture=self.root/"synthetic-fixture",
            editor=Path("/usr/bin/python3"),
            qa=self.root,
        )
        self.phase_names=[]
        self.mutate_original_on_play=False
        self.mutate_imported_script_on_play=False

    def fake_prepare(self,fixture,project):
        for name in ("Assets","ProjectSettings","Packages"):
            (project/name).mkdir(parents=True,exist_ok=True)
        (project/"ProjectSettings/ProjectVersion.txt").write_text("6000.6.7f1")
        return {"original_file_count":1}

    def fake_run(self,editor,project,log,*,import_package=None,
                 execute_method=None,timeout=1800,extra_env=None):
        stage=log.name
        self.phase_names.append(stage)
        log.write_text("MOCK-UNITY-ONLY: "+stage)
        if import_package is not None:
            path=project/SOURCE_NAME
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(self.new_bytes)
            (project/"Assets/HPRGameplaySuite.meta").write_text("guid: "+GUID_ROOT)
            (project/(SOURCE_NAME+".meta")).write_text("guid: "+GUID_SOURCE)
        if execute_method is not None:
            Path(extra_env["HPR_NEW_INPUT_GAME_UPDATE_RECEIPT"]).write_text(
                "new_input_only_real_game_update=PASS\nkey_release=PASS\n")
            Path(extra_env["HPR_COMBINED_URP_INPUT_RECEIPT"]).write_text(
                "active_urp_17_pipeline=PASS\n")
            if self.mutate_original_on_play:
                (project/"ProjectSettings/ProjectVersion.txt").write_text("corrupted Unity version")
            if self.mutate_imported_script_on_play:
                (project/SOURCE_NAME).write_bytes(b"// damaged imported source")
        return {"phase_success":True,"exit_code":0}

    def attempt(self):
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(worker,"prepare_project",side_effect=self.fake_prepare))
            stack.enter_context(mock.patch.object(worker,"run_unity",side_effect=self.fake_run))
            stack.enter_context(mock.patch.object(worker,"UNITY_QA_FILES",()))
            return worker.run_attempt(self.args,1,None,None)

    def test_correct_import_guid_and_contents_gate_allows_mock_play_test(self):
        self.new_bytes=NEW_BYTES
        result=self.attempt()
        self.assertEqual("complete_verified",result["status"])
        integrity=json.loads((self.args.output_root/"attempt-001/import-identity.json").read_text())
        self.assertEqual("PASS",integrity["status"])
        self.assertEqual(2,integrity["guid_identities_verified"])
        self.assertIn("combined-playmode.unity.log",self.phase_names)

    def test_playmode_modifying_protected_customer_setting_invalidates_result(self):
        self.new_bytes=NEW_BYTES
        self.mutate_original_on_play=True
        result=self.attempt()
        self.assertEqual("failed_playmode_requires_review",result["status"])
        phase=result["phase"]
        self.assertIn("ProjectSettings/ProjectVersion.txt",
                      phase["post_playmode_changed_existing_files"])
        self.assertFalse(phase["originals_remained_unmodified_after_install"])

    def test_playmode_modifying_imported_vendor_script_invalidates_result(self):
        self.new_bytes=NEW_BYTES
        self.mutate_imported_script_on_play=True
        result=self.attempt()
        self.assertEqual("failed_playmode_requires_review",result["status"])
        phase=result["phase"]
        self.assertEqual("FAIL",phase["post_playmode_import_identity_status"])
        self.assertFalse(phase["real_editor_urp_new_input_gameplay_accepted"])

    def test_old_installer_in_new_archive_import_is_not_accepted(self):
        self.new_bytes=b"// older installer already existed"
        result=self.attempt()
        self.assertEqual("failed_import_requires_review",result["status"])
        identity=json.loads((self.args.output_root/"attempt-001/import-identity.json").read_text())
        self.assertEqual("FAIL",identity["status"])
        self.assertTrue(any("payload" in issue for issue in identity["issues"]))
        self.assertNotIn("combined-playmode.unity.log",self.phase_names)


if __name__=="__main__":
    unittest.main()
