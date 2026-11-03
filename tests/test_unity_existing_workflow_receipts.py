"""Reject incomplete native acceptance evidence rather than counting PASS lines."""
import importlib.util
from pathlib import Path
import unittest

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
        self.assertEqual((False, False), workflow.classify_native_result("wired", 3, self.success(), ""))

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

if __name__ == "__main__": unittest.main()
