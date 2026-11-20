#!/usr/bin/env python3
"""Create one private native Build Settings serialization fixture, never uninstall.

Launch through an owned resource-broker job. Copies only vendor Assets plus
Packages/ProjectSettings/Library into a new project; original templates stay intact.
Only the new copied EditorBuildSettings asset is intentionally authored by Unity.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time


def load_helpers():
    path = Path(__file__).resolve().parents[1] / "NativeEditMode/run_native_editmode.py"
    spec = importlib.util.spec_from_file_location("native_helpers", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RUNTIME_ROOT = Path("/data/var/marketplace-account-setup")


def validate_output_location(output, template):
    """Validate private, create-only output without creating any files."""
    if output.exists() or output.is_symlink():
        raise FileExistsError("Inspect existing results; never replay a fixture")
    if not output.parent.resolve().is_relative_to(RUNTIME_ROOT.resolve()):
        raise ValueError("Private task runtime required")
    if output.resolve().is_relative_to(template.resolve()):
        raise ValueError("Cannot write fixture output inside the original template")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--import-receipt", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--archive-sha256", required=True)
    parser.add_argument("--editor", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-seconds", type=int, default=600)
    args = parser.parse_args()
    qa = load_helpers()
    if not 60 <= args.max_seconds <= 900:
        raise ValueError("Bounded native time required")
    validate_output_location(args.output, args.template)
    if args.archive.is_symlink() or qa.digest(args.archive) != args.archive_sha256:
        raise ValueError("Exact private archive required")
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from unity_archive_policy import inspect_archive
    if inspect_archive(args.archive)["status"] != "PASS":
        raise ValueError("Archive path/content policy failed")
    prior = json.loads(args.import_receipt.read_text())
    if prior.get("actual_unity_editor_executed") is not True or prior.get("exit_code") != 0 or prior.get("archive_sha256") != args.archive_sha256:
        raise ValueError("Actual matching successful native import required")
    if not args.editor.is_file() or args.editor.is_symlink() or args.template.is_symlink():
        raise ValueError("Installed Editor and private source project required")
    for folder in ("Assets", "Packages", "ProjectSettings", "Library"):
        path = args.template / folder
        if not path.is_dir() or any(p.is_symlink() for p in path.rglob("*")):
            raise ValueError("Unsafe source folder: " + folder)
    count, bad = qa.verify_vendor(args.template, args.archive)
    if count != 55 or bad:
        raise ValueError("Template source differs from exact native-imported archive")
    source_before = qa.snapshot(args.template)
    args.output.mkdir(mode=0o700)
    project = args.output / "project"
    (project / "Assets/Editor").mkdir(parents=True)
    for folder in ("Packages", "ProjectSettings", "Library"):
        subprocess.run(["cp", "-a", "--reflink=auto", str(args.template / folder), str(project)], check=True)
    vendor = args.template / "Assets/HPRGameplaySuite"
    subprocess.run(["cp", "-a", "--reflink=auto", str(vendor), str(project / "Assets")], check=True)
    if vendor.with_suffix(".meta").is_file():
        shutil.copyfile(vendor.with_suffix(".meta"), project / "Assets/HPRGameplaySuite.meta")
    shutil.copyfile(Path(__file__).with_name("NativeBuildSettingsFixture.cs"), project / "Assets/Editor/NativeBuildSettingsFixture.cs")
    before = qa.snapshot(project)
    (args.output / "protected-before.json").write_text(json.dumps(before, indent=2))
    (args.output / "source-before.json").write_text(json.dumps(source_before, indent=2))
    command = [str(args.editor), "-batchmode", "-nographics", "-quit", "-projectPath", str(project),
        "-executeMethod", "NativeBuildSettingsFixture.Run", "-logFile", str(args.output / "unity.log")]
    (args.output / "launch.json").write_text(json.dumps({"command": command, "archive_sha256": args.archive_sha256,
        "intentionally_authored_copied_file": "ProjectSettings/EditorBuildSettings.asset", "original_template_not_modified": True}, indent=2))
    env = os.environ.copy(); env["HPR_SETTINGS_FIXTURE_OUTPUT"] = str(args.output)
    started = time.monotonic()
    try:
        result = subprocess.run(command, env=env, timeout=args.max_seconds)
        code = result.returncode
    except subprocess.TimeoutExpired:
        code = -999
    file = args.output / "native-settings.json"
    data = json.loads(file.read_text()) if file.is_file() else {}
    after = qa.snapshot(project)
    changed = [key for key, value in before.items() if after.get(key) != value]
    source_after = qa.snapshot(args.template)
    original_changes = [key for key, value in source_before.items() if source_after.get(key) != value]
    count, bad = qa.verify_vendor(project, args.archive)
    settings = project / "ProjectSettings/EditorBuildSettings.asset"
    text = settings.read_text() if settings.is_file() else ""
    valid = code == 0 and data.get("nativeSceneAssetLoaded") is True and data.get("configuredScenes") == 1 and data.get("configuredEnabled") is True
    valid = valid and data.get("scenePath") == "Assets/HPRGameplaySuite/Demo/GameplaySuiteShowcase.unity" and data.get("sceneGuid") == "4da0644b7fd1cbd7b9f70bd2b208b822"
    valid = valid and data.get("sceneGuid") in re.findall(r"\bguid:\s*([0-9a-f]{32})", text) and not original_changes and changed == ["ProjectSettings/EditorBuildSettings.asset"] and count == 55 and not bad
    receipt = {"status": "PASS" if valid else "FAIL", "native_exit_code": code, "actual_unity_editor_executed": True,
        "duration_seconds": round(time.monotonic() - started, 1), "archive_sha256": args.archive_sha256,
        "changed_copied_files": changed, "changed_original_source_files": original_changes,
        "exact_product_scripts": count, "vendor_mismatches": bad, "native_build_settings_saved": valid,
        "rendered_usability_tested": False, "uninstall_performed": False}
    (args.output / "RESULT.json").write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt), flush=True)
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
