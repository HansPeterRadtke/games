#!/usr/bin/env python3
"""Retry CPU admission for one immutable Unity URP/new-input-only acceptance.

This is a broker-owned, explicitly started, local QA worker. It does not
preempt other jobs, alter project owner files, publish anything, or modify
the original frozen archive. CPU availability is measured, not guessed
from a nominal logical CPU reservation.

While host CPU is overloaded it only samples admission (no RAM/CPU lease).
When two consecutive samples are acceptable, it uses the central Raspi
resource broker's secure lease before executing *one new disposable* Unity
project. Technical failures and timeouts stop for inspection: an uncertain
partially imported project is NEVER silently reused or overwritten.

This script is not automatically installed as a timer or service. Its caller
may explicitly launch it through /data/bin/resource-broker-job start.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import signal
from pathlib import Path
import shutil
import subprocess
import sys
import time

from unity_cpu_preflight import evaluate_capacity, sample_live


EXPECTED_ARCHIVE_SHA256 = "23699aea358d427f6d03b4fc05f45583e1afb51e34bb439062639b70c09c3ffe"
DEFAULT_ARCHIVE = Path("/data/var/marketplace-account-setup/hpr-unity-internal-selected-installer-20261101/internal-not-published.unitypackage")
DEFAULT_FIXTURE = Path("/data/tmp/hpr-caltask33-20261101-0903/combined-urp-new-input-focused-v14")
DEFAULT_EDITOR = Path("/data/apps/Unity/Hub/Editor/6000.6.7f1/Editor/Unity")
DEFAULT_QA = Path("/data/src/worktrees/unity-customer-integrity-20261101/unity/tools/release/gameplay_suite/qa")
DEFAULT_ROOT = Path("/data/var/marketplace-account-setup/hpr-unity-urp-broker-retry-20261102")
DEFAULT_OWNER = "unity-commercial/qa-urp-exact-20261102"
REQUIRED_FILES = (
    "ProjectSettings/ProjectVersion.txt",
    "ProjectSettings/GraphicsSettings.asset",
    "ProjectSettings/ProjectSettings.asset",
    "Packages/manifest.json",
    "Assets/HprPrivateUrpQA/HprTestUrp.asset",
)
OPTIONAL_ASSETS = (
    "Assets/HprPrivateUrpQA.meta",
    "Assets/UniversalRenderPipelineGlobalSettings.asset",
    "Assets/UniversalRenderPipelineGlobalSettings.asset.meta",
    "Assets/DefaultVolumeProfile.asset",
    "Assets/DefaultVolumeProfile.asset.meta",
)
UNITY_QA_FILES = (
    ("HprCombinedUrpInputPlaymodeValidator.cs", "Assets/Editor/HprCombinedUrpInputPlaymodeValidator.cs"),
    ("HprSuiteInputGameplayProbe.cs", "Assets/HprInputQA/HprSuiteInputGameplayProbe.cs"),
)


def utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def admission_snapshot(cpu_count: int, one_min_load: float, pressure_percent: float) -> dict:
    result = evaluate_capacity(cpu_count, one_min_load, pressure_percent,
                               max_load_per_cpu=1.35, max_pressure_percent=40.0)
    return {
        "decision": "can_request_lease" if result["status"] == "admit" else "wait_for_cpu",
        "sample_utc": utc_now(),
        "available_cpu_count": cpu_count,
        "load_per_cpu": result["load_per_cpu"],
        "cpu_psi_some_avg10_percent": result["cpu_psi_some_avg10_percent"],
        "reasons": result["reasons"],
        "cpu_reservations_made": 0,
    }


def should_attempt(recent: list[dict], required_consecutive: int = 2) -> bool:
    if required_consecutive < 1:
        raise ValueError("Consecutive admission threshold must be positive")
    return len(recent) >= required_consecutive and all(
        item.get("decision") == "can_request_lease"
        for item in recent[-required_consecutive:]
    )


def verify_archive(archive: Path, expected_sha: str = EXPECTED_ARCHIVE_SHA256) -> str:
    if not archive.is_file() or archive.is_symlink():
        raise FileNotFoundError("Immutable Unity buyer archive is missing or unsafe")
    if len(expected_sha) != 64 or any(c not in "0123456789abcdef" for c in expected_sha):
        raise ValueError("Invalid approved archive SHA-256")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != expected_sha:
        raise ValueError("Archive SHA-256 no longer matches the frozen release")
    return digest


def _check_safe_tree(root: Path) -> None:
    if root.is_symlink():
        raise ValueError("Refusing to use symlinked source folder")
    for item in root.rglob("*"):
        if item.is_symlink():
            raise ValueError("Refusing symlinked existing URP fixture: " + str(item))


def prepare_project(fixture: Path, output: Path) -> dict:
    """Copy only source settings and URP assets, *never* existing Library caches."""
    if not fixture.is_dir() or fixture.is_symlink():
        raise ValueError("The original known URP fixture is unavailable")
    if output.exists() or output.is_symlink():
        raise FileExistsError("A disposable Unity project already exists: " + str(output))
    src = Path(fixture)
    for name in REQUIRED_FILES:
        if (src / name).is_symlink():
            raise ValueError("Refusing symlinked required URP source file: " + name)
        if not (src / name).is_file():
            raise FileNotFoundError("Required URP fixture file unavailable: " + name)
    for name in ("ProjectSettings", "Packages", "Assets/HprPrivateUrpQA"):
        _check_safe_tree(src / name)
    version = (src / "ProjectSettings/ProjectVersion.txt").read_text()
    if "6000.6.7f1" not in version:
        raise ValueError("This QA uses exactly the previously installed Unity 6.6 Editor")
    settings = (src / "ProjectSettings/ProjectSettings.asset").read_text()
    if "activeInputHandler: 1" not in settings:
        raise ValueError("Known fixture must require the modern Input System only")
    packages = json.loads((src / "Packages/manifest.json").read_text())
    deps = packages.get("dependencies", {})
    if deps.get("com.unity.render-pipelines.universal") != "17.6.0" or \
            deps.get("com.unity.inputsystem") != "1.20.1":
        raise ValueError("Expected pinned URP and modern input versions")

    output.mkdir(parents=True, mode=0o700)
    shutil.copytree(src / "ProjectSettings", output / "ProjectSettings")
    shutil.copytree(src / "Packages", output / "Packages")
    (output / "Assets").mkdir()
    shutil.copytree(src / "Assets/HprPrivateUrpQA", output / "Assets/HprPrivateUrpQA")
    for name in OPTIONAL_ASSETS:
        f = src / name
        if f.exists():
            if f.is_symlink() or not f.is_file():
                raise ValueError("Unsafe optional URP source file: " + name)
            dest = output / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dest)
    if (output / "Library").exists() or (output / "Assets/HPRGameplaySuite").exists():
        raise AssertionError("An existing Library or vendor package leaked into the test")

    entries = {str(p.relative_to(output)):
               hashlib.sha256(p.read_bytes()).hexdigest()
               for p in output.rglob("*") if p.is_file()}
    return {"original_file_count": len(entries),
            "original_files": entries,
            "unity_version": "6000.6.7f1",
            "urp_version": "17.6.0",
            "inputsystem_version": "1.20.1",
            "original_fixture_unchanged": True}


def atomic_status(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.is_symlink():
        raise ValueError("Refusing symlinked status location")
    temporary = path.with_suffix(".tmp")
    if temporary.exists() or temporary.is_symlink():
        raise FileExistsError("Previous partial status write requires inspection")
    payload = dict(data, updated_utc=utc_now())
    descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            if temporary.exists():
                temporary.unlink()
        except OSError:
            pass
        raise


def original_files_integrity(project: Path, baseline: dict) -> list[str]:
    return sorted(name for name, digest in baseline.items()
                  if not (project / name).is_file() or
                  hashlib.sha256((project / name).read_bytes()).hexdigest() != digest)


def _live_owned_process_group_members(group_id: int) -> list[int]:
    """Inspect only the process group we explicitly created for this Editor.

    Zombie members are not executing work and may await init reaping. We do
    not signal any unrelated PID and make no claim to detect descendants
    that intentionally create a new session outside this group's control.
    """
    sampled = subprocess.run(["ps", "-eo", "pid=,pgid=,stat="],
                             capture_output=True, text=True, timeout=8, check=True)
    members = []
    for line in sampled.stdout.splitlines():
        fields = line.split()
        if len(fields) < 3:
            continue
        try:
            pid, pgid = int(fields[0]), int(fields[1])
        except ValueError:
            continue
        if pgid == group_id and not fields[2].startswith("Z"):
            members.append(pid)
    return members


def _terminate_owned_unity_group(process: subprocess.Popen, *, grace_seconds: float = 3.0) -> bool:
    """Terminate only our own new Unity process session and compiler children."""
    if process.pid <= 0:
        raise ValueError("Invalid private Unity process identifier")
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=grace_seconds)
        except subprocess.TimeoutExpired:
            pass
        # Direct Editor exit does not imply its compiler grandchildren exited.
        time.sleep(0.15)
        if not _live_owned_process_group_members(process.pid):
            return True
    return not _live_owned_process_group_members(process.pid)


def run_unity(editor: Path, project: Path, log: Path, *, import_package: Path | None = None,
              execute_method: str | None = None, timeout: int = 1800,
              extra_env: dict[str, str] | None = None) -> dict:
    if log.exists():
        raise FileExistsError("Refusing to overwrite an existing Unity Editor log")
    args = [str(editor), "-batchmode", "-nographics",
            "-projectPath", str(project)]
    if import_package is not None:
        args += ["-importPackage", str(import_package)]
    if execute_method is not None:
        args += ["-executeMethod", execute_method]
    else:
        args += ["-quit"]
    args += ["-logFile", str(log)]
    env = os.environ.copy()
    env.update(HOME="/home/hans", USER="hans", LOGNAME="hans",
               DISPLAY=":1", XAUTHORITY="/home/hans/.Xauthority",
               XDG_RUNTIME_DIR="/run/user/1000",
               DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/1000/bus")
    env.update(extra_env or {})
    started = time.monotonic()
    # A fresh process session gives this worker a unique group identity.
    # Timeout termination is restricted to this spawned Editor + children.
    process = subprocess.Popen(args, env=env, stdin=subprocess.DEVNULL,
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, start_new_session=True)
    timed_out = False
    try:
        code = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        code = 124
    orphaned = False
    if timed_out:
        group_terminated = _terminate_owned_unity_group(process)
    else:
        # A zero exit does not mean Bee/ILPP grandchildren have stopped.
        # Reap only the process group this worker explicitly created; never
        # signal an unmanaged PID or another agent's Editor or compiler.
        orphaned = bool(_live_owned_process_group_members(process.pid))
        if orphaned:
            group_terminated = _terminate_owned_unity_group(process)
            code = 125  # Editor exited but left an owned compiler alive.
        else:
            group_terminated = True
    return {"exit_code": code, "seconds": round(time.monotonic() - started, 2),
            "log_path": str(log), "log_bytes": log.stat().st_size if log.is_file() else 0,
            "timeout_seconds": timeout, "process_group_terminated": group_terminated,
            "orphaned_owned_compiler_detected": orphaned,
            "timeout_killed_only_own_process_group": timed_out and group_terminated,
            "phase_success": code == 0 and group_terminated}


def no_other_unity() -> bool:
    """Use comm, not shell command arguments that merely mention Unity paths."""
    command = subprocess.run(["ps", "-eo", "comm"], capture_output=True, text=True,
                             timeout=5, check=True)
    return not any(line.strip() in ("Unity", "Unity Main Thre")
                   for line in command.stdout.splitlines())


def _read_broker_api():
    # Import the installed owner's original broker code. No fork/alternate
    # control path and no unregistered process actions.
    sys.path.insert(0, "/data/infra/libexec")
    import resource_broker_lifecycle
    return resource_broker_lifecycle


def _record_wait(root: Path, data: dict) -> None:
    atomic_status(root / "status.json", data)


def run_attempt(args, attempt_number: int, lease_api, lease) -> dict:
    """At most one side-effectful attempt per unique disposable project.

    Do not retry a timed-out/partially imported project. A subsequent
    attempt, if approved, must get another unique project and review.
    """
    run_root = args.output_root / ("attempt-%03d" % attempt_number)
    if run_root.exists() or run_root.is_symlink():
        raise FileExistsError("Refusing to re-run an existing Unity QA attempt")
    run_root.mkdir(parents=True, mode=0o700)
    project = run_root / "unity-project"
    before = prepare_project(args.fixture, project)
    atomic_status(run_root / "source-baseline.json", before)

    phase = run_unity(args.editor, project, run_root / "prepare.unity.log", timeout=1800)
    atomic_status(run_root / "prepare-result.json", phase)
    if not phase["phase_success"]:
        return {"status": "failed_prepare_requires_review", "attempt": attempt_number, "phase": phase}

    # Unity may legitimately initialize project settings before import:
    # snapshot only *after* the first independent package-free Editor run.
    files = {str(p.relative_to(project)): hashlib.sha256(p.read_bytes()).hexdigest()
             for folder in ("Assets", "Packages", "ProjectSettings")
             for p in (project / folder).rglob("*") if p.is_file()}
    atomic_status(run_root / "pre-import-baseline.json", {"original_files": files})
    phase = run_unity(args.editor, project, run_root / "import.unity.log",
                      import_package=args.archive, timeout=1800)
    changed = original_files_integrity(project, files)
    phase.update(original_customer_files=len(files),
                 changed_existing_files=changed,
                 installer_in_project=(project / "Assets/HPRGameplaySuite/Editor/HprSelectedAbilityInstaller.cs").is_file())
    atomic_status(run_root / "import-result.json", phase)
    if not phase["phase_success"] or changed or not phase["installer_in_project"]:
        return {"status": "failed_import_requires_review", "attempt": attempt_number, "phase": phase}

    # Only QA-scoped files are added to this new scratch project.
    for name, relative in UNITY_QA_FILES:
        source = args.qa / name
        dest = project / relative
        if not source.is_file() or source.is_symlink():
            raise FileNotFoundError("Missing private Unity test validator: " + name)
        if dest.exists() or dest.is_symlink():
            raise FileExistsError("Private QA script already exists unexpectedly")
        dest.parent.mkdir(exist_ok=True, parents=True)
        shutil.copy2(source, dest)
    input_receipt = run_root / "new-input-gameplay.txt"
    combined_receipt = run_root / "combined-urp-input.txt"
    phase = run_unity(
        args.editor, project, run_root / "combined-playmode.unity.log",
        execute_method="HprCombinedUrpInputPlaymodeValidator.Run", timeout=1500,
        extra_env={
            "HPR_NEW_INPUT_GAME_UPDATE_RECEIPT": str(input_receipt),
            "HPR_COMBINED_URP_INPUT_RECEIPT": str(combined_receipt),
        })
    if not phase["phase_success"] or not input_receipt.is_file() or not combined_receipt.is_file():
        phase["qa_receipt_missing_or_editor_failed"] = True
        atomic_status(run_root / "playmode-result.json", phase)
        return {"status": "failed_playmode_requires_review", "attempt": attempt_number, "phase": phase}
    gameplay_text = input_receipt.read_text(encoding="utf-8")
    combined_text = combined_receipt.read_text(encoding="utf-8")
    required = ("new_input_only_real_game_update=PASS", "key_release=PASS")
    if not all(line in gameplay_text for line in required) or \
            "active_urp_17_pipeline=PASS" not in combined_text:
        phase["qa_receipt_incomplete"] = True
        atomic_status(run_root / "playmode-result.json", phase)
        return {"status": "failed_playmode_requires_review", "attempt": attempt_number, "phase": phase}

    phase["real_editor_urp_new_input_gameplay_accepted"] = True
    phase["originals_remained_unmodified_after_install"] = not changed
    atomic_status(run_root / "playmode-result.json", phase)
    return {"status": "complete_verified", "attempt": attempt_number, "phase": phase}


def run_worker(args) -> int:
    if args.output_root.exists() or args.output_root.is_symlink():
        # Prevent restarting an old job and claiming progress from its effects.
        raise FileExistsError("The broker-owned worker root already exists; inspect first")
    if args.fixture == args.output_root:
        raise ValueError("The output must be separate from the source fixture")
    verify_archive(args.archive)
    if not args.editor.is_file() or not os.access(args.editor, os.X_OK):
        raise FileNotFoundError("Pinned Unity Editor is unavailable")
    args.output_root.mkdir(parents=True, mode=0o700)
    atomic_status(args.output_root / "status.json",
                  {"phase": "initialized", "attempts_started": 0, "owner": args.owner,
                   "archive_sha256": EXPECTED_ARCHIVE_SHA256,
                   "no_other_jobs_preempted": True, "broker_lease_held_while_waiting": False})
    broker = _read_broker_api()
    started = time.monotonic()
    admissions: list[dict] = []
    checks = 0
    while time.monotonic() - started < args.max_wait_seconds:
        checks += 1
        sample = sample_live()
        decision = admission_snapshot(sample["cpu_count"],
                                      sample["one_min_load"], sample["pressure_percent"])
        if not no_other_unity():
            decision["decision"] = "wait_for_cpu"
            decision["reasons"].append("A Unity Editor process is already active")
        admissions.append(decision)
        admissions = admissions[-args.required_samples:]
        phase = {"phase": "waiting_for_cpu_and_broker",
                 "attempts_started": 0, "samples_checked": checks,
                 "owner": args.owner, "latest": decision,
                 "archive_sha256": EXPECTED_ARCHIVE_SHA256,
                 "no_other_jobs_preempted": True,
                 "broker_lease_held_while_waiting": False}
        _record_wait(args.output_root, phase)

        if should_attempt(admissions, args.required_samples):
            # A stale or degraded hardware observation is not a resource
            # grant. Keep waiting and inspect a new independent observation.
            # Broker authorization/resource denials are NOT retried or evaded.
            try:
                state = broker.analyze_current_machine(refresh=True)
                monitor = state.get("monitor") or {}
                health = (monitor.get("capacity") or {}).get("status")
            except Exception as exc:
                _record_wait(args.output_root, dict(phase, phase="broker_health_unavailable",
                              broker_error_type=type(exc).__name__))
                admissions.clear()
                time.sleep(args.poll_seconds)
                continue
            if health != "ok" or monitor.get("snapshot_status") not in (None, "ok"):
                _record_wait(args.output_root, dict(phase, phase="broker_health_degraded",
                              broker_health=str(health)))
                admissions.clear()
                time.sleep(args.poll_seconds)
                continue
            try:
                grant = broker.reserve_resources(
                    "nitro", args.owner, 6.0, 0.0, 2.0, 7200, secure=True)
            except Exception as exc:
                # No rewriting of a capacity/authorization denial into an
                # alternate owner or endpoint, and no blind repeat of an
                # uncertain secure reservation request.
                _record_wait(args.output_root, dict(phase="broker_grant_unavailable",
                              attempts_started=0, broker_error_type=type(exc).__name__,
                              broker_error=str(exc)[:180]))
                return 4
            if not (isinstance(grant, tuple) and len(grant) == 2):
                _record_wait(args.output_root, dict(phase, phase="invalid_secure_lease"))
                return 4
            request_id, secret = grant
            private = args.output_root / "lease-private.json"
            result_code = 6
            attempted = False
            try:
                # Credential persistence is itself a fallible operation.
                # Begin the release-protected block BEFORE writing any file
                # so even a failed private write never leaks a real lease.
                atomic_status(private,
                              {"request_id": request_id, "control_token": secret,
                               "owner": args.owner, "ttl_seconds": 7200})
                _record_wait(args.output_root,
                             dict(phase, phase="running_unique_disposable_attempt",
                                  attempts_started=1, broker_lease_acquired=True))
                attempted = True
                result = run_attempt(args, 1, broker, grant)
                _record_wait(args.output_root, dict(result, owner=args.owner,
                                                    archive_sha256=EXPECTED_ARCHIVE_SHA256))
                result_code = 0 if result["status"] == "complete_verified" else 5
            except Exception as exc:
                # Unknown effects are NOT replayed. Preserve the original
                # scratch project, logs and explicit terminal checkpoint.
                _record_wait(args.output_root, {
                    "phase": "failed_attempt_requires_review",
                    "attempts_started": 1 if attempted else 0,
                    "broker_grant_acquired": True,
                    "error_type": type(exc).__name__,
                    "owner": args.owner,
                    "archive_sha256": EXPECTED_ARCHIVE_SHA256,
                    "no_automatic_retry_of_uncertain_effects": True,
                })
                result_code = 6
            finally:
                try:
                    release_ok = broker.release_resources(
                        args.owner, request_id, control_token=secret)
                except Exception:
                    release_ok = False
                if release_ok:
                    if private.is_file():
                        private.unlink()
                else:
                    # Never claim complete if the real secure broker lease
                    # release was denied/unknown. Keep the credential private
                    # for explicit owner reconciliation or ledger TTL expiry.
                    token_preserved = private.is_file()
                    if not token_preserved:
                        try:
                            atomic_status(private, {
                                "request_id": request_id, "control_token": secret,
                                "owner": args.owner, "ttl_seconds": 7200})
                            token_preserved = True
                        except Exception:
                            pass
                    _record_wait(args.output_root, {
                        "phase": "broker_lease_release_uncertain",
                        "owner": args.owner,
                        "attempts_started": 1 if attempted else 0,
                        "secure_credential_persisted": token_preserved,
                        "lease_may_remain_active_until_ttl": True,
                        "do_not_create_another_lease": True,
                        "archive_sha256": EXPECTED_ARCHIVE_SHA256,
                    })
                    (args.output_root / "lease-release-pending.txt").write_text(
                        "Secure broker lease release not verified. Inspect the recorded "
                        "private request ID and owner capability or allow TTL expiry. "
                        "Do not substitute another owner's token.\n")
            return result_code if release_ok else 4
        time.sleep(args.poll_seconds)
    _record_wait(args.output_root,
                 {"phase": "deferred_cpu_overload_wait_window_exhausted",
                  "samples_checked": checks, "attempts_started": 0,
                  "no_unity_process_started": True,
                  "no_broker_reservation_held": True,
                  "archive_sha256": EXPECTED_ARCHIVE_SHA256})
    return 2


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode", choices=("report", "retry"), default="report")
    p.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    p.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    p.add_argument("--editor", type=Path, default=DEFAULT_EDITOR)
    p.add_argument("--qa", type=Path, default=DEFAULT_QA)
    p.add_argument("--output-root", type=Path, default=DEFAULT_ROOT)
    p.add_argument("--owner", type=str, default=DEFAULT_OWNER)
    p.add_argument("--max-wait-seconds", type=int, default=43200)
    p.add_argument("--poll-seconds", type=int, default=120)
    p.add_argument("--required-samples", type=int, default=2)
    args = p.parse_args()
    if args.max_wait_seconds < 120 or args.max_wait_seconds > 86400:
        p.error("Wait bound must be between two minutes and one day")
    if args.poll_seconds < 20 or args.poll_seconds > 1800:
        p.error("Poll interval must be between twenty seconds and half an hour")
    if not 1 <= args.required_samples <= 5:
        p.error("Invalid number of consecutive observations")
    return args


def main() -> int:
    args = parse_args()
    try:
        if args.mode == "report":
            verify_archive(args.archive)
            sample = sample_live()
            answer = admission_snapshot(
                sample["cpu_count"], sample["one_min_load"], sample["pressure_percent"])
            answer["archive_sha256_verified"] = True
            answer["any_other_unity_editor_active"] = not no_other_unity()
            answer["action"] = "read_only_report_no_reservation_or_process_launch"
            print(json.dumps(answer, sort_keys=True))
            return 0
        return run_worker(args)
    except Exception as exc:
        # Do not print file contents, credentials or full dynamic exception
        # payloads. Preserve a clear failure report rather than pretending
        # the Unity Editor or lease launched.
        print(json.dumps({"status": "requires_manual_review",
                          "error_type": type(exc).__name__,
                          "error": str(exc)[:220],
                          "owner": args.owner}))
        return 6


if __name__ == "__main__":
    sys.exit(main())
