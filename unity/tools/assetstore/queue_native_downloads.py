#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import unity_native_asset


ROOT = Path("/data/src/github/games")
CATALOG = ROOT / "unity/assetstore/metadata/my_assets.json"
STATE = ROOT / "unity/assetstore/metadata/native_download_state.json"
LOG = ROOT / "unity/assetstore/logs/native_download_queue.log"
RUNNER = ROOT / "unity/tools/assetstore/unity_native_asset.py"
TERMUX_USER = "hans"


def ensure_hans_context() -> None:
    if os.geteuid() != 0 or os.environ.get("HPR_ASSET_QUEUE_AS_HANS") == "1":
        return

    env = os.environ.copy()
    env["HPR_ASSET_QUEUE_AS_HANS"] = "1"
    env.setdefault("DBUS_SESSION_BUS_ADDRESS", "unix:path=/run/user/1000/bus")
    env.setdefault("XDG_RUNTIME_DIR", "/run/user/1000")
    cmd = [
        "sudo",
        "-u",
        TERMUX_USER,
        "-H",
        "env",
        f"DBUS_SESSION_BUS_ADDRESS={env['DBUS_SESSION_BUS_ADDRESS']}",
        f"XDG_RUNTIME_DIR={env['XDG_RUNTIME_DIR']}",
        "HPR_ASSET_QUEUE_AS_HANS=1",
        sys.executable,
        __file__,
        *sys.argv[1:],
    ]
    raise SystemExit(subprocess.call(cmd, env=env))


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {}


def save_state(state: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2, sort_keys=True))


def find_active_download_pids() -> list[int]:
    process = subprocess.run(
        ["pgrep", "-f", "unity_native_asset.py download"],
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode not in (0, 1):
        return []

    pids: list[int] = []
    for line in process.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            pid = int(line)
        except ValueError:
            continue
        if pid != os.getpid():
            pids.append(pid)
    return pids


def wait_for_active_downloads(log_handle, poll_interval: float) -> None:
    while True:
        active = find_active_download_pids()
        if not active:
            return
        log_handle.write(f"WAIT\tactive_downloads={','.join(str(pid) for pid in active)}\n")
        log_handle.flush()
        time.sleep(poll_interval)


def expected_download_path(client, package_id: int) -> Path:
    raw = Path(unity_native_asset.fetch_metadata(client, package_id)["final_path"])
    return unity_native_asset.resolve_final_path(raw)


def record_downloaded(state: dict, package_id: int, display_name: str, path: Path) -> None:
    state[str(package_id)] = {
        "status": "downloaded",
        "displayName": display_name,
        "path": str(path),
        "updatedAt": time.time(),
        "size": path.stat().st_size,
    }


def main() -> int:
    ensure_hans_context()

    parser = argparse.ArgumentParser()
    parser.add_argument("--package-ids", default="")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--timeout", type=int, default=3600)
    parser.add_argument("--poll-interval", type=float, default=20.0)
    parser.add_argument("--continue-on-error", action="store_true")
    args = parser.parse_args()

    purchases = json.loads(CATALOG.read_text())
    wanted_list = [int(value) for value in args.package_ids.split(",") if value.strip()]
    wanted = set(wanted_list)
    if wanted:
        order = {package_id: index for index, package_id in enumerate(wanted_list)}
        purchases = [item for item in purchases if int(item["packageId"]) in wanted]
        purchases.sort(key=lambda item: order[int(item["packageId"])])

    state = load_state()
    LOG.parent.mkdir(parents=True, exist_ok=True)
    client = unity_native_asset.unity_assetstore.UnityAssetStore()

    with LOG.open("a") as log_handle:
        for item in purchases:
            package_id = int(item["packageId"])
            display_name = item["displayName"]
            final_path = expected_download_path(client, package_id)
            if args.skip_existing and unity_native_asset.is_probably_unitypackage(unity_native_asset.resolve_final_path(final_path)):
                final_path = unity_native_asset.resolve_final_path(final_path)
                record_downloaded(state, package_id, display_name, final_path)
                save_state(state)
                log_handle.write(f"SKIP\t{package_id}\t{final_path}\n")
                log_handle.flush()
                continue

            if final_path.exists() and not unity_native_asset.is_probably_unitypackage(final_path):
                log_handle.write(f"CLEAN\t{package_id}\t{final_path}\n")
                log_handle.flush()
                final_path.unlink(missing_ok=True)

            log_handle.write(f"START\t{package_id}\t{display_name}\n")
            log_handle.flush()
            wait_for_active_downloads(log_handle, args.poll_interval)
            started = time.time()
            command = [
                "/data/venv/bin/python",
                str(RUNNER),
                "download",
                str(package_id),
                "--timeout",
                str(args.timeout),
            ]
            if os.geteuid() == 0:
                command = [
                    "sudo", "-u", TERMUX_USER, "-H",
                    "env",
                    "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus",
                    "XDG_RUNTIME_DIR=/run/user/1000",
                    *command,
                ]
            else:
                command = [
                    "env",
                    f"DBUS_SESSION_BUS_ADDRESS={os.environ.get('DBUS_SESSION_BUS_ADDRESS', 'unix:path=/run/user/1000/bus')}",
                    f"XDG_RUNTIME_DIR={os.environ.get('XDG_RUNTIME_DIR', '/run/user/1000')}",
                    *command,
                ]

            process = subprocess.run(
                command,
                text=True,
                capture_output=True,
            )

            if process.returncode == 0:
                final_path = Path(process.stdout.strip().splitlines()[-1]) if process.stdout.strip() else final_path
                final_path = unity_native_asset.resolve_final_path(final_path)
                record_downloaded(state, package_id, display_name, final_path)
                state[str(package_id)]["durationSeconds"] = round(time.time() - started, 2)
                log_handle.write(f"DONE\t{package_id}\t{final_path}\n")
            else:
                state[str(package_id)] = {
                    "status": "error",
                    "displayName": display_name,
                    "updatedAt": time.time(),
                    "durationSeconds": round(time.time() - started, 2),
                    "stdout": process.stdout[-4000:],
                    "stderr": process.stderr[-4000:],
                }
                log_handle.write(f"ERROR\t{package_id}\t{display_name}\n")
                log_handle.write(process.stdout[-4000:])
                log_handle.write(process.stderr[-4000:])
                log_handle.write("\n")
                save_state(state)
                if not args.continue_on_error:
                    return process.returncode

            save_state(state)
            log_handle.flush()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
