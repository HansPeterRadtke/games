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


COLD_OBSERVATIONS = frozenset({
    "cold_scene_reopened_with_original_player_and_bindings", "cold_process_starts_from_serialized_baseline",
    "saved_customer_state_restored_after_process_restart", "existing_hud_tracks_cold_restored_health",
    "restored_cooldown_remains_relative_to_new_game_clock", "queued_existing_input_reaches_restored_runner_once",
    "restored_cooldown_rejects_without_charging", "invalid_snapshot_preserves_customer_state_and_cooldown",
    "source_save_and_scene_unchanged_before_cooldown_wait", "saved_cooldown_naturally_expires_on_new_process_clock",
    "existing_input_activates_after_cold_restore_expiry", "authoritative_vitals_and_hud_update_after_expiry",
    "fresh_process_observation_recorded", "source_save_unchanged_after_cold_play", "integrated_scene_unchanged_after_cold_play"})


def classify_cold_result(native_exit, positive, negative):
    required = {name + "=PASS" for name in COLD_OBSERVATIONS}
    lines = positive.splitlines()
    return native_exit == 0 and not negative and len(lines) == len(required) and set(lines) == required


CONFIG_OBSERVATIONS = frozenset({
    "valid_default", "valid_zero_cost_and_cooldown", "valid_maximum_saved_cooldown", "valid_event_only_runtime_snapshot",
    "reject_excessive_cooldown", "reject_negative_cooldown", "reject_nan_cooldown",
    "reject_infinite_cooldown", "reject_negative_cost", "reject_nan_cost", "reject_infinite_cost",
    "reject_null_effect_list", "reject_nan_effect_value", "reject_negative_effect_value",
    "reject_unsupported_effect_type", "reject_negative_damage_radius", "reject_infinite_effect_offset"})


def classify_configuration_result(native_exit, positive, negative):
    lines = positive.splitlines()
    return native_exit == 0 and not negative and len(lines) == len(CONFIG_OBSERVATIONS) and set(lines) == {name + "=PASS" for name in CONFIG_OBSERVATIONS}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--archive-sha256", required=True)
    parser.add_argument("--editor", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--configuration-matrix", action="store_true")
    parser.add_argument("--cold-save-source", type=Path)
    parser.add_argument("--cold-source-receipt", type=Path)
    parser.add_argument("--cold-scene")
    parser.add_argument("--settle-editor-startup", action="store_true", help="Private QA: drain startup callbacks before authoring/Play")
    parser.add_argument("--fresh-script-cache", action="store_true", help="Preserve and rebuild copied asset/script databases")
    parser.add_argument("--import-receipt", type=Path, help="Reuse a previously native-imported exact archive template")
    parser.add_argument("--scenario", choices=("shadow", "wired"), required=True)
    parser.add_argument("--domain-reload", choices=("on", "off"), required=True)
    parser.add_argument("--max-seconds", type=int, default=600)
    args = parser.parse_args()
    cold = args.cold_save_source is not None
    if args.configuration_matrix and (cold or args.scenario != "wired"):
        raise ValueError("Configuration matrix is a separate wired API test")
    if cold:
        if args.domain_reload != "off" or args.scenario != "wired" or not args.cold_source_receipt or not args.cold_scene:
            raise ValueError("Cold process QA currently requires wired/reload-off and exact prior receipt/scene")
        prior = json.loads(args.cold_source_receipt.read_text())
        if prior.get("status") != "PASS" or prior.get("native_exit_code") != 0 or not prior.get("native_wired_workflow_passed") or prior.get("exact_packaged_scripts") != 55 or prior.get("modified_original_files"):
            raise ValueError("Successful prior native workflow required")
        if args.cold_save_source.is_symlink() or not args.cold_save_source.is_file():
            raise ValueError("Immutable existing save file required")
        if not args.cold_scene.startswith("Assets/") or ".." in Path(args.cold_scene).parts or not (args.template / args.cold_scene).is_file():
            raise ValueError("Exact existing private scene required")
    elif args.cold_source_receipt or args.cold_scene:
        raise ValueError("Cold options require an explicit save source")
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
    save_hash = digest(args.cold_save_source) if cold else None
    if cold: shutil.copyfile(args.cold_save_source, args.output / "previous-process-save.json")
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
    import_before = protected_files(project)
    (args.output / "pre-import-protected-before.json").write_text(json.dumps(import_before, indent=2))
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
    import_after = protected_files(project)
    import_changed = [name for name, old in import_before.items() if import_after.get(name) != old]
    if import_changed:
        # Do not stage probes or continue gameplay after observed customer-data loss.
        receipt = {"status": "FAIL", "failure_stage": "bootstrap_customer_preservation",
            "actual_unity_editor_executed": True, "native_exit_code": None,
            "import_protected_files": len(import_before),
            "modified_original_files": import_changed,
            "native_wired_workflow_passed": False, "expected_shadow_control_rejected": False,
            "commercial_release_approved": False}
        (args.output / "RESULT.json").write_text(json.dumps(receipt, indent=2))
        print(json.dumps(receipt), flush=True)
        return 1
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
    # Compile the prepared GUI observer without running its normal-Editor entry point.
    # Graphical execution remains gated by the owner's software-terms consent.
    gui_observer = code.parent / "EditorUsability/InstallerInteractionProbe.cs"
    if gui_observer.is_file():
        shutil.copyfile(gui_observer, fixtures / "Editor/InstallerInteractionProbe.cs")
    before = protected_files(project)
    (args.output / "protected-before.json").write_text(json.dumps(before, indent=2))
    env = os.environ.copy()
    env.update(HPR_WORKFLOW_RECEIPT_ROOT=str(args.output), HPR_WORKFLOW_SCENARIO=args.scenario)
    if cold:
        env.update(HPR_WORKFLOW_COLD_SAVE=str(args.output / "previous-process-save.json"), HPR_WORKFLOW_COLD_SCENE=args.cold_scene)
    command = [str(args.editor), "-batchmode", "-nographics", "-projectPath", str(project),
               "-executeMethod", "HprAbilityConfigurationValidator.RunAfterStartup" if args.configuration_matrix else ("HprColdRestartValidator.RunAfterStartup" if cold else ("HprExistingGameInputHealthValidator.RunAfterStartup" if args.settle_editor_startup else "HprExistingGameInputHealthValidator.Run")),
               "-logFile", str(args.output / "unity.log")]
    (args.output / "launch.json").write_text(json.dumps({"command": command, "started_epoch": started,
        "scenario": args.scenario, "domain_reload": args.domain_reload, "settled_editor_startup": args.settle_editor_startup,
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
    negative = args.output / ("native-config-failure.txt" if args.configuration_matrix else ("native-cold-failure.txt" if cold else "native-failure.txt"))
    positive = args.output / ("native-config-result.txt" if args.configuration_matrix else ("native-cold-result.txt" if cold else "native-result.txt"))
    valid_negative, valid_positive = classify_native_result(args.scenario, native_exit,
        positive.read_text() if positive.is_file() else "",
        negative.read_text() if negative.is_file() else "")
    if cold:
        valid_negative = False
        valid_positive = classify_cold_result(native_exit, positive.read_text() if positive.is_file() else "", negative.read_text() if negative.is_file() else "")
        if digest(args.cold_save_source) != save_hash or digest(args.output / "previous-process-save.json") != save_hash:
            changed.append("external_source_save")
    if args.configuration_matrix:
        valid_negative = False
        valid_positive = classify_configuration_result(native_exit, positive.read_text() if positive.is_file() else "", negative.read_text() if negative.is_file() else "")
    status = "PASS" if (valid_negative or valid_positive) and not changed and not vendor_changed and vendor_count == 55 else "FAIL"
    receipt = {"status": status, "native_exit_code": native_exit, "scenario": args.scenario,
        "domain_reload": args.domain_reload, "workflow_kind": "configuration_matrix" if args.configuration_matrix else ("cold_restart" if cold else "same_process"),
        "configuration_matrix_passed": bool(args.configuration_matrix and valid_positive),
        "cold_restart_workflow_passed": bool(cold and valid_positive), "source_save_sha256": save_hash,
        "duration_seconds": round(time.time() - started, 1),
        "import_protected_files": len(import_before), "modified_import_files": import_changed,
        "protected_files": len(before), "modified_original_files": changed,
        "exact_packaged_scripts": vendor_count, "vendor_script_mismatches": vendor_changed,
        "expected_shadow_control_rejected": valid_negative, "native_wired_workflow_passed": bool(not cold and not args.configuration_matrix and valid_positive),
        "actual_unity_editor_executed": True, "physical_keyboard_tested": False,
        "external_buyer_tested": False, "commercial_release_approved": False}
    (args.output / "RESULT.json").write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt), flush=True)
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
