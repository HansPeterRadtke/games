"""No external effects: mock the true Infra broker lease contract for Unity QA."""
import importlib.util
import tempfile
import sys
import types
import unittest
from pathlib import Path
from unittest import mock

SOURCE = Path(__file__).resolve().parents[1] / "unity/tools/release/gameplay_suite/qa/unity_urp_broker_retry.py"
sys.path.insert(0, str(SOURCE.parent))
spec = importlib.util.spec_from_file_location("unity_urp_broker_retry_contract", SOURCE)
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


def config(root):
    return types.SimpleNamespace(
        output_root=root / "unique-qa-root",
        fixture=root / "fixture-never-used-by-mock",
        archive=root / "fake-archive",
        editor=Path("/usr/bin/python3"),
        qa=root,
        owner="unity-commercial/test-only-broker-contract",
        max_wait_seconds=60,
        poll_seconds=30,
        required_samples=1,
    )


class UnityBrokerContract(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="hpr_mock_broker_contract_")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.args = config(self.root)
        self.source_sample = {"cpu_count": 8, "one_min_load": 3.0,
                              "pressure_percent": 12.0}
        self.monitor_ok = {"monitor": {"capacity": {"status": "ok"}}}

    def make_broker(self):
        return types.SimpleNamespace(
            analyze_current_machine=mock.Mock(return_value=self.monitor_ok),
            reserve_resources=mock.Mock(return_value=("rb_test_request", "test_private_token")),
            release_resources=mock.Mock(return_value=True),
        )

    def test_mock_healthy_broker_success_uses_real_secure_lease_contract(self):
        broker=self.make_broker()
        with mock.patch.object(worker,"verify_archive"), \
             mock.patch.object(worker,"_read_broker_api",return_value=broker), \
             mock.patch.object(worker,"sample_live",return_value=self.source_sample), \
             mock.patch.object(worker,"no_other_unity",return_value=True), \
             mock.patch.object(worker,"run_attempt",return_value={"status":"complete_verified","attempt":1}), \
             mock.patch.object(worker.time,"monotonic",side_effect=[0,1]):
            code=worker.run_worker(self.args)
        self.assertEqual(0,code)
        broker.reserve_resources.assert_called_once_with(
            "nitro", self.args.owner, 6.0, 0.0, 2.0, 7200, secure=True)
        broker.release_resources.assert_called_once_with(
            self.args.owner, "rb_test_request", control_token="test_private_token")
        self.assertFalse((self.args.output_root / "lease-private.json").exists())

    def test_error_after_secure_grant_is_reported_and_lease_released(self):
        broker=self.make_broker()
        with mock.patch.object(worker,"verify_archive"), \
             mock.patch.object(worker,"_read_broker_api",return_value=broker), \
             mock.patch.object(worker,"sample_live",return_value=self.source_sample), \
             mock.patch.object(worker,"no_other_unity",return_value=True), \
             mock.patch.object(worker,"run_attempt",side_effect=RuntimeError("synthetic owned Unity importer failed")), \
             mock.patch.object(worker.time,"monotonic",side_effect=[0,1]):
            result=worker.run_worker(self.args)
        self.assertEqual(6,result)
        broker.release_resources.assert_called_once()
        self.assertEqual("failed_attempt_requires_review",
                         __import__("json").loads((self.args.output_root/"status.json").read_text())["phase"])
        self.assertFalse((self.args.output_root/"lease-private.json").exists())

    def test_private_lease_file_write_failure_still_releases_grant(self):
        broker=self.make_broker()
        real_write=worker.atomic_status
        def fail_private(path,data):
            if path.name=="lease-private.json":
                raise OSError("synthetic private receipt write failure")
            return real_write(path,data)
        with mock.patch.object(worker,"verify_archive"), \
             mock.patch.object(worker,"_read_broker_api",return_value=broker), \
             mock.patch.object(worker,"sample_live",return_value=self.source_sample), \
             mock.patch.object(worker,"no_other_unity",return_value=True), \
             mock.patch.object(worker,"atomic_status",side_effect=fail_private), \
             mock.patch.object(worker.time,"monotonic",side_effect=[0,1]):
            code=worker.run_worker(self.args)
        self.assertEqual(6,code)
        broker.release_resources.assert_called_once()
        self.assertFalse((self.args.output_root/"lease-private.json").exists())

    def test_failed_secure_release_never_reports_complete_and_retains_credential(self):
        broker=self.make_broker()
        broker.release_resources.return_value=False
        with mock.patch.object(worker,"verify_archive"), \
             mock.patch.object(worker,"_read_broker_api",return_value=broker), \
             mock.patch.object(worker,"sample_live",return_value=self.source_sample), \
             mock.patch.object(worker,"no_other_unity",return_value=True), \
             mock.patch.object(worker,"run_attempt",return_value={"status":"complete_verified","attempt":1}), \
             mock.patch.object(worker.time,"monotonic",side_effect=[0,1]):
            code=worker.run_worker(self.args)
        self.assertEqual(4,code)
        self.assertTrue((self.args.output_root/"lease-private.json").exists())
        self.assertEqual(0o600,(self.args.output_root/"lease-private.json").stat().st_mode & 0o777)
        self.assertEqual("broker_lease_release_uncertain",
                         __import__("json").loads((self.args.output_root/"status.json").read_text())["phase"])

    def test_degraded_health_observation_recovers_without_denied_lease_replay(self):
        broker=self.make_broker()
        broker.analyze_current_machine.side_effect=[
            {"monitor":{"capacity":{"status":"degraded"}}},self.monitor_ok,
        ]
        with mock.patch.object(worker,"verify_archive"), \
             mock.patch.object(worker,"_read_broker_api",return_value=broker), \
             mock.patch.object(worker,"sample_live",return_value=self.source_sample), \
             mock.patch.object(worker,"no_other_unity",return_value=True), \
             mock.patch.object(worker,"run_attempt",return_value={"status":"complete_verified","attempt":1}), \
             mock.patch.object(worker.time,"monotonic",side_effect=[0,1,2]), \
             mock.patch.object(worker.time,"sleep",return_value=None):
            code=worker.run_worker(self.args)
        self.assertEqual(0,code)
        broker.reserve_resources.assert_called_once()
        broker.release_resources.assert_called_once()

    def test_true_broker_reservation_denial_is_not_rerouted_or_retried(self):
        broker=self.make_broker()
        broker.reserve_resources.side_effect=RuntimeError("central_reservation_denied_authorization")
        with mock.patch.object(worker,"verify_archive"), \
             mock.patch.object(worker,"_read_broker_api",return_value=broker), \
             mock.patch.object(worker,"sample_live",return_value=self.source_sample), \
             mock.patch.object(worker,"no_other_unity",return_value=True), \
             mock.patch.object(worker.time,"monotonic",side_effect=[0,1]):
            code=worker.run_worker(self.args)
        self.assertEqual(4,code)
        broker.reserve_resources.assert_called_once()
        broker.release_resources.assert_not_called()


if __name__ == "__main__":
    unittest.main()
