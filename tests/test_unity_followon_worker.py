"""Resource-broker serial Unity buyer QA follower: no real Unity in unit tests."""
import importlib.util
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock, patch

QA = Path(__file__).resolve().parents[1] / "unity/tools/release/gameplay_suite/qa"
sys.path.insert(0, str(QA))
SPEC = importlib.util.spec_from_file_location("unity_customer_followon", QA / "unity_customer_followon.py")
worker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(worker)


class FollowOnContract(TestCase):
    def test_followon_waits_for_real_urp_worker_completion_not_merely_no_unity_pid(self):
        self.assertEqual("wait", worker.upstream_gate(
            {"phase":"waiting_for_cpu_and_broker","attempts_started":0},
            {"state":"running","systemd_active":"active"}))
        self.assertEqual("wait", worker.upstream_gate(
            {"phase":"running_unique_disposable_attempt","attempts_started":1},
            {"state":"running","systemd_active":"active"}))

    def test_proper_urp_result_and_stopped_broker_permit_independent_customer_qa(self):
        self.assertEqual("ready", worker.upstream_gate(
            {"status":"complete_verified"}, {"state":"exited","systemd_active":"inactive"}))
        self.assertEqual("ready", worker.upstream_gate(
            {"phase":"deferred_cpu_overload_wait_window_exhausted"},
            {"state":"stopped","systemd_active":"inactive"}))
        self.assertEqual("ready", worker.upstream_gate(
            {"status":"failed_import_requires_review"},
            {"state":"exited","systemd_active":"inactive"}))

    def test_manual_stop_without_urp_final_receipt_does_not_auto_start(self):
        self.assertEqual("halt", worker.upstream_gate(
            {"phase":"waiting_for_cpu_and_broker","attempts_started":0},
            {"state":"stopped","systemd_active":"inactive"}))
        self.assertEqual("halt", worker.upstream_gate(
            {"phase":"broker_lease_release_uncertain"},
            {"state":"exited","systemd_active":"inactive"}))
        self.assertEqual("halt", worker.upstream_gate({}, {"state":"unknown"}))

    def test_exact_customer_editor_methods_include_correct_quit_behavior(self):
        stages=worker.STAGES
        self.assertEqual(("stats_build","stats_playmode","dirty_asset_copy"),
                         tuple(stage["name"] for stage in stages))
        self.assertTrue(stages[0]["quit"])
        self.assertFalse(stages[1]["quit"])
        self.assertTrue(stages[2]["quit"])
        self.assertIn("BuildNewCustomerScene",stages[0]["method"])
        self.assertIn("RunPlaymode",stages[1]["method"])
        self.assertIn("HprUnrelatedDirtyAssetValidator.Run",stages[2]["method"])
        self.assertTrue(all(stage["receipt_key"].startswith("HPR_") for stage in stages))

    def test_source_validation_rejects_previous_effects_or_missing_files(self):
        with TemporaryDirectory() as td:
            root=Path(td)
            project=root/"buyer"
            project.mkdir()
            originals={"Assets/Customer.asset":"hello"}
            import hashlib
            digests={"Assets/Customer.asset":hashlib.sha256(b"hello").hexdigest()}
            path=project/"Assets/Customer.asset"
            path.parent.mkdir()
            path.write_text("hello")
            self.assertEqual([],worker.changed_originals(project,digests))
            path.write_text("changed")
            self.assertEqual(["Assets/Customer.asset"],worker.changed_originals(project,digests))
            with self.assertRaises(FileExistsError):
                worker.require_fresh_effect(root/"completed-receipt.txt",
                                            existing_effects=[path])
            self.assertFalse((root/"completed-receipt.txt").exists())

    def test_unique_disposable_only_and_no_cleanup_of_prior_project(self):
        with TemporaryDirectory() as td:
            root=Path(td)
            old=root/"old-project"
            old.mkdir()
            (old/"history.json").write_text("{}")
            self.assertFalse(worker.project_preflight(root/"different-project"))
            (root/"different-project").mkdir()
            with self.assertRaises(FileExistsError):
                worker.project_preflight(root/"different-project")
            self.assertTrue((old/"history.json").is_file())

    def test_marked_success_only_when_real_exit_and_required_receipt(self):
        self.assertFalse(worker.stage_accepted({"exit_code":0,"phase_success":True},None,["PASS"]))
        self.assertFalse(worker.stage_accepted({"exit_code":124,"phase_success":False},"key=PASS",["key=PASS"]))
        self.assertFalse(worker.stage_accepted({"exit_code":0,"phase_success":True},"key=FAIL",["key=PASS"]))
        self.assertTrue(worker.stage_accepted({"exit_code":0,"phase_success":True},"key=PASS\n",["key=PASS"]))

    def test_upstream_lease_not_mistaken_for_completion(self):
        self.assertEqual("wait",worker.upstream_gate(
            {"status":"complete_verified"},{"state":"running","systemd_active":"active"}))
        self.assertEqual("halt",worker.upstream_gate(
            {"status":"complete_verified"},{"state":"exited","systemd_active":"inactive",
                                              "reservation_id":"rb_test"}))

    def test_malformed_status_is_failure_not_implicit_ready(self):
        for value in (None,{},[],{"phase":"nonsense"}):
            with self.subTest(value=value):
                self.assertNotEqual("ready",worker.upstream_gate(value,{"state":"exited","systemd_active":"inactive"}))


    def test_output_root_must_not_be_nested_inside_any_source_project(self):
        with TemporaryDirectory() as td:
            root=Path(td)
            upstream=root/"upstream"
            native=root/"native"
            dirty=root/"dirty"
            for folder in (upstream,native,dirty):
                folder.mkdir()
            worker.validate_output_location(root/"new-results",native,dirty,upstream)
            for bad in (native/"customer-project/results",dirty/"customer-project/results",
                        upstream/"log/recovery",native,dirty,upstream):
                with self.subTest(bad=bad),self.assertRaises(ValueError):
                    worker.validate_output_location(bad,native,dirty,upstream)

    def test_vendor_source_meta_guids_are_pinned_not_just_csharp_bytes(self):
        self.assertIn("Assets/HPRGameplaySuite/Integration/HprSuiteIntegration.cs.meta",
                      worker.PREEXISTING_PROJECT_SOURCES["native"])
        self.assertIn("Assets/HPRGameplaySuite/Editor/HprSelectedAbilityInstaller.cs.meta",
                      worker.PREEXISTING_PROJECT_SOURCES["native"])
        self.assertIn("Assets/HPRGameplaySuite/Editor/HprSuiteIntegrationGuide.cs.meta",
                      worker.PREEXISTING_PROJECT_SOURCES["dirty"])


if __name__ == "__main__":
    import unittest
    unittest.main()
