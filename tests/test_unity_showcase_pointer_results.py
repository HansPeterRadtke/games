"""Regression checks for accepting actual standalone showcase logs."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

RUNNER = Path(__file__).resolve().parents[1] / "unity/tools/release/gameplay_suite/qa/PointerAim/run_pointer_player.py"
spec = importlib.util.spec_from_file_location("pointer_qa", RUNNER)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def headless_log():
    cases = [
        ("native", 5, True, "(NaN,NaN)", True),
        ("disabled", 0, False, "(0,0)", True),
        ("absent", 4, False, "(100,100)", True),
        ("nan-x", 4, True, "(NaN,100)", True),
        ("infinite-y", 4, True, "(100,Infinity)", True),
        ("finite", 4, True, "(100,100)", False),
    ]
    lines = [f"HPR_POINTER_CASE stage={stage} graphics=Null reads={reads} available={available} "
             f"pointer={pointer} warnings=0 stayed={stayed} aimed=False pass=True"
             for stage, reads, available, pointer, stayed in cases]
    return "\n".join(lines + ["HPR_POINTER_DONE failures=0", ""])


class PointerResultsTests(unittest.TestCase):
    def accept(self, contents):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "player.log"
            path.write_text(contents)
            return runner.verify_log(path, "Null", runner.BASE_CASES)

    def test_accepts_exercised_native_and_injected_cases(self):
        self.assertEqual(len(self.accept(headless_log())), 6)

    def test_warning_before_probe_subscription_fails_the_run(self):
        with self.assertRaisesRegex(ValueError, "Player diagnostic"):
            self.accept("Screen position out of view frustum (screen pos -nan, -nan)\n" + headless_log())

    def test_passing_flags_cannot_mask_a_turn_with_invalid_coordinates(self):
        contents = headless_log().replace("pointer=(NaN,NaN) warnings=0 stayed=True",
                                          "pointer=(NaN,NaN) warnings=0 stayed=False")
        with self.assertRaisesRegex(ValueError, "turned the character"):
            self.accept(contents)

    def test_injected_nonfinite_case_must_exercise_that_input(self):
        contents = headless_log().replace("pointer=(100,Infinity)", "pointer=(100,100)")
        with self.assertRaisesRegex(ValueError, "requested coordinates"):
            self.accept(contents)

    def test_inactive_or_missing_controls_fail(self):
        for contents in (headless_log().replace("reads=4", "reads=0", 1),
                         headless_log().replace("stage=finite", "stage=nan-x")):
            with self.subTest(contents=contents), self.assertRaises(ValueError):
                self.accept(contents)
