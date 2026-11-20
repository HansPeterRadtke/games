"""Unity October 2026 security-fix preflight for internal HPR package builds.

Source of the minimum patched versions: Unity's 2026-11-07 eMudhra and
Brotli advisories. Unsupported or unknown editor streams are not assumed safe.
This guard does not install Unity, change projects, submit products or alter
credentials. Legacy editor compatibility QA remains possible via an explicit
internal-only override in the package builder.
"""
from __future__ import annotations

import re
import os
import subprocess
from pathlib import Path

# Official Unity affected-stream patch baselines. Unknown branches fail closed.
FIXED = {
    (6000, 0): (85, "f", 2),
    (6000, 3): (27, "f", 2),
    (6000, 6): (8, "f", 1),
    (6000, 7): (0, "b", 7),
    (7000, 0): (0, "a", 16),
}
CHANNEL_ORDER = {"a": 0, "b": 1, "f": 2}
VERSION = re.compile(r"^(\d+)\.(\d+)\.(\d+)([abf])(\d+)$")


def version_is_patched(version: str) -> bool:
    """True only for versions within a documented fixed release line."""
    match = VERSION.fullmatch((version or "").strip())
    if not match:
        return False
    major, minor, patch, channel, build = match.groups()
    fixed = FIXED.get((int(major), int(minor)))
    if fixed is None:
        return False
    actual = (int(patch), CHANNEL_ORDER[channel], int(build))
    minimum = (fixed[0], CHANNEL_ORDER[fixed[1]], fixed[2])
    return actual >= minimum


def require_patched_editor(editor: Path) -> str:
    """Query the installed editor and fail closed on unsupported builds."""
    executable = Path(editor)
    if not executable.is_file() or not os.access(executable, os.X_OK):
        raise RuntimeError("Unity Editor executable is not available")
    result = subprocess.run(
        [str(executable), "-version"], capture_output=True, text=True,
        timeout=40, check=False,
    )
    output = (result.stdout + "\n" + result.stderr).strip()
    version = next((line.strip() for line in output.splitlines()
                    if VERSION.fullmatch(line.strip())), "")
    if result.returncode or not version or not version_is_patched(version):
        raise RuntimeError(
            "Unity Editor is not verified as security-patched: "
            + (version or "unrecognized version")
        )
    return version


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("editor", type=Path)
    args = parser.parse_args()
    print("UNITY_SECURITY_PATCHED=" + require_patched_editor(args.editor))
