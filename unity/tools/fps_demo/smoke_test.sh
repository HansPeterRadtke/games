#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(git -C "$script_dir" rev-parse --show-toplevel)
player_bin="${PLAYER_BIN:-$repo_root/unity/projects/fps_demo/Build/Linux/FPSDemo.x86_64}"
timeout_seconds="${SMOKE_TIMEOUT:-20}"
notice_seconds="${NOTICE_SECONDS:-2}"
notice_message="${NOTICE_MESSAGE:-Leave FPSDemo alone for 8 seconds.}"

run_smoke() {
  local log_root="${HOME}/.config/unity3d/DefaultCompany/fps_demo"
  mkdir -p "$log_root"
  rm -f "$log_root/Player.log"
  if [[ "${NO_NOTICE:-0}" != "1" ]]; then
    "$repo_root/unity/tools/common/focus_notice.sh" "$notice_seconds" "$notice_message"
    sleep 2.2
  fi
  timeout "$timeout_seconds" "$player_bin" -smoketest
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
    PLAYER_BIN="$player_bin" SMOKE_TIMEOUT="$timeout_seconds" NOTICE_SECONDS="$notice_seconds" NOTICE_MESSAGE="$notice_message" \
    bash "$script_dir/smoke_test.sh"
fi
