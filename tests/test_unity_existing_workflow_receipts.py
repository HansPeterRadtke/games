"""Reject incomplete native acceptance evidence rather than counting PASS lines."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
import contextlib
import hashlib
import io
import json
import shutil
import tarfile
import tempfile
import types

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "unity/tools/release/gameplay_suite/qa/ExistingGameWorkflow/run_native_workflow.py"
spec = importlib.util.spec_from_file_location("existing_workflow", FILE)
workflow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workflow)

EXPECTED = {
    "independent_customer_scene_created", "new_scene_copy_created",
    "integration_scene_saved_explicitly", "existing_health_and_bindings_survive_scene_reopen",
    "original_scene_bytes_unchanged_before_play",
    "queued_keyboard_event_reaches_existing_input_action_once",
    "input_callback_activates_packaged_runner", "authoritative_existing_health_and_stamina_changed",
    "existing_hud_binding_observes_authoritative_health",
    "cooldown_blocks_second_input_without_charging_again",
    "reenable_does_not_duplicate_input_subscription",
    "customer_save_disk_roundtrip_restores_existing_state",
    "restored_extension_preserves_active_cooldown",
    "detached_feature_keeps_existing_input_and_health_usable",
    "only_optional_runner_and_input_binding_detached",
    "original_customer_scene_still_byte_identical_after_play",
}

class NativeWorkflowEvidence(unittest.TestCase):
    def success(self):
        return "\n".join(name + "=PASS" for name in sorted(EXPECTED))

    def test_complete_native_wired_path_accepted(self):
        self.assertEqual((False, True), workflow.classify_native_result("wired", 0, self.success(), ""))

    def test_many_duplicate_pass_lines_are_not_completion(self):
        self.assertEqual((False, False), workflow.classify_native_result("wired", 0,
            "independent_customer_scene_created=PASS\n" * 40, ""))

    def test_each_missing_contract_observation_blocks_completion(self):
        for missing in EXPECTED:
            with self.subTest(missing=missing):
                text = "\n".join(name + "=PASS" for name in EXPECTED - {missing})
                self.assertEqual((False, False), workflow.classify_native_result("wired", 0, text, ""))

    def test_wrong_native_exit_cannot_be_overridden_by_success_file(self):
        # The URP native run wrote all observations but timed out during exit.
        for native_exit in (3, -999, -15):
            with self.subTest(native_exit=native_exit):
                self.assertEqual((False, False), workflow.classify_native_result(
                    "wired", native_exit, self.success(), ""))

    def test_failure_marker_alongside_positive_receipt_blocks_completion(self):
        self.assertEqual((False, False), workflow.classify_native_result("wired", 0, self.success(), "unexpected error"))

    def test_shadow_is_only_valid_after_actual_input_and_runner_success(self):
        text = "queued_keyboard_event_reaches_existing_input_action_once\ninput_callback_activates_packaged_runner\nFAILED: authoritative_existing_health_and_stamina_changed"
        self.assertEqual((True, False), workflow.classify_native_result("shadow", 3, "", text))
        self.assertEqual((False, False), workflow.classify_native_result("shadow", 3, "",
            "FAILED: authoritative_existing_health_and_stamina_changed"))

    def test_compile_failure_does_not_count_as_shadow_control(self):
        self.assertEqual((False, False), workflow.classify_native_result("shadow", 3, "", "error CS7036"))

    def test_unknown_scenario_is_never_a_pass(self):
        self.assertEqual((False, False), workflow.classify_native_result("other", 0, self.success(), ""))

class ImportPreservation(unittest.TestCase):
    """Exercise the actual create-only driver with a controlled native boundary."""
    def run_import(self, mutation):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            template = root / "template"
            for folder in ("Assets", "Packages", "ProjectSettings", "Library"):
                (template / folder).mkdir(parents=True)
            (template / "Assets/Customer.txt").write_text("customer original")
            (template / "ProjectSettings/EditorSettings.asset").write_text(
                "m_EnterPlayModeOptionsEnabled: 0\nm_EnterPlayModeOptions: 0\n")
            editor = root / "Unity"
            editor.touch()
            archive = root / "candidate.unitypackage"
            scripts = {"Assets/HPRGameplaySuite/Script%d.cs" % n: b"// packaged source\n"
                       for n in range(55)}
            with tarfile.open(archive, "w:gz") as package:
                for n, (name, content) in enumerate(scripts.items()):
                    for part, data in (("pathname", name.encode()), ("asset", content)):
                        member = tarfile.TarInfo("%032x/%s" % (n, part))
                        member.size = len(data)
                        package.addfile(member, io.BytesIO(data))
            output = root / "result"
            argv = [str(FILE), "--template", str(template), "--archive", str(archive),
                    "--archive-sha256", hashlib.sha256(archive.read_bytes()).hexdigest(),
                    "--editor", str(editor), "--output", str(output),
                    "--scenario", "wired", "--domain-reload", "on"]
            real_resolve = Path.resolve
            def resolve(path, *args, **kwargs):
                # Keep this unit test in temporary storage without relaxing production policy.
                if path == root:
                    return Path("/data/var/marketplace-account-setup/unit-test")
                return real_resolve(path, *args, **kwargs)
            def native(command, **kwargs):
                if command[0] == "cp":
                    shutil.copytree(command[-2], Path(command[-1]) / Path(command[-2]).name)
                elif "-importPackage" in command:
                    project = Path(command[command.index("-projectPath") + 1])
                    for name, content in scripts.items():
                        target = project / name
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(content)
                    customer = project / "Assets/Customer.txt"
                    if mutation == "changed": customer.write_text("import overwrote customer")
                    if mutation == "deleted": customer.unlink()
                else:
                    (output / "native-result.txt").write_text(
                        "\n".join(name + "=PASS" for name in sorted(EXPECTED)))
                return types.SimpleNamespace(returncode=0)
            policy = types.SimpleNamespace(inspect_archive=lambda path: {"status": "PASS"})
            with patch.object(workflow.sys, "argv", argv), patch.object(Path, "resolve", resolve), \
                 patch.object(workflow.subprocess, "run", side_effect=native), \
                 patch.dict(workflow.sys.modules, {"unity_archive_policy": policy}), \
                 contextlib.redirect_stdout(io.StringIO()):
                exit_code = workflow.main()
            return exit_code, json.loads((output / "RESULT.json").read_text())

    def test_vendor_import_without_customer_mutation_passes(self):
        code, receipt = self.run_import("none")
        self.assertEqual(0, code)
        self.assertEqual("PASS", receipt["status"])

    def test_customer_overwrite_during_bootstrap_cannot_hide_behind_later_baseline(self):
        code, receipt = self.run_import("changed")
        self.assertEqual(1, code)
        self.assertEqual("FAIL", receipt["status"])
        self.assertIn("Assets/Customer.txt", receipt["modified_original_files"])
        self.assertEqual("bootstrap_customer_preservation", receipt["failure_stage"])
        self.assertIsNone(receipt["native_exit_code"])

    def test_customer_deletion_during_bootstrap_cannot_hide_behind_later_baseline(self):
        code, receipt = self.run_import("deleted")
        self.assertEqual(1, code)
        self.assertEqual("FAIL", receipt["status"])
        self.assertIn("Assets/Customer.txt", receipt["modified_original_files"])
        self.assertEqual("bootstrap_customer_preservation", receipt["failure_stage"])
        self.assertIsNone(receipt["native_exit_code"])

if __name__ == "__main__": unittest.main()
