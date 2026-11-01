#!/usr/bin/env python3
"""Read-only, optional Unity CPU admission preflight.

This checks scheduler saturation before starting an expensive Unity Editor
build. It is NOT a CPU reservation, does not manipulate other processes,
cannot guarantee future available cycles and never alters project files.

Values come from Linux /proc and the current process' effective CPU affinity.
Thresholds are explicitly configurable by the caller. A conservative default
defers when runnable load is over two per allowed CPU or CPU some-pressure
exceeds sixty percent for ten seconds. The caller still checks the resource
broker / project ownership and keeps results of failed experiments.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import re
import sys


def _finite_number(value: float, label: str) -> float:
    try:
        number = float(value)
    except (ValueError, TypeError) as err:
        raise ValueError(label + " must be a finite numeric value") from err
    if not math.isfinite(number):
        raise ValueError(label + " must be finite")
    return number


def parse_one_min_load(text: str) -> float:
    """Read the first of at least three Linux /proc/loadavg load estimates."""
    parts = text.split()
    if len(parts) < 3:
        raise ValueError("Linux /proc/loadavg lacks three load estimates")
    result = _finite_number(parts[0], "one-minute load")
    for candidate in parts[1:3]:
        _finite_number(candidate, "five-/fifteen-minute load")
    if result < 0:
        raise ValueError("one-minute load must be nonnegative")
    return result


def parse_pressure_percent(text: str) -> float:
    """Parse the CPU 'some avg10' ten-second pressure without averaging clocks."""
    matches = [re.match(r"^some\s+avg10=([^\s]+)(?:\s|$)", line.strip())
               for line in text.splitlines()]
    valid = [match.group(1) for match in matches if match is not None]
    if len(valid) != 1:
        raise ValueError("Linux CPU pressure missing unique 'some avg10' record")
    result = _finite_number(valid[0], "CPU pressure")
    if not 0 <= result <= 100:
        raise ValueError("CPU pressure percentage must be between zero and one hundred")
    return result


def evaluate_capacity(cpu_count: int, one_min_load: float,
                      pressure_percent: float,
                      max_load_per_cpu: float = 2.0,
                      max_pressure_percent: float = 60.0) -> dict:
    """Return an explicit status; never schedule, kill, renice or reserve tasks.

    CPU count: integer cores available under current affinity/cpuset.
    Load: host one-minute runnable/blocked task average, nonnegative.
    Pressure: Linux CPU some avg10, percent from 0 through 100.
    Limits: max one-minute load per available CPU, positive; and maximum
    accepted ten-second CPU pressure, strictly positive up to 100.
    """
    if isinstance(cpu_count, bool) or not isinstance(cpu_count, int) or cpu_count <= 0:
        raise ValueError("cpu_count must be a positive integer")
    load = _finite_number(one_min_load, "one-minute load")
    pressure = _finite_number(pressure_percent, "CPU pressure")
    max_ratio = _finite_number(max_load_per_cpu, "maximum load per CPU")
    max_pressure = _finite_number(max_pressure_percent, "maximum CPU pressure")
    if load < 0 or not 0 <= pressure <= 100 or max_ratio <= 0 or not 0 < max_pressure <= 100:
        raise ValueError("Invalid CPU sample or admission limit")

    ratio = load / cpu_count
    reasons = []
    if ratio > max_ratio:
        reasons.append("one-minute runnable load exceeds configured CPU capacity")
    if pressure > max_pressure:
        reasons.append("CPU pressure exceeds configured saturation limit")
    return {
        "status": "defer" if reasons else "admit",
        "reasons": reasons,
        "available_cpu_count": cpu_count,
        "one_minute_load": load,
        "cpu_psi_some_avg10_percent": pressure,
        "load_per_cpu": ratio,
        "configured_max_load_per_cpu": max_ratio,
        "configured_max_cpu_pressure_percent": max_pressure,
        "processes_changed": False,
        "reservation_made": False,
        "warning": "A point-in-time read-only estimate, not a guaranteed CPU reservation.",
    }


def sample_live() -> dict:
    """Read fresh local Linux counters; do not access other agents' process data."""
    allowed_cpus = len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else os.cpu_count()
    if allowed_cpus is None:
        raise ValueError("Could not identify available CPU count")
    return {
        "cpu_count": allowed_cpus,
        "one_min_load": parse_one_min_load(Path("/proc/loadavg").read_text(encoding="utf-8")),
        "pressure_percent": parse_pressure_percent(
            Path("/proc/pressure/cpu").read_text(encoding="utf-8")),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-load-per-cpu", type=float, default=2.0,
                        help="upper safe one-minute runnable task load per allowed CPU; default 2.0")
    parser.add_argument("--max-cpu-pressure-percent", type=float, default=60.0,
                        help="maximum tolerable 10s CPU some-pressure percentage; default 60")
    options = parser.parse_args()
    try:
        result = evaluate_capacity(**sample_live(),
                                   max_load_per_cpu=options.max_load_per_cpu,
                                   max_pressure_percent=options.max_cpu_pressure_percent)
    except (ValueError, OSError) as err:
        print(json.dumps({"status": "error", "reason": str(err), "processes_changed": False}))
        return 3
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "admit" else 2


if __name__ == "__main__":
    sys.exit(main())
