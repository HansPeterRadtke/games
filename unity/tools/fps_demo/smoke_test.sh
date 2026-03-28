#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(git -C "$script_dir" rev-parse --show-toplevel)
player_bin="${PLAYER_BIN:-$repo_root/unity/projects/fps_demo/Build/Linux/FPSDemo.x86_64}"
timeout_seconds="${SMOKE_TIMEOUT:-20}"
notice_seconds="${NOTICE_SECONDS:-2}"
notice_message="${NOTICE_MESSAGE:-Leave FPSDemo alone for 8 seconds.}"
log_dir="${LOG_DIR:-$repo_root/doc/logs}"
log_file="${LOG_FILE:-$log_dir/$(date +%Y%m%d_%H%M%S)_smoke_test.log}"

run_smoke() {
  local log_root="${HOME}/.config/unity3d/DefaultCompany/fps_demo"
  mkdir -p "$log_root"
  mkdir -p "$log_dir"
  rm -f "$log_root/Player.log"
  if [[ "${NO_NOTICE:-0}" != "1" ]]; then
    "$repo_root/unity/tools/common/focus_notice.sh" "$notice_seconds" "$notice_message"
    sleep 2.2
  fi
  local rc=0
  timeout "$timeout_seconds" "$player_bin" -smoketest || rc=$?
  if [[ -f "$log_root/Player.log" ]]; then
    cp "$log_root/Player.log" "$log_file"
  else
    printf 'Player.log missing after smoke test\n' >"$log_file"
  fi
  if [[ $rc -ne 0 ]]; then
    return "$rc"
  fi
  if ! rg -n "Smoke test completed" "$log_file" >/dev/null 2>&1; then
    echo "Smoke test did not report completion. See log: $log_file" >&2
    exit 1
  fi
  echo "Smoke test log: $log_file"
}

if [[ "$(id -un)" == "hans" ]]; then
  run_smoke
else
  exec sudo -u hans -H env \
    HOME=/home/hans USER=hans LOGNAME=hans \
    DISPLAY="${DISPLAY:-:1}" \
    XAUTHORITY="${XAUTHORITY:-/home/hans/.Xauthority}" \
    XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/1000}" \
    DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}" \
    PLAYER_BIN="$player_bin" SMOKE_TIMEOUT="$timeout_seconds" NOTICE_SECONDS="$notice_seconds" NOTICE_MESSAGE="$notice_message" LOG_DIR="$log_dir" LOG_FILE="$log_file" \
    bash "$script_dir/smoke_test.sh"
fi
