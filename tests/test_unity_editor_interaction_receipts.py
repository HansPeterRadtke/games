"""Prevent rendered-UI acceptance from a mere native result-file presence."""
import importlib.util
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "unity/tools/release/gameplay_suite/qa/EditorUsability/run_editor_interaction.py"
spec = importlib.util.spec_from_file_location("editor_interaction", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class InteractionReceipt(unittest.TestCase):
    def test_exact_native_sequence_and_each_required_frame_are_accepted(self):
        self.assertTrue(module.interaction_complete(0, "\n".join(module.EXPECTED_INTERACTION), None, module.REQUIRED_FRAMES))

    def test_empty_native_result_file_is_not_completion(self):
        self.assertFalse(module.interaction_complete(0, "", None, module.REQUIRED_FRAMES))

    def test_each_missing_observation_rejects_completion(self):
        for index in range(len(module.EXPECTED_INTERACTION)):
            with self.subTest(index=index):
                names = module.EXPECTED_INTERACTION[:index] + module.EXPECTED_INTERACTION[index + 1:]
                self.assertFalse(module.interaction_complete(0, "\n".join(names), None, module.REQUIRED_FRAMES))

    def test_each_missing_rendered_stage_rejects_completion(self):
        for stage in module.REQUIRED_FRAMES:
            with self.subTest(stage=stage):
                self.assertFalse(module.interaction_complete(0, "\n".join(module.EXPECTED_INTERACTION), None, module.REQUIRED_FRAMES - {stage}))

    def test_nonzero_native_exit_or_failure_file_cannot_be_overridden(self):
        for code in (-999, 3):
            self.assertFalse(module.interaction_complete(code, "\n".join(module.EXPECTED_INTERACTION), None, module.REQUIRED_FRAMES))
        self.assertFalse(module.interaction_complete(0, "\n".join(module.EXPECTED_INTERACTION), "error", module.REQUIRED_FRAMES))

if __name__ == "__main__": unittest.main()
