#!/usr/bin/env bash
set -euo pipefail

seconds="${1:-3}"
shift || true
message="${*:-Leave the window alone briefly.}"

run_notice() {
  zenity --info \
    --title="Codex Notice" \
    --text="$message" \
    --width=460 \
    --timeout="$seconds" \
    --no-wrap >/dev/null 2>&1 &
  local pid=$!
  for _ in $(seq 1 30); do
    local wid
    wid="$(wmctrl -lp 2>/dev/null | awk '/Codex Notice/ {print $1; exit}')"
    if [[ -n "${wid:-}" ]]; then
      wmctrl -ia "$wid" >/dev/null 2>&1 || true
      break
    fi
    sleep 0.1
  done
  wait "$pid" || true
}

if [[ "$(id -un)" == "hans" ]]; then
  export DISPLAY="${DISPLAY:-:1}"
  export XAUTHORITY="${XAUTHORITY:-/home/hans/.Xauthority}"
  export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/1000}"
  export DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}"
  run_notice &
  disown || true
  exit 0
fi

sudo -u hans -H env \
  DISPLAY="${DISPLAY:-:1}" \
  XAUTHORITY="${XAUTHORITY:-/home/hans/.Xauthority}" \
  XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/1000}" \
  DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}" \
  bash -lc "$(printf '%q ' declare -f run_notice); message=$(printf '%q' "$message"); seconds=$(printf '%q' "$seconds"); run_notice" >/dev/null 2>&1 &
