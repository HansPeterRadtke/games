#!/usr/bin/env python3
"""Create-only focused native input API regression; no physical keyboard or UI claim."""
import argparse
import importlib.util
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import time

CASES = {"letter_a", "alpha_1", "left_control", "return", "keypad_enter", "keypad_0", "none", "mouse_not_keyboard", "joystick_not_keyboard", "undefined_numeric_alias", "undefined_large_value", "undefined_negative_value"}


POSITIVE_CASES = {"letter_a", "alpha_1", "left_control", "return", "keypad_enter", "keypad_0"}


def classify(native_exit, data):
    if native_exit != 0 or not isinstance(data, dict) or data.get("aliasLegacyValueUndefined") is not True or data.get("aliasNewValueDefined") is not True:
        return False
    rows = data.get("cases")
    if not isinstance(rows, list) or len(rows) != len(CASES) or any(not isinstance(row, dict) or not isinstance(row.get("name"), str) for row in rows):
        return False
    if {row["name"] for row in rows} != CASES:
        return False
    return all(row.get("passed") is True and row.get("nativeHeld") is True and row.get("nativeEdge") is True and row.get("error") == "" and
        row.get("expected") is (row["name"] in POSITIVE_CASES) and
        type(row.get("pressed")) is bool and type(row.get("edge")) is bool and
        row["pressed"] == row["expected"] and row["edge"] == row["expected"] for row in rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("template", "archive", "editor", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--archive-sha256", required=True)
    parser.add_argument("--import-receipt", type=Path)
    parser.add_argument("--max-seconds", type=int, default=600)
    args = parser.parse_args()
    parent = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(parent))
    from unity_archive_policy import inspect_archive
    spec = importlib.util.spec_from_file_location("helpers", parent / "NativeEditMode/run_native_editmode.py")
    qa = importlib.util.module_from_spec(spec); spec.loader.exec_module(qa)
    if not 60 <= args.max_seconds <= 1200 or not args.editor.is_file() or args.editor.is_symlink():
        raise ValueError("Installed Editor and bounded execution required")
    if args.output.exists() or args.output.is_symlink():
        raise FileExistsError("Inspect existing output; do not replay")
    if not args.output.parent.resolve().is_relative_to(Path("/data/var/marketplace-account-setup")) or args.output.resolve().is_relative_to(args.template.resolve()):
        raise ValueError("Use new private output outside the original template")
    if args.archive.is_symlink() or qa.digest(args.archive) != args.archive_sha256 or inspect_archive(args.archive)["status"] != "PASS":
        raise ValueError("Exact validated archive required")
    if args.template.is_symlink(): raise ValueError("No template symlink")
    for folder in ("Assets", "Packages", "ProjectSettings", "Library"):
        path = args.template / folder
        if not path.is_dir() or any(p.is_symlink() for p in path.rglob("*")):
            raise ValueError("Unsafe original template")
    if args.import_receipt:
        prior = json.loads(args.import_receipt.read_text())
        count, bad = qa.verify_vendor(args.template, args.archive)
        if prior.get("actual_unity_editor_executed") is not True or prior.get("exit_code") != 0 or prior.get("archive_sha256") != args.archive_sha256 or count != 55 or bad:
            raise ValueError("Matching actual native import and exact sources required")
    source_before = qa.snapshot(args.template)
    args.output.mkdir(mode=0o700); project = args.output / "project"; project.mkdir()
    for folder in ("Assets", "Packages", "ProjectSettings", "Library"):
        subprocess.run(["cp", "-a", "--reflink=auto", str(args.template / folder), str(project)], check=True)
    settings_file = project / "ProjectSettings/EditorSettings.asset"
    settings_text = settings_file.read_text()
    settings_text, n = re.subn(r"m_EnterPlayModeOptionsEnabled: \d+", "m_EnterPlayModeOptionsEnabled: 1", settings_text)
    settings_text, m = re.subn(r"m_EnterPlayModeOptions: \d+", "m_EnterPlayModeOptions: 1", settings_text)
    if n != 1 or m != 1: raise ValueError("Unknown private Editor settings layout")
    settings_file.write_text(settings_text)
    started = time.monotonic()
    before_import = qa.snapshot(project)
    commands = []
    if not args.import_receipt:
        command = [str(args.editor), "-batchmode", "-nographics", "-quit", "-projectPath", str(project), "-importPackage", str(args.archive), "-logFile", str(args.output / "import.log")]
        commands.append(command)
        r = subprocess.run(command, timeout=args.max_seconds)
        (args.output / "IMPORT_RESULT.json").write_text(json.dumps({"actual_unity_editor_executed": True, "exit_code": r.returncode, "archive_sha256": args.archive_sha256}, indent=2))
        if r.returncode: raise RuntimeError("Native import failed")
        after_import = qa.snapshot(project)
        # The selected archive intentionally changes vendor source only.
        changed = [name for name, value in before_import.items() if after_import.get(name) != value and not name.startswith("Assets/HPRGameplaySuite/")]
        if changed: raise RuntimeError("Original customer files changed during import: " + str(changed))
    fixtures = project / "Assets/Editor/InputKeySafetyValidator.cs"
    if fixtures.exists(): raise FileExistsError("Private probe collision")
    fixtures.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(Path(__file__).with_name("InputKeySafetyValidator.cs"), fixtures)
    before = qa.snapshot(project)
    (args.output / "protected-before.json").write_text(json.dumps(before, indent=2))
    command = [str(args.editor), "-batchmode", "-nographics", "-projectPath", str(project), "-executeMethod", "InputKeySafetyValidator.Run", "-logFile", str(args.output / "unity.log")]
    commands.append(command)
    (args.output / "launch.json").write_text(json.dumps({"commands": commands, "archive_sha256": args.archive_sha256}, indent=2))
    env = os.environ.copy(); env["HPR_INPUT_KEY_OUTPUT"] = str(args.output)
    try:
        r = subprocess.run(command, env=env, timeout=max(1, args.max_seconds - (time.monotonic() - started)))
        native_exit = r.returncode
    except subprocess.TimeoutExpired: native_exit = -999
    file = args.output / "native-input-keys.json"
    data = json.loads(file.read_text()) if file.exists() else None
    after = qa.snapshot(project); changed = [key for key, value in before.items() if after.get(key) != value]
    source_after = qa.snapshot(args.template); original_changed = [key for key, value in source_before.items() if source_after.get(key) != value]
    count, bad = qa.verify_vendor(project, args.archive)
    passed = classify(native_exit, data) and not changed and not original_changed and count == 55 and not bad
    result = {"status": "PASS" if passed else "FAIL", "actual_unity_editor_executed": True, "native_exit_code": native_exit,
        "archive_sha256": args.archive_sha256, "duration_seconds": round(time.monotonic() - started, 1), "changed_project_files": changed,
        "changed_original_files": original_changed, "exact_product_scripts": count, "vendor_mismatches": bad,
        "native_case_count": len(data.get("cases", [])) if isinstance(data, dict) else 0,
        "physical_keyboard_tested": False, "commercial_release_approved": False}
    (args.output / "RESULT.json").write_text(json.dumps(result, indent=2)); print(json.dumps(result), flush=True)
    return 0 if passed else 1


if __name__ == "__main__": raise SystemExit(main())
