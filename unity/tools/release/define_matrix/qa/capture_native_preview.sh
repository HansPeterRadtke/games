#!/usr/bin/env bash
# Private real Editor screenshot on a self-owned isolated Xvfb display only.
# Does not use owner or another worker's X display, windows, or browser tabs.
set -euo pipefail
project=${1:?Previously accepted disposable private buyer project required}
out=${2:?Existing private evidence directory required}
[[ "$project" = /data/var/marketplace-account-setup/*/buyer && -d "$project/Assets/HPRDefineMatrix" && -d "$out" ]]
[[ ! -e "$out/define-matrix-native-preview.png" ]]
[[ ! -e /tmp/.X138-lock ]] || { echo 'Private Xvfb display occupied; refuse' >&2; exit 3; }
script_dir=$(cd -- "$(dirname "$0")" && pwd)
unity=/data/apps/Unity/Hub/Editor/6000.6.8f1/Editor/Unity
[[ -x "$unity" ]]
cp "$script_dir/HprDefineMatrixPreview.cs" "$project/Assets/Editor/HprDefineMatrixPreview.cs"
export HOME=/home/hans USER=hans LOGNAME=hans DISPLAY=:138
export XAUTHORITY=/home/hans/.Xauthority XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export LP_NUM_THREADS=2
Xvfb :138 -screen 0 1680x1050x24 -nolisten tcp > "$out/define-preview-xvfb.log" 2>&1 &
xvfb_pid=$!
unity_pid=''
cleanup(){
  if [[ -n "$unity_pid" ]] && kill -0 "$unity_pid" 2>/dev/null; then kill -TERM "$unity_pid" 2>/dev/null || true; fi
  if [[ -n "$unity_pid" ]]; then wait "$unity_pid" 2>/dev/null || true; fi
  if kill -0 "$xvfb_pid" 2>/dev/null; then kill -TERM "$xvfb_pid" 2>/dev/null || true; fi
  wait "$xvfb_pid" 2>/dev/null || true
}
trap cleanup EXIT
for i in {1..15}; do
 [[ -S /tmp/.X11-unix/X138 ]] && break
 sleep 1
done
[[ -S /tmp/.X11-unix/X138 ]] || { echo 'Xvfb failed to start' >&2; exit 4; }
"$unity" -projectPath "$project" -executeMethod HprDefineMatrixPreview.Open -logFile "$out/define-preview-editor.unity.log" > "$out/define-preview-editor.stdout" 2>&1 &
unity_pid=$!
window=''
for i in {1..140}; do
 kill -0 "$unity_pid" 2>/dev/null || { echo 'Native Editor exited before screenshot' >&2; exit 5; }
 if grep -q 'HPR_DEFINE_PREVIEW_WINDOW_OPENED' "$out/define-preview-editor.unity.log" 2>/dev/null; then
   window=$(xdotool search --onlyvisible --name 'Define Matrix' 2>/dev/null | tail -1 || true)
   if [[ -n "$window" ]]; then break; fi
 fi
 sleep 2
done
[[ -n "$window" ]] || { echo 'Define Matrix window not found on private display' >&2; exit 6; }
xdotool windowraise "$window" || true
sleep 3
import -window "$window" "$out/define-matrix-native-preview.png"
[[ -s "$out/define-matrix-native-preview.png" ]]
printf 'NATIVE_WINDOW_CAPTURED %s\n' "$window"
