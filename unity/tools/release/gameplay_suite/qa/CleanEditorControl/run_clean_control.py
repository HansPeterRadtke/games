#!/usr/bin/env python3
"""Create a genuinely new native Unity project without importing the HPR product.
Launch through the owner resource broker; output is create-only private runtime.
The verdict concerns validity of the no-product control, not product acceptance.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time


def snapshot(project):
    result = {}
    for folder in ("Assets", "Packages", "ProjectSettings"):
        for path in (project / folder).rglob("*"):
            if path.is_symlink():
                raise ValueError("Unexpected symlink in control")
            if path.is_file():
                result[path.relative_to(project).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--editor", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-seconds", type=int, default=660)
    parser.add_argument("--settle-before-play", action="store_true", help="Observe startup in Edit mode for twenty seconds before Play")
    parser.add_argument("--input-system", action="store_true", help="Configure official Input System 1.20.1 in this new control only")
    parser.add_argument("--play-cycles", action="store_true", help="Observe two native Play sessions")
    parser.add_argument("--disable-domain-reload", action="store_true")
    parser.add_argument("--graphics", action="store_true", help="Require software OpenGL under a separately owned Xvfb")
    args = parser.parse_args()
    if args.settle_before_play and not args.play_cycles:
        raise ValueError("Settling is a Play-control condition")
    if not args.editor.is_file() or args.editor.is_symlink():
        raise ValueError("Installed real Editor required")
    if not 60 <= args.max_seconds <= 900:
        raise ValueError("Bounded control required")
    if args.output.exists() or args.output.is_symlink():
        raise FileExistsError("Inspect prior effects; never replay an output")
    if not str(args.output.parent.resolve()).startswith("/data/var/marketplace-account-setup/"):
        raise ValueError("Private control runtime root required")
    args.output.mkdir()
    project = args.output / "project"
    started = time.monotonic()
    graphics_flags = ["-force-glcore"] if args.graphics else ["-nographics"]
    if args.graphics and not os.environ.get("DISPLAY"):
        raise ValueError("An explicitly owned graphics display is required")
    commands = [
        [str(args.editor), "-batchmode", *graphics_flags, "-quit", "-createProject", str(project),
         "-logFile", str(args.output / "create.log")],
        [str(args.editor), "-batchmode", *graphics_flags, "-projectPath", str(project),
         "-executeMethod", "PrivateEditorControl.CleanEditorControl.RunPlayCycles" if args.play_cycles else "PrivateEditorControl.CleanEditorControl.Run",
         "-logFile", str(args.output / "observe.log")]]
    (args.output / "launch.json").write_text(json.dumps({"commands": commands, "copies_existing_library": False,
        "imports_product": False, "requested_graphics": args.graphics}, indent=2))
    create = subprocess.run(commands[0], timeout=args.max_seconds)
    if create.returncode != 0:
        raise RuntimeError("Native create-project failed: " + str(create.returncode))
    if args.disable_domain_reload:
        import re
        settings = project / "ProjectSettings/EditorSettings.asset"
        text = settings.read_text()
        text, enabled = re.subn(r"m_EnterPlayModeOptionsEnabled: \d+", "m_EnterPlayModeOptionsEnabled: 1", text)
        text, flags = re.subn(r"m_EnterPlayModeOptions: \d+", "m_EnterPlayModeOptions: 1", text)
        if enabled != 1 or flags != 1:
            raise ValueError("Unknown native reload configuration")
        settings.write_text(text)
    if args.input_system:
        import re
        manifest = project / "Packages/manifest.json"
        packages = json.loads(manifest.read_text())
        packages["dependencies"]["com.unity.inputsystem"] = "1.20.1"
        manifest.write_text(json.dumps(packages, indent=2))
        settings = project / "ProjectSettings/ProjectSettings.asset"
        text, changed = re.subn(r"activeInputHandler: \d+", "activeInputHandler: 1", settings.read_text())
        if changed != 1:
            raise ValueError("Unknown input-handler setting")
        settings.write_text(text)
        configure = [str(args.editor), "-batchmode", *graphics_flags, "-quit", "-projectPath", str(project),
                     "-logFile", str(args.output / "configure-input.log")]
        remaining = args.max_seconds - (time.monotonic() - started)
        if remaining < 30:
            raise TimeoutError("No time remains to configure input control")
        configured = subprocess.run(configure, timeout=remaining)
        (args.output / "CONFIGURE_RESULT.json").write_text(json.dumps({"native_exit": configured.returncode,
            "command": configure, "requested_inputsystem": "1.20.1"}, indent=2))
        if configured.returncode != 0:
            raise RuntimeError("Native input-package configuration failed")
    before = snapshot(project)
    (args.output / "protected-before.json").write_text(json.dumps(before, indent=2))
    code = project / "Assets/Editor/CleanEditorControl.cs"
    code.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(Path(__file__).with_name("CleanEditorControl.cs"), code)
    remaining = args.max_seconds - (time.monotonic() - started)
    if remaining < 30:
        raise TimeoutError("No bounded observation time remains")
    env = os.environ.copy()
    env["UNITY_CLEAN_CONTROL_OUTPUT"] = str(args.output)
    env["UNITY_CLEAN_CONTROL_SETTLE"] = "1" if args.settle_before_play else "0"
    try:
        observed = subprocess.run(commands[1], env=env, timeout=remaining)
        native_exit = observed.returncode
    except subprocess.TimeoutExpired:
        native_exit = -999
    after = snapshot(project)
    changed = [name for name, old in before.items() if after.get(name) != old]
    receipt = args.output / "native-observation.json"
    data = json.loads(receipt.read_text()) if receipt.is_file() else {}
    logs = "\n".join((args.output / name).read_text(errors="replace") for name in ("create.log", "observe.log"))
    if args.input_system:
        logs += "\n" + (args.output / "configure-input.log").read_text(errors="replace")
    search_exception = "ArgumentOutOfRangeException: Index was out of range" in logs and "UnityEditor.Search.SearchDatabase" in logs
    valid = native_exit == 0 and data.get("nativeUpdateProbeCompleted") is True and data.get("productAssemblyCount") == 0 and data.get("assetScriptCount") == 1 and data.get("observedSeconds", 0) >= 20 and data.get("observedEditorUpdates", 0) >= 10 and not changed
    valid = valid and data.get("graphicsDevice") == ("OpenGLCore" if args.graphics else "Null")
    if args.play_cycles:
        valid = valid and data.get("completedPlayCycles") == 2 and data.get("domainReloadDisabled") == args.disable_domain_reload
    if args.settle_before_play:
        valid = valid and data.get("editSecondsBeforePlay", 0) >= 20
    if args.input_system:
        lock = json.loads((project / "Packages/packages-lock.json").read_text())
        valid = valid and lock["dependencies"]["com.unity.inputsystem"]["version"] == "1.20.1"
    result = {"status": "CONTROL_VALID" if valid else "CONTROL_INCOMPLETE", "native_create_exit": create.returncode,
        "native_observe_exit": native_exit, "actual_unity_editor_executed": True,
        "copied_existing_library": False, "imported_hpr_package": False,
        "search_exception_seen": search_exception, "original_files": len(before), "changed_original_files": changed,
        "duration_seconds": round(time.monotonic() - started, 1), "observation": data,
        "requested_startup_settle": args.settle_before_play,
        "requested_inputsystem": "1.20.1" if args.input_system else None,
        "requested_graphics": args.graphics, "requested_play_cycles": args.play_cycles,
        "requested_domain_reload_disabled": args.disable_domain_reload, "rendered_gui_tested": False, "commercial_release_approved": False}
    (args.output / "RESULT.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result), flush=True)
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
