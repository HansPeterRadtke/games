#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: run_unity_batch.sh <ExecuteMethod> [extra-unity-args...]" >&2
  exit 1
fi

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(git -C "$script_dir" rev-parse --show-toplevel)
workspace_root="${WORKSPACE_ROOT:-$repo_root/unity}"
project_path="${PROJECT_PATH:-$repo_root/unity/projects/fps_demo}"
unity_bin="${UNITY_BIN:-/data/apps/Unity/Hub/Editor/6000.4.0f1/Editor/Unity}"
method=$1
shift
log_dir="${LOG_DIR:-$repo_root/doc/logs}"
mkdir -p "$log_dir"
log_file="${LOG_FILE:-$log_dir/$(date +%Y%m%d_%H%M%S)_${method##*.}.log}"

cleanup_locks() {
  rm -f "$project_path"/Library/*.pid "$project_path"/Library/*lock* "$project_path"/Temp/UnityLockfile 2>/dev/null || true
}

sync_local_packages() {
  python3 - <<'PY' "$project_path/Packages" "$workspace_root/packages"
from pathlib import Path
import os
import shutil
import sys

packages_dir = Path(sys.argv[1])
shared_packages = Path(sys.argv[2])
package_names = sorted(path.name for path in shared_packages.iterdir() if path.is_dir() and path.name.startswith("com.hpr."))

for name in package_names:
    source = shared_packages / name
    target = packages_dir / name
    relative_source = Path(os.path.relpath(source, packages_dir))
    if target.is_symlink() and (packages_dir / Path(os.readlink(target))).resolve() == source.resolve():
        continue
    if target.exists() or target.is_symlink():
        if target.is_symlink() or target.is_file():
            target.unlink()
        else:
            shutil.rmtree(target)
    target.symlink_to(relative_source)
PY
}

run_batch() {
  sync_local_packages
  cleanup_locks
  "$unity_bin" -batchmode -projectPath "$project_path" -executeMethod "$method" -quit -logFile "$log_file" "$@"
}

if [[ "$(id -un)" == "hans" ]]; then
  run_batch "$@"
else
  exec sudo -u hans -H env \
    HOME=/home/hans USER=hans LOGNAME=hans \
    DISPLAY="${DISPLAY:-:1}" \
    XAUTHORITY="${XAUTHORITY:-/home/hans/.Xauthority}" \
    XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/1000}" \
    DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}" \
    PROJECT_PATH="$project_path" UNITY_BIN="$unity_bin" LOG_DIR="$log_dir" LOG_FILE="$log_file" \
    bash "$script_dir/run_unity_batch.sh" "$method" "$@"
fi

if rg -n "error CS|: error|Aborting batchmode|Unhandled exception|NullReferenceException|Exception:" "$log_file" >/dev/null 2>&1; then
  echo "Unity batch method failed. See log: $log_file" >&2
  rg -n "error CS|: error|Aborting batchmode|Unhandled exception|NullReferenceException|Exception:" "$log_file" >&2 || true
  exit 1
fi

echo "Unity batch method succeeded"
echo "Log: $log_file"
