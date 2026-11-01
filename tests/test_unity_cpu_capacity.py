"""Deterministic QA gate for high-load Unity Editor test admission.

The module under test must never stop, renice, reserve, or alter anyone's jobs.
"""
import importlib.util
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "unity/tools/release/gameplay_suite/qa/unity_cpu_preflight.py"
spec = importlib.util.spec_from_file_location("unity_cpu_preflight", SOURCE)
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)


class CpuPreflightContract(unittest.TestCase):
    def test_normal_host_admits_without_side_effects(self):
        result = preflight.evaluate_capacity(
            cpu_count=8, one_min_load=3.5, pressure_percent=18.0,
            max_load_per_cpu=2.0, max_pressure_percent=60.0
        )
        self.assertEqual("admit", result["status"])
        self.assertEqual([], result["reasons"])
        self.assertAlmostEqual(0.4375, result["load_per_cpu"])
        self.assertFalse(result["processes_changed"])

    def test_overloaded_eight_core_host_defers(self):
        result = preflight.evaluate_capacity(
            cpu_count=8, one_min_load=63.0, pressure_percent=86.0,
            max_load_per_cpu=2.0, max_pressure_percent=60.0
        )
        self.assertEqual("defer", result["status"])
        self.assertIn("one-minute runnable load exceeds configured CPU capacity", result["reasons"])
        self.assertIn("CPU pressure exceeds configured saturation limit", result["reasons"])
        self.assertGreater(result["load_per_cpu"], 7.0)

    def test_busy_cpu_pressure_with_low_load_defers(self):
        result = preflight.evaluate_capacity(
            cpu_count=4, one_min_load=2.0, pressure_percent=70.0,
            max_load_per_cpu=2.0, max_pressure_percent=60.0
        )
        self.assertEqual("defer", result["status"])
        self.assertEqual(1, len(result["reasons"]))

    def test_exact_threshold_is_admitted(self):
        result = preflight.evaluate_capacity(
            cpu_count=8, one_min_load=16.0, pressure_percent=60.0,
            max_load_per_cpu=2.0, max_pressure_percent=60.0
        )
        self.assertEqual("admit", result["status"])

    def test_invalid_values_fail_closed(self):
        cases = (
            (0, 4.0, 20.0, 2.0, 60.0),
            (-1, 4.0, 20.0, 2.0, 60.0),
            (4, -2.0, 20.0, 2.0, 60.0),
            (4, float("nan"), 20.0, 2.0, 60.0),
            (4, 2.0, 101.0, 2.0, 60.0),
            (4, 2.0, -1.0, 2.0, 60.0),
            (4, 2.0, 40.0, 0.0, 60.0),
            (4, 2.0, 40.0, 2.0, 0.0),
            (4, 2.0, 40.0, 2.0, 101.0),
        )
        for args in cases:
            with self.subTest(args=args), self.assertRaises(ValueError):
                preflight.evaluate_capacity(*args)

    def test_real_proc_shapes_parsed_without_guessing(self):
        self.assertEqual(62.48, preflight.parse_one_min_load("62.48 55.17 49.22 9/1907 78451"))
        self.assertEqual(85.71, preflight.parse_pressure_percent(
            "some avg10=85.71 avg60=82.00 avg300=75.44 total=5934\n"
            "full avg10=0.00 avg60=0.00 avg300=0.00 total=0\n"))
        for bad in ("", "nonsense", "62.0", "-8.0 0 0", "nan 1 1"):
            with self.subTest(load=bad), self.assertRaises(ValueError):
                preflight.parse_one_min_load(bad)
        for bad in ("", "full avg10=20.0", "some avg60=0.4", "some avg10=110.0"):
            with self.subTest(pressure=bad), self.assertRaises(ValueError):
                preflight.parse_pressure_percent(bad)


if __name__ == "__main__":
    unittest.main()
