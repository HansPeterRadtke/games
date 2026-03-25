#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: run_unity_batch.sh <ExecuteMethod> [extra-unity-args...]" >&2
  exit 1
fi

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(git -C "$script_dir" rev-parse --show-toplevel)
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

run_batch() {
  cleanup_locks
  exec "$unity_bin" -batchmode -projectPath "$project_path" -executeMethod "$method" -quit -logFile "$log_file" "$@"
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
