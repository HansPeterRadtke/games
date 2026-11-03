#!/usr/bin/env python3
"""Create-only private customer workflow experiment; launch only through broker.

The scene and health/input/save sources are representative self-authored fixtures,
not an external paid buyer. Keyboard input is queued through native InputSystem,
not physical hardware. No marketplace actions or source-worktree writes occur.
"""
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


def protected_files(project):
    result = {}
    for folder in ("Assets", "Packages", "ProjectSettings"):
        for file in (project / folder).rglob("*"):
            if file.is_symlink():
                raise ValueError("Symlink in private QA input: " + str(file))
            if file.is_file() and not file.relative_to(project).as_posix().startswith("Assets/HPRGameplaySuite/"):
                result[file.relative_to(project).as_posix()] = digest(file)
    return result


EXPECTED_OBSERVATIONS = frozenset({'independent_customer_scene_created', 'original_scene_bytes_unchanged_before_play', 'customer_save_disk_roundtrip_restores_existing_state', 'original_customer_scene_still_byte_identical_after_play', 'authoritative_existing_health_and_stamina_changed', 'cooldown_blocks_second_input_without_charging_again', 'existing_health_and_bindings_survive_scene_reopen', 'existing_hud_binding_observes_authoritative_health', 'new_scene_copy_created', 'only_optional_runner_and_input_binding_detached', 'integration_scene_saved_explicitly', 'queued_keyboard_event_reaches_existing_input_action_once', 'detached_feature_keeps_existing_input_and_health_usable', 'reenable_does_not_duplicate_input_subscription', 'restored_extension_preserves_active_cooldown', 'input_callback_activates_packaged_runner'})

def classify_native_result(scenario, native_exit, positive_text, negative_text):
    """Require every distinct contract observation and no contradictory marker."""
    required = {name + "=PASS" for name in EXPECTED_OBSERVATIONS}
    lines = positive_text.splitlines()
    positive = (scenario == "wired" and native_exit == 0 and not negative_text and
                len(lines) == len(required) and set(lines) == required)
    negative = (scenario == "shadow" and native_exit == 3 and not positive_text and
        "FAILED: authoritative_existing_health_and_stamina_changed" in negative_text and
        "queued_keyboard_event_reaches_existing_input_action_once" in negative_text and
        "input_callback_activates_packaged_runner" in negative_text)
    return negative, positive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--archive-sha256", required=True)
    parser.add_argument("--editor", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fresh-script-cache", action="store_true", help="Preserve and rebuild copied asset/script databases")
    parser.add_argument("--import-receipt", type=Path, help="Reuse a previously native-imported exact archive template")
    parser.add_argument("--scenario", choices=("shadow", "wired"), required=True)
    parser.add_argument("--domain-reload", choices=("on", "off"), required=True)
    parser.add_argument("--max-seconds", type=int, default=600)
    args = parser.parse_args()
    if not 30 <= args.max_seconds <= 1200:
        raise ValueError("Bounded native run must last at most twenty minutes")
    if args.output.exists() or args.output.is_symlink():
        raise FileExistsError("Refusing to replay a private native experiment")
    if not args.template.is_dir() or args.template.is_symlink() or not args.editor.is_file():
        raise ValueError("Actual original project and installed Editor required")
    if args.archive.is_symlink() or digest(args.archive) != args.archive_sha256:
        raise ValueError("Exact reviewed archive checksum required")
    parent = args.output.parent.resolve()
    if not str(parent).startswith("/data/var/marketplace-account-setup/"):
        raise ValueError("Use the private marketplace QA runtime parent")
    # Validate package before any copying. No archive extraction is performed here.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from unity_archive_policy import inspect_archive
    if inspect_archive(args.archive)["status"] != "PASS":
        raise ValueError("Archive policy failed")
    for folder in ("Assets", "Packages", "ProjectSettings", "Library"):
        source = args.template / folder
        if not source.is_dir() or any(f.is_symlink() for f in source.rglob("*")):
            raise ValueError("Expected safe template folder: " + folder)
    args.output.mkdir()
    project = args.output / "project"
    project.mkdir()
    for folder in ("Assets", "Packages", "ProjectSettings", "Library"):
        subprocess.run(["cp", "-a", "--reflink=auto", str(args.template / folder), str(project)], check=True)
    if args.fresh_script_cache:
        cache_snapshot = args.output / "template-cache-snapshot"
        cache_snapshot.mkdir()
        for name in ("SourceAssetDB", "ArtifactDB", "Bee", "ScriptAssemblies"):
            cached = project / "Library" / name
            if cached.exists(): shutil.move(str(cached), str(cache_snapshot / name))
    settings = project / "ProjectSettings/EditorSettings.asset"
    text = settings.read_text()
    import re
    text, enabled = re.subn(r"m_EnterPlayModeOptionsEnabled: \d+", "m_EnterPlayModeOptionsEnabled: 1", text)
    text, flags = re.subn(r"m_EnterPlayModeOptions: \d+", "m_EnterPlayModeOptions: " + ("1" if args.domain_reload == "off" else "0"), text)
    if enabled != 1 or flags != 1:
        raise ValueError("Unknown private Editor settings layout")
    settings.write_text(text)
    # Bootstrap the actual archive BEFORE adding a probe referencing its new APIs.
    # Unity compiles existing project scripts before processing -importPackage.
    started = time.time()
    import_command = [str(args.editor), "-batchmode", "-nographics", "-quit",
        "-projectPath", str(project), "-importPackage", str(args.archive),
        "-logFile", str(args.output / "archive-import.log")]
    if args.import_receipt is not None:
        prior = json.loads(args.import_receipt.read_text())
        if prior.get("exit_code") != 0 or prior.get("archive_sha256") != args.archive_sha256 or not prior.get("actual_unity_editor_executed"):
            raise ValueError("Template has no matching successful native import receipt")
        with tarfile.open(args.archive, "r:gz") as package:
            raw = {m.name: package.extractfile(m).read() for m in package if m.isfile()}
        scripts = 0
        for key, body in raw.items():
            if key.endswith("/pathname") and body.decode().rstrip("\r\n").endswith(".cs"):
                name = body.decode().rstrip("\r\n")
                source = project / name
                expected = hashlib.sha256(raw[key.rsplit("/", 1)[0] + "/asset"]).hexdigest()
                if not source.is_file() or digest(source) != expected:
                    raise ValueError("Reused native template has changed packaged source")
                scripts += 1
        if scripts != 55:
            raise ValueError("Native template source coverage differs from reviewed archive")
        (args.output / "IMPORT_RESULT.json").write_text(json.dumps({"reused_verified_native_import": True,
            "original_receipt": str(args.import_receipt), "archive_sha256": args.archive_sha256, "exact_scripts": scripts}, indent=2))
    else:
        bootstrap = subprocess.run(import_command, timeout=args.max_seconds)
        (args.output / "IMPORT_RESULT.json").write_text(json.dumps({
            "actual_unity_editor_executed": True, "exit_code": bootstrap.returncode,
            "archive_sha256": args.archive_sha256}, indent=2))
        if bootstrap.returncode != 0:
            raise RuntimeError("Native archive import failed before probe staging")
    remaining_seconds = args.max_seconds - (time.time() - started)
    if remaining_seconds < 30:
        raise TimeoutError("No bounded time remains for native workflow probe")
    code = Path(__file__).resolve().parent
    fixtures = project / "Assets/WorkflowPrivate"
    (fixtures / "Editor").mkdir(parents=True, exist_ok=True)
    for file in code.glob("*.cs"):
        target = fixtures / ("Editor" if file.name.endswith("Validator.cs") else "") / file.name
        shutil.copyfile(file, target)
    shutil.copyfile(code.parent / "HprCustomerAbilityResourceBridge.cs", fixtures / "HprCustomerAbilityResourceBridge.cs")
    before = protected_files(project)
    (args.output / "protected-before.json").write_text(json.dumps(before, indent=2))
    env = os.environ.copy()
    env.update(HPR_WORKFLOW_RECEIPT_ROOT=str(args.output), HPR_WORKFLOW_SCENARIO=args.scenario)
    command = [str(args.editor), "-batchmode", "-nographics", "-projectPath", str(project),
               "-executeMethod", "HprExistingGameInputHealthValidator.Run",
               "-logFile", str(args.output / "unity.log")]
    (args.output / "launch.json").write_text(json.dumps({"command": command, "started_epoch": started,
        "scenario": args.scenario, "domain_reload": args.domain_reload,
        "archive_sha256": args.archive_sha256}, indent=2))
    print("NATIVE_START", args.scenario, args.domain_reload, flush=True)
    try:
        result = subprocess.run(command, env=env, timeout=remaining_seconds)
        native_exit = result.returncode
    except subprocess.TimeoutExpired:
        native_exit = -999
    after = protected_files(project)
    changed = [name for name, old in before.items() if after.get(name) != old]
    # Independently compare every packaged C# file after native ImportPackage.
    vendor_changed = []
    vendor_count = 0
    with tarfile.open(args.archive, "r:gz") as package:
        payloads = {m.name: package.extractfile(m).read() for m in package if m.isfile()}
    for key, raw in payloads.items():
        if not key.endswith("/pathname"):
            continue
        name = raw.decode().rstrip("\r\n")
        if name.endswith(".cs"):
            path = project / name
            expected = hashlib.sha256(payloads[key.rsplit("/", 1)[0] + "/asset"]).hexdigest()
            vendor_count += 1
            if not path.is_file() or digest(path) != expected:
                vendor_changed.append(name)
    negative = args.output / "native-failure.txt"
    positive = args.output / "native-result.txt"
    valid_negative, valid_positive = classify_native_result(args.scenario, native_exit,
        positive.read_text() if positive.is_file() else "",
        negative.read_text() if negative.is_file() else "")
    status = "PASS" if (valid_negative or valid_positive) and not changed and not vendor_changed and vendor_count == 55 else "FAIL"
    receipt = {"status": status, "native_exit_code": native_exit, "scenario": args.scenario,
        "domain_reload": args.domain_reload, "duration_seconds": round(time.time() - started, 1),
        "protected_files": len(before), "modified_original_files": changed,
        "exact_packaged_scripts": vendor_count, "vendor_script_mismatches": vendor_changed,
        "expected_shadow_control_rejected": valid_negative, "native_wired_workflow_passed": valid_positive,
        "actual_unity_editor_executed": True, "physical_keyboard_tested": False,
        "external_buyer_tested": False, "commercial_release_approved": False}
    (args.output / "RESULT.json").write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt), flush=True)
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
