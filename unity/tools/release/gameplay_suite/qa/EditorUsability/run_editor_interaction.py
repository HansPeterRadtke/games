#!/usr/bin/env python3
"""Private, create-only real Unity Editor interaction observer; broker + owned Xvfb required."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import time


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protected(project):
    result = {}
    for folder in ("Assets", "Packages", "ProjectSettings"):
        for p in (project / folder).rglob("*"):
            if p.is_symlink(): raise ValueError("Private template symlink refused")
            if p.is_file() and not p.relative_to(project).as_posix().startswith("Assets/HPRGameplaySuite/"):
                result[p.relative_to(project).as_posix()] = digest(p)
    return result


def exact_scripts(project, archive):
    with tarfile.open(archive, "r:gz") as package:
        raw = {m.name: package.extractfile(m).read() for m in package if m.isfile()}
    mismatches = []
    count = 0
    for name, body in raw.items():
        if name.endswith("/pathname") and body.decode().rstrip("\r\n").endswith(".cs"):
            count += 1
            path = body.decode().rstrip("\r\n")
            expected = hashlib.sha256(raw[name.rsplit("/", 1)[0] + "/asset"]).hexdigest()
            if not (project / path).is_file() or digest(project / path) != expected: mismatches.append(path)
    return count, mismatches


EXPECTED_INTERACTION = [
    "new_private_asset_folder", "initial_customer_scene_saved",
    "initial_preview_is_read_only_and_blocked", "owned_ability_enables_actual_ui_attach",
    "runner_exists_after_ui_input", "actual_runner_references_customer_ability",
    "actual_runner_references_existing_vitals_adapter", "actual_runner_origin_is_selected_actor",
    "attach_marks_only_open_scene_dirty", "attach_does_not_save_scene",
    "actual_editor_undo_restores_no_runner_without_saving",
    "runner_exists_after_ui_input", "actual_runner_references_customer_ability",
    "actual_runner_references_existing_vitals_adapter", "actual_runner_origin_is_selected_actor",
    "actual_editor_redo_restores_binding_without_saving", "ui_attach_undo_redo_never_saved_scene",
    "ui_actions_preserved_authoritative_player_state"]
REQUIRED_FRAMES = {("ready-for-attach", 370), ("ready-for-attach", 640),
    ("attached-await-undo", 370), ("undone-await-redo", 370), ("redone-await-finish", 370)}


def interaction_complete(native_exit, positive, negative, stages):
    return (native_exit == 0 and positive is not None and negative is None
            and positive.splitlines() == EXPECTED_INTERACTION
            and REQUIRED_FRAMES.issubset(set(stages)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--archive-sha256", required=True)
    parser.add_argument("--editor", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-seconds", type=int, default=1200)
    args = parser.parse_args()
    if not 120 <= args.max_seconds <= 1800: raise ValueError("Bounded interactive QA required")
    if not os.environ.get("DISPLAY"): raise ValueError("A separately owned Xvfb is required")
    if args.output.exists() or args.output.is_symlink(): raise FileExistsError("Inspect prior effects; do not replay")
    if not str(args.output.parent.resolve()).startswith("/data/var/marketplace-account-setup/"): raise ValueError("Private root required")
    if not args.editor.is_file() or digest(args.archive) != args.archive_sha256: raise ValueError("Pinned installed Editor/archive required")
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from unity_archive_policy import inspect_archive
    if inspect_archive(args.archive)["status"] != "PASS": raise ValueError("Archive policy failed")
    for folder in ("Assets", "Packages", "ProjectSettings", "Library"):
        source = args.template / folder
        if not source.is_dir() or source.is_symlink() or any(p.is_symlink() for p in source.rglob("*")):
            raise ValueError("Unsafe original template")
    args.output.mkdir()
    (args.output / "frames").mkdir()
    (args.output / "display.txt").write_text(os.environ["DISPLAY"])
    # Save only the owned X server's authentication-file locator, never cookie bytes.
    display_context = {name: os.environ[name] for name in ("DISPLAY", "XAUTHORITY") if name in os.environ}
    context_file = args.output / "display-env.json"
    context_file.write_text(json.dumps(display_context))
    context_file.chmod(0o600)
    project = args.output / "project"
    project.mkdir()
    for folder in ("Assets", "Packages", "ProjectSettings", "Library"):
        subprocess.run(["cp", "-a", "--reflink=auto", str(args.template / folder), str(project)], check=True)
    cache = args.output / "template-cache-snapshot"
    cache.mkdir()
    for name in ("SourceAssetDB", "ArtifactDB", "Bee", "ScriptAssemblies"):
        if (project / "Library" / name).exists(): shutil.move(str(project / "Library" / name), str(cache / name))
    original = protected(project)
    (args.output / "pre-import-protected.json").write_text(json.dumps(original, indent=2))
    started = time.monotonic()
    imported = subprocess.run([str(args.editor), "-batchmode", "-nographics", "-quit", "-projectPath", str(project),
        "-importPackage", str(args.archive), "-logFile", str(args.output / "archive-import.log")], timeout=args.max_seconds)
    (args.output / "IMPORT_RESULT.json").write_text(json.dumps({"native_exit": imported.returncode, "archive_sha256": args.archive_sha256}, indent=2))
    if imported.returncode != 0: raise RuntimeError("Native archive import failed")
    after_import = protected(project)
    changed_import = [n for n, h in original.items() if after_import.get(n) != h]
    count, mismatch = exact_scripts(project, args.archive)
    if changed_import or count != 55 or mismatch: raise RuntimeError("Import identity/preservation failed: " + str(changed_import + mismatch))
    code = project / "Assets/EditorUsabilityPrivate/Editor/InstallerInteractionProbe.cs"
    code.parent.mkdir(parents=True)
    shutil.copyfile(Path(__file__).with_name("InstallerInteractionProbe.cs"), code)
    before = protected(project)
    (args.output / "protected-before.json").write_text(json.dumps(before, indent=2))
    env = os.environ.copy()
    env["HPR_EDITOR_UI_OUTPUT"] = str(args.output)
    command = [str(args.editor), "-force-glcore", "-projectPath", str(project),
        "-executeMethod", "PrivateEditorUsability.InstallerInteractionProbe.Run", "-logFile", str(args.output / "editor.log")]
    (args.output / "launch.json").write_text(json.dumps({"command": command, "batchmode": False, "display": env["DISPLAY"],
        "graphics_software_requested": env.get("LIBGL_ALWAYS_SOFTWARE"), "archive_sha256": args.archive_sha256}, indent=2))
    seen = set()
    native = subprocess.Popen(command, env=env)
    while native.poll() is None and time.monotonic() - started < args.max_seconds:
        state = args.output / "ui-state.json"
        if state.is_file():
            try: data = json.loads(state.read_text())
            except (json.JSONDecodeError, OSError): data = None
            if data:
                key = (data["stage"], round(data["windowWidth"]))
                if key not in seen:
                    time.sleep(0.6)
                    dest = args.output / "frames" / (key[0] + "-" + str(key[1]) + ".png")
                    capture = subprocess.run(["import", "-display", env["DISPLAY"], "-window", "root", str(dest)], timeout=15)
                    if capture.returncode != 0: raise RuntimeError("Actual X display capture failed")
                    (dest.with_suffix(".json")).write_text(json.dumps(data, indent=2))
                    seen.add(key)
                    print("NATIVE_UI_STAGE", key[0], key[1], flush=True)
        time.sleep(0.5)
    if native.poll() is None:
        native.terminate()
        try: native.wait(timeout=15)
        except subprocess.TimeoutExpired: native.kill(); native.wait()
        exit_code = -999
    else: exit_code = native.returncode
    after = protected(project)
    changed = [n for n, h in before.items() if after.get(n) != h]
    count, mismatch = exact_scripts(project, args.archive)
    positive = args.output / "native-result.txt"
    negative = args.output / "native-failure.txt"
    complete = interaction_complete(exit_code, positive.read_text() if positive.is_file() else None,
        negative.read_text() if negative.is_file() else None, seen)
    ok = complete and not changed and count == 55 and not mismatch
    receipt = {"status": "PASS" if ok else "FAIL", "native_exit": exit_code, "import_exit": imported.returncode,
        "actual_normal_unity_editor_executed": True, "private_display": env["DISPLAY"], "captured_stages": sorted(seen),
        "protected_import_files": len(original), "modified_import_files": changed_import,
        "protected_ui_files": len(before), "modified_original_files": changed, "exact_packaged_scripts": count,
        "vendor_mismatches": mismatch, "duration_seconds": round(time.monotonic() - started, 1),
        "external_buyer_tested": False, "physical_device_tested": False, "commercial_release_approved": False}
    (args.output / "RESULT.json").write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt), flush=True)
    return 0 if ok else 1


if __name__ == "__main__": raise SystemExit(main())
