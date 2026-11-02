#!/usr/bin/env python3
"""Broker-admitted, serial customer-asset QA AFTER the separate URP worker.

This local owner-approved QA worker is launched ONLY through the existing
Nitro resource-broker-job supervisor. It waits for a completed *upstream*
URP broker job and genuine CPU capacity without holding a resource lease.

No other owner's job is killed or reprioritized. The upstream worker and all
prior disposable projects/logs remain untouched. The two existing PRIVATE
customer project copies are one-time fixtures; unknown/partial effects are
never replayed in place. No vendor, marketplace or account writes occur.

After secure broker reservation, the worker runs three real Unity Editor
checks serially: native HPR Stats scene build, Stats Play mode, and the
independent dirty-customer-asset copy. The latter can proceed independently
if the first scene build fails, provided the Editor's own process children
were terminated and the separate dirty test's baseline is unchanged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from unity_urp_broker_retry import (
    _read_broker_api, _terminate_owned_unity_group,
    _live_owned_process_group_members, admission_snapshot,
    atomic_status, no_other_unity, sample_live, should_attempt, utc_now,
)

DEFAULT_ROOT = Path("/data/var/marketplace-account-setup/hpr-unity-customer-followup-20261102")
DEFAULT_UPSTREAM = Path("/data/var/marketplace-account-setup/hpr-unity-urp-broker-retry-20261102-v3")
DEFAULT_UPSTREAM_ID = Path(
    "/data/var/marketplace-account-setup/"
    "hpr-unity-internal-selected-installer-20261101/qa-evidence/"
    "urp-upstream-public-id-20261102.json"
)
DEFAULT_NATIVE = Path("/data/tmp/hpr-unity-native-stats-customer-20261102")
DEFAULT_DIRTY = Path("/data/tmp/hpr-unity-dirty-asset-save-qa-20261102")
DEFAULT_EDITOR = Path("/data/apps/Unity/Hub/Editor/6000.6.7f1/Editor/Unity")
DEFAULT_OWNER = "unity-commercial/qa-customer-followup-20261102"
STAGES = (
    {
        "name": "stats_build",
        "method": "HprCustomerStatsAdapterValidator.BuildNewCustomerScene",
        "quit": True,
        "fixture": "native",
        "receipt_key": "HPR_STATS_ADAPTER_RECEIPT",
        "expected_receipt": ("stats_source_inspector_reference_survives_scene_reload=PASS",
                             "original_customer_scene_prefab_script_settings_ability_unchanged=PASS"),
        "new_paths": (
            "Assets/ExternalCustomerGame/IntegrationDemos/CustomerActorStatsIntegrated.unity",
            "Assets/ExternalCustomerGame/IntegrationDemos/CustomerActorStatsIntegrated.unity.meta",
            "Assets/Editor/HprCustomerStatsAdapterValidator.cs.meta",
        ),
    },
    {
        "name": "stats_playmode",
        "method": "HprCustomerStatsAdapterValidator.RunPlaymode",
        "quit": False,
        "fixture": "native",
        "receipt_key": "HPR_STATS_ADAPTER_PLAY_RECEIPT",
        "expected_receipt": ("healing_restored_twenty_health=PASS",
                             "stamina_consumed_twenty=PASS",
                             "ability_cooldown_blocked_second_cast=PASS"),
        "new_paths": (),
    },
    {
        "name": "dirty_asset_copy",
        "method": "HprUnrelatedDirtyAssetValidator.Run",
        "quit": True,
        "fixture": "dirty",
        "receipt_key": "HPR_DIRTY_ASSET_ISOLATION_RECEIPT",
        "expected_receipt": ("unrelated_customer_asset_saved_to_disk=False",
                             "original_scene_mutated=False",
                             "vendor_original_mutated=False",
                             "customer_asset_metadata_mutated=False",
                             "unrelated_customer_edit_remains_unsaved=True"),
        "new_paths": (
            "Assets/ExternalCustomerGame/IntegrationDemos/ScopedCopyOnly.asset",
            "Assets/ExternalCustomerGame/IntegrationDemos/ScopedCopyOnly.asset.meta",
            "Assets/ExternalCustomerGame/IntegrationDemos/ScopedCopyOnly__HPR_RepairEffect.asset",
            "Assets/ExternalCustomerGame/IntegrationDemos/ScopedCopyOnly__HPR_RepairEffect.asset.meta",
            "Assets/Editor/HprUnrelatedDirtyAssetValidator.cs.meta",
        ),
    },
)
PREEXISTING_PROJECT_SOURCES = {
    "native": {
        "Assets/HPRGameplaySuite/Integration/HprSuiteIntegration.cs":
            "af109fbfa0d9a23f2962b1bec06636b339a3f86b56fef686317ce184dcb94076",
        "Assets/HPRGameplaySuite/Editor/HprSelectedAbilityInstaller.cs":
            "be1d7835cfd7ae1e79b7ef4e475856c73270598491921d074e487c194bf11bff",
        "Assets/HPRGameplaySuite/Integration/HprSuiteIntegration.cs.meta":
            "252e3d3930cefe3bf3e7a774e4747a2d81c9b6f232167cb09e5f5e45df10af4c",
        "Assets/HPRGameplaySuite/Editor/HprSelectedAbilityInstaller.cs.meta":
            "34a891602fdd190d5f247b760bd3d3a06bfed573154c213d7be52742683abb6c",
    },
    "dirty": {
        "Assets/HPRGameplaySuite/Editor/HprSuiteIntegrationGuide.cs":
            "7ce0bb2f57635f0204fc8c5a1927c97e8ae3b3cb8cce80d24227f91a9e897464",
        "Assets/HPRGameplaySuite/Editor/HprSuiteIntegrationGuide.cs.meta":
            "4781cf717ec3fac5aea4890b69b34008f17e8e642e9af2fd0b1929a77961527a",
    },
}
UPSTREAM_DONE = {
    "complete_verified", "failed_import_requires_review",
    "failed_prepare_requires_review", "failed_playmode_requires_review",
}
UPSTREAM_DEFERRED = {
    "deferred_cpu_overload_wait_window_exhausted",
}
RECEIPT_BY_NAME = {
    "stats_build": "stats-build-receipt.txt",
    "stats_playmode": "stats-playmode-receipt.txt",
    "dirty_asset_copy": "dirty-asset-receipt.txt",
}


def upstream_gate(result: dict | None, broker_job: dict | None) -> str:
    """Return wait, ready, halt. Never infer a completed job from no PID."""
    if not isinstance(result, dict) or not isinstance(broker_job, dict):
        return "halt"
    if broker_job.get("reservation_id"):
        return "halt"
    status = broker_job.get("state")
    service = broker_job.get("systemd_active")
    if status in ("running", "starting", "frozen", "restarting") or service == "active":
        return "wait"
    if status not in ("stopped", "exited") or service not in ("inactive", "failed"):
        return "halt"
    if result.get("status") in UPSTREAM_DONE or result.get("phase") in UPSTREAM_DEFERRED:
        return "ready"
    return "halt"


def changed_originals(project: Path, digests: dict[str, str]) -> list[str]:
    return sorted(name for name, digest in digests.items()
                  if not (project / name).is_file()
                  or hashlib.sha256((project / name).read_bytes()).hexdigest() != digest)


def require_fresh_effect(receipt: Path, *, existing_effects: list[Path]) -> None:
    if receipt.exists() or receipt.is_symlink():
        raise FileExistsError("A previous QA receipt already exists: " + str(receipt))
    if any(path.exists() or path.is_symlink() for path in existing_effects):
        raise FileExistsError("A previous Unity QA effect exists; inspect before retry")


def validate_output_location(output: Path, native: Path, dirty: Path, upstream: Path) -> None:
    """Reject results nested inside any original, staged, or prior project.

    Existing source input directories may contain owner files; this worker
    never creates a log directory within or above those input roots.
    """
    output = Path(output).resolve(strict=False)
    for source in (Path(native), Path(dirty), Path(upstream)):
        source = source.resolve(strict=False)
        if output == source or output.is_relative_to(source) or source.is_relative_to(output):
            raise ValueError("Output root overlaps a protected project or upstream job")


def project_preflight(project: Path) -> bool:
    if project.exists() or project.is_symlink():
        raise FileExistsError("A disposable project already exists; never overwrite: " + str(project))
    return False


def stage_accepted(result: dict, receipt_text: str | None,
                   required_lines: list[str] | tuple[str, ...]) -> bool:
    return (isinstance(result, dict) and result.get("exit_code") == 0
            and result.get("phase_success") is True
            and isinstance(receipt_text, str)
            and all(line in receipt_text.splitlines() for line in required_lines))


def _upstream_public_id(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise FileNotFoundError("Upstream broker public ID not available")
    value = json.loads(path.read_text(encoding="utf-8"))
    identifier = value.get("job_id") if isinstance(value, dict) else None
    if not isinstance(identifier, str) or re.fullmatch(r"job_[a-f0-9]{24}", identifier) is None:
        raise ValueError("Invalid upstream broker ID")
    return identifier


def _upstream_status(args, public_id: str) -> tuple[dict, dict]:
    if not (args.upstream / "status.json").is_file():
        raise FileNotFoundError("Original URP result/status not found")
    saved = json.loads((args.upstream / "status.json").read_text(encoding="utf-8"))
    response = subprocess.run(
        ["/data/bin/resource-broker-job", "status", "--job-id", public_id],
        capture_output=True, text=True, timeout=20, check=True)
    current = json.loads(response.stdout)
    if current.get("id") != public_id:
        raise ValueError("Upstream status returned another owner's job")
    return saved, current


def _check_safe_staged_fixture(project: Path, digest_file: Path, source_files: dict) -> dict:
    if project.is_symlink() or not project.is_dir():
        raise ValueError("Expected isolated customer QA project")
    if not digest_file.is_file() or digest_file.is_symlink():
        raise ValueError("Expected unmodified customer SHA-256 baseline")
    original = json.loads(digest_file.read_text(encoding="utf-8"))
    digests = original.get("files") if isinstance(original, dict) else None
    if not isinstance(digests, dict) or len(digests) < 60:
        raise ValueError("Customer original-file baseline is incomplete")
    changed = changed_originals(project, digests)
    if changed:
        raise ValueError("Buyer original files changed before QA: " + ", ".join(changed[:8]))
    for path, expected_sha in source_files.items():
        physical = project / path
        if not physical.is_file() or physical.is_symlink() or \
                hashlib.sha256(physical.read_bytes()).hexdigest() != expected_sha:
            raise ValueError("Incorrect private Unity source overlay: " + path)
    return digests


def _scan_customer_project(project: Path) -> dict[str, str]:
    # The existing independent checker knows which files are NOT HPR vendor
    # assets; do not silently change its data preservation contract.
    from customer_integrity import snapshot_customer_project
    return snapshot_customer_project(project)


def _editor_command(editor: Path, project: Path, log: Path, stage: dict) -> list[str]:
    cmd = [str(editor), "-batchmode", "-nographics"]
    if stage["quit"]:
        cmd += ["-quit"]
    cmd += ["-projectPath", str(project), "-executeMethod", stage["method"], "-logFile", str(log)]
    return cmd


def _run_stage_editor(editor: Path, project: Path, stage: dict, log: Path,
                      receipt: Path, *, timeout_seconds: int) -> dict:
    from unity_urp_broker_retry import _terminate_owned_unity_group, _live_owned_process_group_members
    if log.exists() or receipt.exists():
        raise FileExistsError("Previous Editor test log or receipt exists; do not repeat")
    env = os.environ.copy()
    env.update(HOME="/home/hans", USER="hans", LOGNAME="hans",
               DISPLAY=":1", XAUTHORITY="/home/hans/.Xauthority",
               XDG_RUNTIME_DIR="/run/user/1000",
               DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/1000/bus")
    env[stage["receipt_key"]] = str(receipt)
    started = time.monotonic()
    cmd = _editor_command(editor, project, log, stage)
    process = subprocess.Popen(cmd, env=env, stdin=subprocess.DEVNULL,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               start_new_session=True)
    try:
        code = process.wait(timeout=timeout_seconds)
        timed_out = False
    except subprocess.TimeoutExpired:
        timed_out = True
        code = 124
    lingering = bool(_live_owned_process_group_members(process.pid))
    if timed_out or lingering:
        terminated = _terminate_owned_unity_group(process)
        if lingering and not timed_out:
            code = 125
    else:
        terminated = True
    return {
        "exit_code": code,
        "phase_success": code == 0 and terminated and not timed_out,
        "elapsed_seconds": round(time.monotonic() - started, 2),
        "log_path": str(log),
        "log_bytes": log.stat().st_size if log.is_file() else 0,
        "owned_process_group_terminated": terminated,
        "timeout_seconds": timeout_seconds,
    }


def _run_permitted_qa(args, state_root: Path) -> dict:
    fixture = {"native": (args.native, PREEXISTING_PROJECT_SOURCES["native"]),
               "dirty": (args.dirty, PREEXISTING_PROJECT_SOURCES["dirty"])}
    original = {}
    for kind, (root, sources) in fixture.items():
        project = root / "customer-project"
        originals = _check_safe_staged_fixture(project,
                    root / ("pre-editor-original-buyer-files.json"
                            if kind == "native" else "pre-editor-customer-baseline.json"), sources)
        original[kind] = originals

    results = []
    stats_built = False
    for stage in STAGES:
        if stage["name"] == "stats_playmode" and not stats_built:
            results.append({"name": "stats_playmode", "status": "skipped_due_to_failed_scene_build"})
            continue
        kind = stage["fixture"]
        project = fixture[kind][0] / "customer-project"
        log = state_root / (stage["name"] + ".unity.log")
        receipt = fixture[kind][0] / RECEIPT_BY_NAME[stage["name"]]
        # Check before launching (not after) to detect an effect made by
        # another agent since our first source audit.
        if stage["name"] in ("stats_build", "dirty_asset_copy"):
            targets = [project / path for path in stage["new_paths"]]
            require_fresh_effect(receipt, existing_effects=targets)
        else:
            if not (project / STAGES[0]["new_paths"][0]).is_file():
                raise ValueError("Stats customer scene missing after build")
            require_fresh_effect(receipt, existing_effects=[])
        atomic_status(state_root / (stage["name"] + "-started.json"), {
            "phase": "unity_editor_stage_started", "stage": stage["name"],
            "project": str(project), "owner": args.owner,
        })
        result = _run_stage_editor(args.editor, project, stage, log, receipt,
                                   timeout_seconds=args.editor_timeout_seconds)
        text = receipt.read_text(encoding="utf-8") if receipt.is_file() else None
        accepted = stage_accepted(result, text, stage["expected_receipt"])
        modified = changed_originals(project, original[kind])
        now = _scan_customer_project(project)
        newly_added = sorted(set(now) - set(original[kind]))
        if kind == "native":
            permitted = set(STAGES[0]["new_paths"])
        else:
            permitted = set(STAGES[2]["new_paths"])
        unexpected = sorted(set(newly_added) - permitted)
        record = {"name": stage["name"], "status": "PASS" if accepted and not modified and not unexpected
                  else "FAILED_REQUIRES_REVIEW", "editor": result,
                  "original_customer_files": len(original[kind]),
                  "modified_original_files": modified,
                  "new_customer_files": newly_added,
                  "unexpected_new_files": unexpected,
                  "expected_receipt_lines_verified": accepted}
        atomic_status(state_root / (stage["name"] + "-result.json"), record)
        results.append(record)
        if stage["name"] == "stats_build":
            stats_built = record["status"] == "PASS"
        # A timed-out Unity compile can leave a complex unknown Library and
        # external state. Never start another task until the child group has
        # been confirmed absent, and never re-run this same stage in place.
        if not result["owned_process_group_terminated"]:
            break
    complete = len(results) == len(STAGES) and all(
        record.get("status") == "PASS" for record in results)
    return {"status": "complete_verified" if complete else "partial_requires_review",
            "stages": results, "owner": args.owner, "archive_not_published": True}


def run_worker(args) -> int:
    validate_output_location(args.output_root, args.native, args.dirty, args.upstream)
    if args.output_root.exists() or args.output_root.is_symlink():
        raise FileExistsError("A prior customer follow-up project/checkpoint exists; inspect first")
    if not args.editor.is_file() or not os.access(args.editor, os.X_OK):
        raise FileNotFoundError("Pinned Unity Editor binary missing")
    identifier = _upstream_public_id(args.upstream_id_file)
    # Verify staged sources and buyer baselines BEFORE starting any broker
    # waiting job. Buyer project paths are intentionally NOT copied/recreated
    # when their own previous receipt is already uncertain.
    _check_safe_staged_fixture(args.native/"customer-project",
                               args.native/"pre-editor-original-buyer-files.json",
                               PREEXISTING_PROJECT_SOURCES["native"])
    _check_safe_staged_fixture(args.dirty/"customer-project",
                               args.dirty/"pre-editor-customer-baseline.json",
                               PREEXISTING_PROJECT_SOURCES["dirty"])
    args.output_root.mkdir(parents=True, mode=0o700)
    atomic_status(args.output_root/"status.json", {
        "phase": "initialized", "owner": args.owner,
        "upstream_id_verified": True, "unity_editor_attempts": 0,
        "broker_lease_held_while_waiting": False,
    })
    started = time.monotonic()
    samples = []
    checks = 0
    broker = _read_broker_api()
    while time.monotonic() - started < args.max_wait_seconds:
        checks += 1
        try:
            result, job = _upstream_status(args, identifier)
        except (subprocess.TimeoutExpired, TimeoutError, ConnectionError, OSError) as exc:
            # Ordinary read-only status/transport interruptions may be
            # rechecked. Never repeat a side-effectful import or denied lease.
            atomic_status(args.output_root / "status.json", {
                "phase": "upstream_status_transient_retry",
                "error_type": type(exc).__name__, "owner": args.owner,
                "checks": checks, "unity_editor_attempts": 0,
                "broker_lease_held_while_waiting": False,
            })
            samples.clear()
            time.sleep(args.poll_seconds)
            continue
        gate = upstream_gate(result, job)
        if gate == "halt":
            atomic_status(args.output_root/"status.json", {
                "phase": "upstream_missing_verified_terminal_result",
                "owner": args.owner, "unity_editor_attempts": 0,
                "upstream_job_state": job.get("state"),
                "broker_lease_held_while_waiting": False,
            })
            return 4
        if gate == "wait":
            atomic_status(args.output_root/"status.json", {
                "phase": "waiting_for_original_urp_worker",
                "owner": args.owner, "checks": checks,
                "upstream_job_state": job.get("state"),
                "unity_editor_attempts": 0,
                "broker_lease_held_while_waiting": False,
            })
            samples.clear()
            time.sleep(args.poll_seconds)
            continue
        if not no_other_unity():
            samples.clear()
            time.sleep(args.poll_seconds)
            continue

        sample = sample_live()
        admission = admission_snapshot(sample["cpu_count"], sample["one_min_load"],
                                       sample["pressure_percent"])
        samples.append(admission)
        samples = samples[-args.required_samples:]
        atomic_status(args.output_root/"status.json", {
            "phase": "waiting_for_cpu_after_urp_worker",
            "owner": args.owner, "checks": checks,
            "latest": admission, "unity_editor_attempts": 0,
            "broker_lease_held_while_waiting": False,
        })
        if not should_attempt(samples, args.required_samples):
            time.sleep(args.poll_seconds)
            continue

        try:
            state = broker.analyze_current_machine(refresh=True)
        except (subprocess.TimeoutExpired, TimeoutError, ConnectionError, OSError) as exc:
            atomic_status(args.output_root / "status.json", {
                "phase": "broker_monitor_transient_retry",
                "error_type": type(exc).__name__, "owner": args.owner,
                "checks": checks, "unity_editor_attempts": 0,
                "broker_lease_held_while_waiting": False,
            })
            samples.clear()
            time.sleep(args.poll_seconds)
            continue
        monitor = state.get("monitor") or {}
        if (monitor.get("capacity") or {}).get("status") != "ok" or \
                monitor.get("snapshot_status") not in (None, "ok"):
            samples.clear()
            time.sleep(args.poll_seconds)
            continue
        try:
            grant = broker.reserve_resources("nitro", args.owner, 6.0, 0.0, 2.0, 7200, secure=True)
        except Exception as exc:
            atomic_status(args.output_root/"status.json", {
                "phase": "secure_broker_reservation_denied_or_uncertain",
                "error_type": type(exc).__name__, "owner": args.owner,
                "unity_editor_attempts": 0,
                "denial_not_retried_or_rerouted": True,
            })
            return 4
        if not (isinstance(grant, tuple) and len(grant) == 2):
            raise ValueError("Broker returned an invalid secure lease")
        request, secret = grant
        private = args.output_root/"lease-private.json"
        outcome_code = 6
        attempted = False
        try:
            atomic_status(private, {"owner": args.owner, "request_id": request,
                                    "control_token": secret})
            atomic_status(args.output_root/"status.json", {
                "phase": "running_approved_disposable_customer_editor_checks",
                "owner": args.owner, "unity_editor_attempts": 1,
                "source_projects_previously_staged": True,
            })
            attempted = True
            result = _run_permitted_qa(args, args.output_root)
            atomic_status(args.output_root/"status.json", result)
            outcome_code = 0 if result["status"] == "complete_verified" else 5
        except Exception as exc:
            atomic_status(args.output_root/"status.json", {
                "phase": "independent_customer_qa_unknown_effect_requires_review",
                "owner": args.owner, "attempted": attempted,
                "error_type": type(exc).__name__, "no_replay_in_same_project": True,
            })
            outcome_code = 6
        finally:
            try:
                released = broker.release_resources(args.owner, request, control_token=secret)
            except Exception:
                released = False
            if released:
                if private.is_file():
                    private.unlink()
            else:
                persisted = private.is_file()
                if not persisted:
                    # If the disk is full or private writes are denied, the
                    # capability might be unrecoverable. Record that explicitly;
                    # the broker lease must expire by its own TTL, not by an
                    # invented insecure release or another owner's token.
                    try:
                        atomic_status(private, {
                            "owner": args.owner, "request_id": request,
                            "control_token": secret,
                        })
                        persisted = True
                    except Exception:
                        persisted = False
                atomic_status(args.output_root/"status.json", {
                    "phase": "secure_broker_release_unverified",
                    "owner": args.owner, "attempted": attempted,
                    "secure_credential_persisted": persisted,
                    "lease_may_remain_active_until_ttl": True,
                    "do_not_start_another_job_until_lease_is_reconciled": True,
                })
        return outcome_code if released else 4

    atomic_status(args.output_root/"status.json", {
        "phase": "bounded_wait_expired_no_unity_editor_started",
        "owner": args.owner, "checks": checks,
        "unity_editor_attempts": 0, "no_reservation_held": True,
    })
    return 2


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode", choices=("report", "retry"), default="report")
    p.add_argument("--output-root", type=Path, default=DEFAULT_ROOT)
    p.add_argument("--upstream", type=Path, default=DEFAULT_UPSTREAM)
    p.add_argument("--upstream-id-file", type=Path, default=DEFAULT_UPSTREAM_ID)
    p.add_argument("--native", type=Path, default=DEFAULT_NATIVE)
    p.add_argument("--dirty", type=Path, default=DEFAULT_DIRTY)
    p.add_argument("--editor", type=Path, default=DEFAULT_EDITOR)
    p.add_argument("--owner", type=str, default=DEFAULT_OWNER)
    p.add_argument("--poll-seconds", type=int, default=120)
    p.add_argument("--max-wait-seconds", type=int, default=100800)
    p.add_argument("--required-samples", type=int, default=2)
    p.add_argument("--editor-timeout-seconds", type=int, default=1800)
    args = p.parse_args()
    if not 20 <= args.poll_seconds <= 1800 or not 1 <= args.required_samples <= 5 or \
            not 300 <= args.max_wait_seconds <= 172800 or \
            not 60 <= args.editor_timeout_seconds <= 3600:
        p.error("Unreasonable worker deadline, capacity sample or Editor timeout")
    return args


def main() -> int:
    args = parse_args()
    try:
        if args.mode == "report":
            public_id = _upstream_public_id(args.upstream_id_file)
            source, job = _upstream_status(args, public_id)
            stats = sample_live()
            returncode = {
                "upstream_gate": upstream_gate(source, job),
                "upstream_report_phase": source.get("phase", source.get("status")),
                "upstream_job_state": job.get("state"),
                "cpu_admission": admission_snapshot(
                    stats["cpu_count"], stats["one_min_load"], stats["pressure_percent"]),
                "no_unity_process_created": True, "no_lease_requested": True,
                "independent_buyer_qa_stages": [x["name"] for x in STAGES],
            }
            print(json.dumps(returncode, indent=2))
            return 0
        return run_worker(args)
    except Exception as exc:
        print(json.dumps({"phase": "requires_manual_review", "error_type": type(exc).__name__,
                          "detail": str(exc)[:180], "no_publication": True}))
        return 6


if __name__ == "__main__":
    raise SystemExit(main())
