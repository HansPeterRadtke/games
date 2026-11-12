"""Exercise the user-facing Play Mode launcher with real archives and a controlled Editor."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from test_unity_release_export import emit_package


SUITE = Path(__file__).resolve().parents[1] / "unity/tools/release/gameplay_suite"
ARCHIVE = "hpr-gameplay-systems-suite-candidate.unitypackage"
SCENE = "Assets/HPRGameplaySuite/Demo/GameplaySuiteShowcase.unity"
CHECKS = """imported_scene_actual_playmode real_awake_and_scene_bindings
collision_aware_character_motor automatic_enemy_chase composition_and_world_registry
combat_and_typed_damage_event live_ability_and_stamina live_weapon_and_checkpoint_restore""".split()

FAKE_EDITOR = '''#!/usr/bin/env python3
import os
from pathlib import Path
import sys
mode = os.environ["FIXTURE_MODE"]
Path(os.environ["LAUNCHED"]).touch()
project = Path(sys.argv[sys.argv.index("-projectPath") + 1])
log = Path(sys.argv[sys.argv.index("-logFile") + 1])
assert sys.argv[sys.argv.index("-executeMethod") + 1] == "HprShowcasePlayAfterStartup.Run"
rows = [k + "=PASS" for k in os.environ["CHECKS"].split()]
events = ["Initialize engine version: 6000.6.8f1 (fixture)", "HPR_QA_REAL_PLAYMODE_PASS"]
if mode == "exception": events.append("ArgumentOutOfRangeException: simulated")
if mode == "compiler-error": events.append("Assets/X.cs(1,2): error CS1002: simulated")
if mode == "partial": rows.pop()
if mode == "duplicate": rows.append(rows[-1])
if mode == "missing-marker": events.pop()
if mode == "edit-after-launch": (project / os.environ["SCENE"]).write_text("changed")
if mode == "replace-release":
    import json
    receipt = Path(os.environ["HPR_SUITE_RELEASE_ROOT"]) / "release-receipt.json"
    data = json.loads(receipt.read_text())
    data["sha256"] = "f" * 64
    receipt.write_text(json.dumps(data))
log.write_text("\\n".join(events) + "\\n")
Path(os.environ["HPR_SUITE_PLAYMODE_RECEIPT"]).write_text("\\n".join(rows) + "\\n")
sys.exit(7 if mode == "failed-exit" else 0)
'''


class PlayModeReleaseIdentityTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name)
        self.project = self.base / "imported game"
        self.scene = self.project / SCENE
        self.scene.parent.mkdir(parents=True)
        self.scene.write_text("fixture scene")
        assets = self.project / "Assets"
        for index, path in enumerate(sorted(assets.rglob("*")), start=1):
            Path(str(path) + ".meta").write_text(f"fileFormatVersion: 2\nguid: {index:032x}\n")
        self.release = self.base / "selected release"
        self.release.mkdir()
        self.archive = self.release / ARCHIVE
        emit_package(assets, self.archive)
        self.sha = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        self.builder = self.release / "release-receipt.json"
        self.builder.write_text(json.dumps({"artifact": ARCHIVE, "sha256": self.sha,
                                           "unity_editor_success": True}))
        self.output = self.release / "actual-playmode-receipt.txt"
        self.launched = self.base / "launched"
        self.editor = self.base / "Unity"
        self.editor.write_text(FAKE_EDITOR)
        self.editor.chmod(0o700)

    def launch(self, mode="pass"):
        env = dict(os.environ, UNITY_BIN=str(self.editor), HPR_SUITE_RELEASE_ROOT=str(self.release),
                   HPR_SUITE_CLEANROOM_PROJECT=str(self.project), FIXTURE_MODE=mode, SCENE=SCENE,
                   LAUNCHED=str(self.launched), CHECKS=" ".join(CHECKS), PYTHONDONTWRITEBYTECODE="1")
        return subprocess.run(["bash", str(SUITE / "validate_playmode.sh")], cwd=self.base,
                              env=env, capture_output=True, text=True, timeout=15)

    def test_cleanroom_and_play_share_default_release_and_project(self):
        def defaults(script):
            return [line for line in (SUITE / script).read_text().splitlines()
                    if line.startswith(("project=", "release="))]
        self.assertEqual(len(defaults("validate_playmode.sh")), 2)
        self.assertEqual(defaults("validate_cleanroom.sh"), defaults("validate_playmode.sh"))

    def test_success_binds_digest_project_and_engine_and_preserves_prior_log(self):
        old = self.release / "actual-playmode.unity.log"
        old.write_text("earlier failed attempt")
        result = self.launch()
        self.assertEqual(result.returncode, 0, result.stderr)
        fields = dict(line.split("=", 1) for line in self.output.read_text().splitlines())
        self.assertEqual({k for k, v in fields.items() if v == "PASS"}, set(CHECKS))
        self.assertEqual(fields["archive_sha256"], self.sha)
        self.assertEqual(fields["unity_version"], "6000.6.8f1")
        self.assertEqual(fields["unity_project"], str(self.project))
        self.assertTrue(Path(fields["unity_log"]).is_file())
        self.assertEqual(old.read_text(), "earlier failed attempt")

    def test_wrong_import_fails_before_staging_code_or_starting_unity(self):
        meta = Path(str(self.scene) + ".meta")
        meta.write_text(meta.read_text() + "userData: local\n")
        result = self.launch()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("metadata payload differs", result.stderr)
        self.assertFalse(self.launched.exists())
        self.assertFalse((self.project / "Assets/Editor").exists())
        self.assertFalse(self.output.exists())

    def test_invalid_export_receipts_fail_before_launch(self):
        for change in ({"sha256": "a" * 64}, {"unity_editor_success": False}, {"artifact": "other"}):
            with self.subTest(change=change):
                self.builder.write_text(json.dumps(dict(artifact=ARCHIVE, sha256=self.sha,
                                                        unity_editor_success=True) | change))
                self.assertNotEqual(self.launch().returncode, 0)
                self.assertFalse(self.launched.exists())
                self.assertFalse(self.output.exists())

    def test_existing_result_and_customer_validator_are_preserved(self):
        folder = self.project / "Assets/Editor"
        folder.mkdir()
        local = folder / "HprShowcasePlayAfterStartup.cs"
        local.write_text("customer-owned file")
        result = self.launch()
        self.assertIn("different existing validator", result.stderr)
        self.assertEqual(list(folder.iterdir()), [local])
        self.output.write_text("original result")
        result = self.launch()
        self.assertIn("existing Play Mode receipt", result.stderr)
        self.assertEqual(self.output.read_text(), "original result")
        self.assertEqual(local.read_text(), "customer-owned file")
        self.assertFalse(self.launched.exists())

    def test_orphaned_validator_metadata_is_preserved(self):
        folder = self.project / "Assets/Editor"
        folder.mkdir()
        meta = folder / "HprShowcasePlayAfterStartup.cs.meta"
        meta.write_text("guid: customer-metadata")
        self.assertIn("existing validator metadata", self.launch().stderr)
        self.assertEqual(list(folder.iterdir()), [meta])
        self.assertEqual(meta.read_text(), "guid: customer-metadata")
        self.assertFalse(self.launched.exists())

    def test_native_failure_or_partial_results_never_publish_a_pass(self):
        for mode in ("exception", "compiler-error", "partial", "duplicate", "missing-marker", "failed-exit"):
            with self.subTest(mode=mode):
                self.assertNotEqual(self.launch(mode).returncode, 0)
                self.assertTrue(self.launched.exists())
                self.assertFalse(self.output.exists())

    def test_edit_during_play_prevents_acceptance(self):
        result = self.launch("edit-after-launch")
        self.assertIn("asset payload differs", result.stderr)
        self.assertFalse(self.output.exists())
        self.assertEqual(self.scene.read_text(), "changed")

    def test_replaced_release_receipt_prevents_acceptance(self):
        self.assertIn("changed during Play Mode", self.launch("replace-release").stderr)
        self.assertFalse(self.output.exists())

    def test_busy_release_is_left_unmodified(self):
        directory = os.open(self.release, os.O_RDONLY)
        try:
            fcntl.flock(directory, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertNotEqual(self.launch().returncode, 0)
            self.assertFalse(self.launched.exists())
            self.assertFalse(self.output.exists())
        finally:
            os.close(directory)
