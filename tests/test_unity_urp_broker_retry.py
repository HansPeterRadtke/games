"""Regression gates for broker-managed, retry-on-capacity Unity QA.

Only synthetic temporary projects are created by these tests; Unity and the
resource broker are never started during unit tests.
"""
from pathlib import Path
import importlib.util
import tempfile
import sys
import unittest
import hashlib
import json

QA = Path(__file__).resolve().parents[1] / "unity/tools/release/gameplay_suite/qa"
sys.path.insert(0, str(QA))
SPEC = importlib.util.spec_from_file_location("unity_urp_broker_retry", QA / "unity_urp_broker_retry.py")
worker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(worker)


class RetryAdmission(unittest.TestCase):
    def test_overloaded_host_waits_and_does_not_fake_cpu_allocation(self):
        result = worker.admission_snapshot(8, 31.0, 71.0)
        self.assertEqual("wait_for_cpu", result["decision"])
        self.assertEqual(0, result["cpu_reservations_made"])
        self.assertTrue(result["reasons"])

    def test_healthy_host_candidate_requires_multiple_samples(self):
        first = worker.admission_snapshot(8, 4.0, 18.0)
        self.assertEqual("can_request_lease", first["decision"])
        self.assertFalse(worker.should_attempt([first], 2))
        self.assertTrue(worker.should_attempt([first, first], 2))
        self.assertFalse(worker.should_attempt([first, worker.admission_snapshot(8, 39.0, 81.0)], 2))

    def test_invalid_sample_fails_closed(self):
        for values in ((0, 1.0, 5.0), (8, -1.0, 5.0), (8, 1.0, 120.0)):
            with self.subTest(values=values), self.assertRaises(ValueError):
                worker.admission_snapshot(*values)

    def test_archive_checksum_is_pinned_and_never_mutated(self):
        with tempfile.TemporaryDirectory() as td:
            archive = Path(td) / "candidate.unitypackage"
            archive.write_bytes(b"fake immutable candidate")
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            self.assertEqual(digest, worker.verify_archive(archive, digest))
            with self.assertRaises(ValueError):
                worker.verify_archive(archive, "0"*64)
            self.assertEqual(b"fake immutable candidate", archive.read_bytes())

    def test_prepare_new_project_only_writes_disposable_copy(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root/"source"
            for name in ("ProjectSettings/ProjectVersion.txt",
                         "ProjectSettings/GraphicsSettings.asset",
                         "ProjectSettings/ProjectSettings.asset",
                         "Packages/manifest.json",
                         "Packages/packages-lock.json",
                         "Assets/HprPrivateUrpQA/HprTestUrp.asset",
                         "Assets/HprPrivateUrpQA/HprTestUrp.asset.meta",
                         "Assets/HprPrivateUrpQA.meta",
                         "Assets/UniversalRenderPipelineGlobalSettings.asset",
                         "Assets/DefaultVolumeProfile.asset"):
                f=source/name
                f.parent.mkdir(parents=True,exist_ok=True)
                f.write_text("fixture file " + name)
            (source/"ProjectSettings/ProjectVersion.txt").write_text("m_EditorVersion: 6000.6.7f1")
            (source/"ProjectSettings/ProjectSettings.asset").write_text("activeInputHandler: 1")
            (source/"Packages/manifest.json").write_text(json.dumps({"dependencies": {
                "com.unity.render-pipelines.universal": "17.6.0",
                "com.unity.inputsystem": "1.20.1"}}))
            snap={p.relative_to(source):p.read_bytes() for p in source.rglob("*") if p.is_file()}
            result = worker.prepare_project(source, root/"attempt-001")
            self.assertGreaterEqual(result["original_file_count"], 9)
            self.assertFalse((root/"attempt-001/Library").exists())
            self.assertFalse((root/"attempt-001/Assets/HPRGameplaySuite").exists())
            self.assertTrue((root/"attempt-001/Assets/HprPrivateUrpQA/HprTestUrp.asset").is_file())
            self.assertEqual(snap, {p.relative_to(source):p.read_bytes() for p in source.rglob("*") if p.is_file()})
            with self.assertRaises(FileExistsError):
                worker.prepare_project(source, root/"attempt-001")

    def test_skip_symlinked_source_and_never_overwrite_attempt(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            src=root/"fixture"; (src/"ProjectSettings").mkdir(parents=True)
            (src/"Packages").mkdir()
            (src/"Assets/HprPrivateUrpQA").mkdir(parents=True)
            (src/"ProjectSettings/ProjectVersion.txt").write_text("m_EditorVersion: 6000.6.7f1")
            (src/"ProjectSettings/GraphicsSettings.asset").write_text("sample render pipeline")
            (src/"ProjectSettings/ProjectSettings.asset").write_text("activeInputHandler: 1")
            (src/"Packages/manifest.json").write_text('{"dependencies":{"com.unity.inputsystem":"1.20.1","com.unity.render-pipelines.universal":"17.6.0"}}')
            (src/"Assets/HprPrivateUrpQA/HprTestUrp.asset").symlink_to(root/"external")
            with self.assertRaises(ValueError):
                worker.prepare_project(src,root/"output")

    def test_status_write_is_atomic_and_does_not_touch_sources(self):
        with tempfile.TemporaryDirectory() as td:
            file=Path(td)/"private"/"state.json"
            worker.atomic_status(file,{"phase":"waiting","attempts":0})
            self.assertEqual("waiting",json.loads(file.read_text())["phase"])
            self.assertEqual(0o600, file.stat().st_mode & 0o777)
            self.assertFalse(file.with_suffix(".tmp").exists())


if __name__ == "__main__":
    unittest.main()
