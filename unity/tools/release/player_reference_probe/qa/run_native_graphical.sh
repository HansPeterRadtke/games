#!/usr/bin/env bash
set -euo pipefail
label=${1:?previous actual built Player buyer label}
[[ "$label" =~ ^[a-z0-9_-]{4,30}$ ]]||exit 2
root=/data/var/marketplace-account-setup/unity-player-reference-probe-20261123-wave63
work="$root/$label"
project="$work/independent-buyer-project"
qa=$(cd "$(dirname "$0")" && pwd)/HprProbeQaGraphical.cs
target="$project/Assets/Editor/HprProbeQaGraphical.cs"
out="$work/actual-original-graphical-qa"
unity=/data/apps/Unity/Hub/Editor/6000.6.8f1/Editor/Unity
[[ -x "$unity" && -s "$qa" && -s "$work/editor-original-baseline.json" &&
 -s "$work/actual-player-receipt.json" && -d "$project/Assets/HPRPlayerReferenceProbe" &&
 ! -e "$target" && ! -e "$out" && ! -e /tmp/.X11-unix/X148 ]] || {
 echo 'Refusing repeated UI access or missing independent actual Player buyer project' >&2;exit 3;
}
mkdir -p "$out"
cp "$qa" "$target"
Xvfb :148 -screen 0 1440x900x24 -nolisten tcp >"$out/xvfb.log" 2>&1 & pid_x=$!
trap 'kill "$pid_x" 2>/dev/null || true' EXIT
for i in $(seq 1 30);do [[ -S /tmp/.X11-unix/X148 ]] && break; sleep .2;done
[[ -S /tmp/.X11-unix/X148 ]]||exit 4
export DISPLAY=:148 LIBGL_ALWAYS_SOFTWARE=1 HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
export HPR_PROBE_QA_GUI_RECEIPT="$out/original-graphical-receipt.txt" HPR_PROBE_QA_ROOT="$work"
if command -v openbox >/dev/null;then openbox --sm-disable >"$out/wm.log" 2>&1 & wm=$!;trap 'kill "$wm" "$pid_x" 2>/dev/null || true' EXIT;fi
(timeout 140 "$unity" -force-glcore -projectPath "$project" \
 -executeMethod HprProbeQaGraphical.Run -logFile "$out/native-editor.log" \
 > "$out/native-editor.stdout" 2>&1) & pid_unity=$!
sleep 67
import -display :148 -window root "$out/actual-original-player-reference-editor.png"
[[ -s "$out/original-graphical-receipt.txt" && -s "$out/actual-original-player-reference-editor.png" ]] || {
 grep -E 'HPR_PLAYER_PROBE_GUI_QA_FAILURE|error CS[0-9]|Exception' "$out/native-editor.log"|tail -15 >&2 || true;exit 5;
}
grep -q HPR_PLAYER_REFERENCE_REAL_GRAPHICAL_WINDOW_QA_PASS "$out/native-editor.log"
convert "$out/actual-original-player-reference-editor.png" -resize 900x563 -quality 72 "$out/visual-inspection-900.jpg"
cat "$out/original-graphical-receipt.txt"
wait "$pid_unity"||true
