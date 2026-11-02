"""Mocked owner-broker contracts for serial customer Editor QA after URP.

No actual broker, Unity instance, machine lease or customer files are mutated
during these tests: all paths are fresh /tmp test locations.
"""
import importlib.util
import json
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

QA=Path(__file__).resolve().parents[1]/"unity/tools/release/gameplay_suite/qa"
sys.path.insert(0,str(QA))
SPEC=importlib.util.spec_from_file_location("customer_followon_contracts",QA/"unity_customer_followon.py")
worker=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(worker)


class MockedFollowOnBroker(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="hpr_followon_broker_mock_")
        self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name)
        editor=root/"fake-editor"
        editor.write_text("#!/bin/sh\nexit 0\n")
        editor.chmod(0o700)
        public=root/"upstream-public-id.json"
        public.write_text(json.dumps({"job_id":"job_"+"1"*24}))
        self.args=types.SimpleNamespace(
            editor=editor,output_root=root/"new-unique-job",native=root/"native",
            dirty=root/"dirty",upstream=root/"finished-upstream",
            upstream_id_file=public,owner="unity-commercial/test-only",
            max_wait_seconds=360,poll_seconds=60,required_samples=1,
            editor_timeout_seconds=60)
        self.sample={"cpu_count":8,"one_min_load":2.0,"pressure_percent":12.0}
        self.status=({"status":"complete_verified"},
                     {"state":"exited","systemd_active":"inactive","reservation_id":None})
        self.completed={"status":"complete_verified","stages":[
            {"name":"stats_build","status":"PASS"},
            {"name":"stats_playmode","status":"PASS"},
            {"name":"dirty_asset_copy","status":"PASS"},
        ]}
        self.broker=types.SimpleNamespace(
            analyze_current_machine=mock.Mock(return_value={"monitor":{"capacity":{"status":"ok"},"snapshot_status":"ok"}}),
            reserve_resources=mock.Mock(return_value=("rb_unit_test", "synthetic_test_secret")),
            release_resources=mock.Mock(return_value=True),
        )

    def patch_inputs(self, *, upstream=None, result=None, monitoring=None):
        return (
            mock.patch.object(worker,"_upstream_status",side_effect=upstream) if upstream is not None
                else mock.patch.object(worker,"_upstream_status",return_value=self.status),
            mock.patch.object(worker,"_check_safe_staged_fixture",return_value={"Assets/a":"sha"}),
            mock.patch.object(worker,"_read_broker_api",return_value=self.broker),
            mock.patch.object(worker,"sample_live",return_value=self.sample),
            mock.patch.object(worker,"no_other_unity",return_value=True),
            mock.patch.object(worker,"_run_permitted_qa",side_effect=result) if isinstance(result,Exception)
                else mock.patch.object(worker,"_run_permitted_qa",return_value=result or self.completed),
            mock.patch.object(worker.time,"monotonic",side_effect=[0,1,2,3,4,5,6]),
            mock.patch.object(worker.time,"sleep",return_value=None),
        )

    def execute(self, **kwargs):
        patches=self.patch_inputs(**kwargs)
        with patches[0],patches[1],patches[2],patches[3],patches[4],patches[5],patches[6],patches[7]:
            return worker.run_worker(self.args)

    def test_secure_broker_grant_after_verified_finished_upstream(self):
        self.assertEqual(0,self.execute())
        self.broker.reserve_resources.assert_called_once_with(
            "nitro",self.args.owner,6.0,0.0,2.0,7200,secure=True)
        self.broker.release_resources.assert_called_once_with(
            self.args.owner,"rb_unit_test",control_token="synthetic_test_secret")
        self.assertFalse((self.args.output_root/"lease-private.json").exists())
        self.assertEqual("complete_verified",
                         json.loads((self.args.output_root/"status.json").read_text())["status"])

    def test_buyer_test_failure_releases_lease_without_replaying_unknown_effect(self):
        self.assertEqual(6,self.execute(result=RuntimeError("synthetic Unity asset import failed")))
        self.broker.release_resources.assert_called_once()
        self.assertFalse((self.args.output_root/"lease-private.json").exists())
        status=json.loads((self.args.output_root/"status.json").read_text())
        self.assertTrue(status["no_replay_in_same_project"])

    def test_broker_refusal_is_not_retried_or_reframed(self):
        self.broker.reserve_resources.side_effect=RuntimeError("central_reservation_denied_authorization")
        self.assertEqual(4,self.execute())
        self.broker.reserve_resources.assert_called_once()
        self.broker.release_resources.assert_not_called()

    def test_unwritable_private_credential_and_failed_release_are_reported(self):
        self.broker.release_resources.return_value=False
        original=worker.atomic_status
        def fail_private(path, data):
            if path.name=="lease-private.json":
                raise OSError("synthetic private credential disk full")
            return original(path,data)
        with mock.patch.object(worker,"atomic_status",side_effect=fail_private):
            code=self.execute()
        self.assertEqual(4,code)
        self.broker.release_resources.assert_called_once()
        state=json.loads((self.args.output_root/"status.json").read_text())
        self.assertEqual("secure_broker_release_unverified",state["phase"])
        self.assertFalse(state["secure_credential_persisted"])
        self.assertFalse((self.args.output_root/"lease-private.json").exists())

    def test_broker_release_failure_never_claims_complete(self):
        self.broker.release_resources.return_value=False
        self.assertEqual(4,self.execute())
        status=json.loads((self.args.output_root/"status.json").read_text())
        self.assertEqual("secure_broker_release_unverified",status["phase"])
        self.assertEqual(0o600,(self.args.output_root/"lease-private.json").stat().st_mode & 0o777)

    def test_upstream_ordinary_status_timeout_retries_a_new_read_only_check(self):
        sequence=[subprocess.TimeoutExpired("owner_job_status",20),self.status]
        self.assertEqual(0,self.execute(upstream=sequence))
        self.broker.reserve_resources.assert_called_once()

    def test_temporary_broker_health_timeout_is_rechecked_not_claimed_complete(self):
        self.broker.analyze_current_machine.side_effect=[
            subprocess.TimeoutExpired("central_broker_status",20),
            {"monitor":{"capacity":{"status":"ok"},"snapshot_status":"ok"}},
        ]
        self.assertEqual(0,self.execute())
        self.broker.reserve_resources.assert_called_once()


if __name__=="__main__":
    unittest.main()
