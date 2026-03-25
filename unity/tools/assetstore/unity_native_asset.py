#!/usr/bin/env python3
import argparse
import json
import os
import re
import shlex
import signal
import subprocess
import sys
import time
from pathlib import Path

import unity_assetstore


REPO_ROOT = Path("/data/src/github/games")
UNITY = Path("/data/apps/Unity/Hub/Editor/6000.4.0f1/Editor/Unity")
MAIN_PROJECT = REPO_ROOT / "unity/projects/fps_demo"
HELPER_PROJECT = Path("/home/hans/.local/share/hpr_unity_asset_helper")
LOG_DIR = REPO_ROOT / "unity/assetstore/logs"
DOWNLOAD_CACHE = Path("/home/hans/.local/share/unity3d/Asset Store-5.x")
PIPELINE_META_DIR = REPO_ROOT / "unity/assetstore/metadata/pipeline"


def build_unity_command(project: Path, method: str, extra_args: list[str], log_name: str, auto_quit: bool = True) -> tuple[list[str], Path]:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / log_name
    args_str = " ".join(shlex.quote(arg) for arg in extra_args)
    quit_arg = " -quit" if auto_quit else ""
    cmd = [
        "sudo", "-u", "hans", "-H",
        "env",
        f"UNITY={UNITY}",
        f"PROJECT={project}",
        f"LOG={log_path}",
        "bash", "-lc",
        "\"$UNITY\" -batchmode -nographics -projectPath \"$PROJECT\" -executeMethod "
        + method
        + " "
        + args_str
        + quit_arg
        + " -logFile \"$LOG\"",
    ]
    return cmd, log_path


def kill_stale_helper_unity() -> None:
    subprocess.run(
        [
            "bash",
            "-lc",
            f"pkill -u hans -f {shlex.quote(str(HELPER_PROJECT))} || true",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    time.sleep(2)


def run_unity(project: Path, method: str, extra_args: list[str], log_name: str) -> subprocess.CompletedProcess[str]:
    cmd, _ = build_unity_command(project, method, extra_args, log_name)
    return subprocess.run(cmd, text=True, capture_output=True)


def maybe_recover_import_with_known_fixes(log_name: str) -> bool:
    log_path = LOG_DIR / log_name
    if not log_path.exists():
        return False

    log_text = log_path.read_text(errors="ignore")
    if "Scripts have compiler errors." not in log_text:
        return False

    fix_result = run_unity(
        MAIN_PROJECT,
        "AssetStoreImportTools.ApplyKnownCompatibilityFixes",
        [],
        f"{Path(log_name).stem}_fixup.log",
    )
    return fix_result.returncode == 0


def fetch_metadata(client: unity_assetstore.UnityAssetStore, package_id: int) -> dict:
    product = client.fetch_product(package_id)
    download = client.fetch_download_info(package_id)["result"]["download"]
    return {
        "package_id": str(package_id),
        "display_name": product["displayName"],
        "publisher": download["filename_safe_publisher_name"],
        "category": download["filename_safe_category_name"],
        "package_name": download["filename_safe_package_name"],
        "asset_key": download["key"],
        "asset_url": download["url"],
        "final_path": DOWNLOAD_CACHE / download["filename_safe_publisher_name"] / download["filename_safe_category_name"] / f"{download['filename_safe_package_name']}.unitypackage",
    }


def load_cached_metadata(package_id: int) -> dict | None:
    candidates = [
        PIPELINE_META_DIR / f"meta_{package_id}.json",
        REPO_ROOT / "unity/assetstore/metadata" / f"meta_{package_id}.json",
    ]
    for path in candidates:
        if path.exists():
            meta = json.loads(path.read_text())
            if "final_path" in meta:
                meta["final_path"] = Path(meta["final_path"])
            return meta
    return None


def fetch_metadata_with_cache(package_id: int) -> dict:
    client = unity_assetstore.UnityAssetStore()
    try:
        return fetch_metadata(client, package_id)
    except Exception:
        cached = load_cached_metadata(package_id)
        if cached is not None:
            return cached
        raise


def is_probably_unitypackage(path: Path) -> bool:
    if not path.exists() or path.stat().st_size < 4:
        return False
    with path.open("rb") as handle:
        return handle.read(2) == b"\x1f\x8b"


def _normalize_asset_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def resolve_final_path(final_path: Path) -> Path:
    if final_path.exists():
        return final_path
    parent = final_path.parent
    if not parent.exists():
        return final_path
    expected = _normalize_asset_name(final_path.stem)
    for candidate in sorted(parent.glob("*.unitypackage")):
        if _normalize_asset_name(candidate.stem) == expected:
            return candidate
    return final_path


def temp_download_path(final_path: Path, package_id: int) -> Path:
    resolved_final = resolve_final_path(final_path)
    parent = resolved_final.parent
    if parent.exists():
        matches = sorted(parent.glob(f".*-{package_id}.tmp"), key=lambda p: p.stat().st_mtime_ns, reverse=True)
        if matches:
            return matches[0]
    return resolved_final.with_name(f".{resolved_final.stem}-{package_id}.tmp")


def cleanup_stale_download_artifacts(final_path: Path, package_id: int, stale_seconds: int = 120) -> None:
    resolved_final = resolve_final_path(final_path)
    tmp_path = temp_download_path(resolved_final, package_id)
    if is_probably_unitypackage(resolved_final):
        return

    candidates = [tmp_path, Path(str(tmp_path) + ".json"), resolved_final]
    if resolved_final.parent.exists():
        candidates.extend(sorted(resolved_final.parent.glob(f".*-{package_id}.tmp*")))
    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen or not candidate.exists():
            continue
        seen.add(candidate)
        age_seconds = time.time() - candidate.stat().st_mtime
        if age_seconds >= stale_seconds:
            candidate.unlink(missing_ok=True)


def _kill_process_tree(process: subprocess.Popen[str]) -> None:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=10)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        return
    process.wait(timeout=10)


def run_unity_download_with_monitoring(
    package_id: int,
    final_path: Path,
    method: str,
    extra_args: list[str],
    log_name: str,
    timeout: int,
    stall_timeout: int,
) -> tuple[int, str, str]:
    kill_stale_helper_unity()
    cmd, log_path = build_unity_command(HELPER_PROJECT, method, extra_args, log_name, auto_quit=False)
    process = subprocess.Popen(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    started = time.monotonic()
    last_progress = started
    last_size = None
    last_mtime_ns = None
    last_reported_at = started
    download_completed = False

    while True:
        resolved_final = resolve_final_path(final_path)
        if is_probably_unitypackage(resolved_final):
            download_completed = True
            if process.poll() is not None:
                break
            if time.monotonic() - last_progress > 10:
                _kill_process_tree(process)
                break

        if process.poll() is not None:
            break

        observed_path = resolved_final if resolved_final.exists() else temp_download_path(final_path, package_id)
        if observed_path.exists():
            stat = observed_path.stat()
            signature = (stat.st_size, stat.st_mtime_ns)
            if signature != (last_size, last_mtime_ns):
                last_size, last_mtime_ns = signature
                last_progress = time.monotonic()
                if time.monotonic() - last_reported_at >= 15 or observed_path == final_path:
                    print(f"progress package={package_id} path={observed_path} size={stat.st_size}", flush=True)
                    last_reported_at = time.monotonic()

        elapsed = time.monotonic() - started
        stalled = time.monotonic() - last_progress
        if elapsed > timeout:
            _kill_process_tree(process)
            stdout, stderr = process.communicate()
            stderr = (stderr or "") + f"\nTimed out after {timeout}s waiting for package {package_id}\n"
            return 124, stdout or "", stderr

        if stalled > stall_timeout:
            _kill_process_tree(process)
            stdout, stderr = process.communicate()
            detail = ""
            if observed_path.exists():
                detail = f"path={observed_path} size={observed_path.stat().st_size}"
            stderr = (stderr or "") + f"\nStalled after {stall_timeout}s without download progress for package {package_id}. {detail}\n"
            return 125, stdout or "", stderr

        time.sleep(5)

    stdout, stderr = process.communicate()
    resolved_final = resolve_final_path(final_path)
    if is_probably_unitypackage(resolved_final):
        return 0, stdout or "", stderr or ""
    return process.returncode or 0, stdout or "", stderr or ""


def cmd_download(args: argparse.Namespace) -> int:
    meta = fetch_metadata_with_cache(args.package_id)
    final_path = resolve_final_path(Path(meta["final_path"]))
    if is_probably_unitypackage(final_path):
        print(final_path)
        return 0
    cleanup_stale_download_artifacts(final_path, args.package_id)
    if final_path.exists():
        final_path.unlink(missing_ok=True)
    extra_args = [
        "-assetId", meta["package_id"],
        "-assetUrl", meta["asset_url"],
        "-publisher", meta["publisher"],
        "-category", meta["category"],
        "-packageName", meta["package_name"],
        "-timeout", str(args.timeout),
    ]
    if meta.get("asset_key"):
        extra_args[4:4] = ["-assetKey", meta["asset_key"]]
    returncode, stdout, stderr = run_unity_download_with_monitoring(
        args.package_id,
        final_path,
        "AssetStoreImportTools.DirectAssetStoreContextDownloadFromArgs",
        extra_args,
        f"native_download_{args.package_id}.log",
        args.timeout,
        args.stall_timeout,
    )
    final_path = resolve_final_path(final_path)
    if returncode != 0 and is_probably_unitypackage(final_path):
        returncode = 0
    if returncode != 0:
        sys.stderr.write(stdout)
        sys.stderr.write(stderr)
        sys.stderr.write((LOG_DIR / f"native_download_{args.package_id}.log").read_text())
        return returncode
    if not is_probably_unitypackage(final_path):
        sys.stderr.write(f"Downloaded file is not a valid gzip-based unitypackage: {final_path}\n")
        return 2
    print(final_path)
    return 0


def cmd_import(args: argparse.Namespace) -> int:
    package_path = Path(args.package_path).expanduser().resolve()
    log_name = f"native_import_{package_path.stem}.log"
    result = run_unity(MAIN_PROJECT, "AssetStoreImportTools.ImportFromArgs", ["-assetPackage", str(package_path)], log_name)
    if result.returncode != 0:
        if maybe_recover_import_with_known_fixes(log_name):
            print(package_path)
            return 0
        sys.stderr.write(result.stderr)
        sys.stderr.write((LOG_DIR / log_name).read_text())
        return result.returncode
    print(package_path)
    return 0


def cmd_download_import(args: argparse.Namespace) -> int:
    meta = fetch_metadata_with_cache(args.package_id)
    final_path = resolve_final_path(Path(meta["final_path"]))
    if final_path.exists() and not is_probably_unitypackage(final_path):
        final_path.unlink(missing_ok=True)
    cleanup_stale_download_artifacts(final_path, args.package_id)
    if is_probably_unitypackage(final_path):
        import_result = run_unity(MAIN_PROJECT, "AssetStoreImportTools.ImportFromArgs", ["-assetPackage", str(final_path)], f"native_import_{args.package_id}.log")
        if import_result.returncode != 0:
            sys.stderr.write(import_result.stderr)
            sys.stderr.write((LOG_DIR / f"native_import_{args.package_id}.log").read_text())
            return import_result.returncode
        print(json.dumps({"packageId": args.package_id, "path": str(final_path)}))
        return 0
    extra_args = [
        "-assetId", meta["package_id"],
        "-assetUrl", meta["asset_url"],
        "-publisher", meta["publisher"],
        "-category", meta["category"],
        "-packageName", meta["package_name"],
        "-timeout", str(args.timeout),
    ]
    if meta.get("asset_key"):
        extra_args[4:4] = ["-assetKey", meta["asset_key"]]
    returncode, stdout, stderr = run_unity_download_with_monitoring(
        args.package_id,
        final_path,
        "AssetStoreImportTools.DirectAssetStoreContextDownloadFromArgs",
        extra_args,
        f"native_download_{args.package_id}.log",
        args.timeout,
        args.stall_timeout,
    )
    if returncode != 0:
        sys.stderr.write(stdout)
        sys.stderr.write(stderr)
        sys.stderr.write((LOG_DIR / f"native_download_{args.package_id}.log").read_text())
        return returncode

    import_result = run_unity(MAIN_PROJECT, "AssetStoreImportTools.ImportFromArgs", ["-assetPackage", str(final_path)], f"native_import_{args.package_id}.log")
    if import_result.returncode != 0:
        log_name = f"native_import_{args.package_id}.log"
        if maybe_recover_import_with_known_fixes(log_name):
            print(json.dumps({"packageId": args.package_id, "path": str(final_path)}))
            return 0
        sys.stderr.write(import_result.stderr)
        sys.stderr.write((LOG_DIR / log_name).read_text())
        return import_result.returncode

    final_path = resolve_final_path(final_path)
    if not is_probably_unitypackage(final_path):
        sys.stderr.write(f"Downloaded file is not a valid gzip-based unitypackage: {final_path}\n")
        return 2
    print(json.dumps({"packageId": args.package_id, "path": str(final_path)}))
    return 0


def cmd_metadata(args: argparse.Namespace) -> int:
    meta = fetch_metadata_with_cache(args.package_id)
    payload = dict(meta)
    payload["final_path"] = str(payload["final_path"])
    print(json.dumps(payload))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Unity native Asset Store downloader/importer")
    sub = parser.add_subparsers(dest="cmd", required=True)

    dl = sub.add_parser("download")
    dl.add_argument("package_id", type=int)
    dl.add_argument("--timeout", type=int, default=3600)
    dl.add_argument("--stall-timeout", type=int, default=300)
    dl.set_defaults(func=cmd_download)

    imp = sub.add_parser("import")
    imp.add_argument("package_path")
    imp.set_defaults(func=cmd_import)

    dli = sub.add_parser("download-import")
    dli.add_argument("package_id", type=int)
    dli.add_argument("--timeout", type=int, default=3600)
    dli.add_argument("--stall-timeout", type=int, default=300)
    dli.set_defaults(func=cmd_download_import)

    meta = sub.add_parser("metadata")
    meta.add_argument("package_id", type=int)
    meta.set_defaults(func=cmd_metadata)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
