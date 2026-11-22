#!/usr/bin/env bash
set -euo pipefail
label=${1:?tested actual 2022 and Unity 6 native label}
[[ "$label" =~ ^[a-z0-9_-]{4,30}$ ]]||exit 2
root=/data/var/marketplace-account-setup/unity-prefab-state-parity-20261122-wave59
out="$root/graphical-original-$label"
buyer="$root/2022-3-22f1-$label/independent-buyer-project"
a="$root/2022-3-22f1-$label/real-imported-prefab-states.json"
b="$root/6000-6-8f1-$label/real-imported-prefab-states.json"
qa=$(cd "$(dirname "$0")" && pwd)/HprPrefabParityGraphicalQa.cs
target="$buyer/Assets/Editor/HprPrefabParityGraphicalQa.cs"
unity=/data/apps/Unity/Hub/Editor/2022.3.22f1/Editor/Unity
[[ -x "$unity" && -s "$a" && -s "$b" && -s "$qa" && -d "$buyer/Assets/HPRImportedPrefabParity" &&
   ! -e "$out" && ! -e "$target" && ! -e /tmp/.X11-unix/X147 ]] || { echo 'Refusing repeated graphical effect or missing original Unity source' >&2; exit 3; }
mkdir -p "$out"
cp -- "$qa" "$target"
Xvfb :147 -screen 0 1440x900x24 -nolisten tcp > "$out/xvfb.log" 2>&1 & vp=$!
trap 'kill "$vp" 2>/dev/null || true' EXIT
for i in $(seq 1 30); do [[ -S /tmp/.X11-unix/X147 ]] && break;sleep .2;done
[[ -S /tmp/.X11-unix/X147 ]]||exit 4
export DISPLAY=:147 LIBGL_ALWAYS_SOFTWARE=1 HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
export HPR_PREFAB_GUI_RECEIPT="$out/actual-editor-window-receipt.txt"
export HPR_PREFAB_GUI_FIRST="$a" HPR_PREFAB_GUI_SECOND="$b"
if command -v openbox >/dev/null; then openbox --sm-disable > "$out/window-manager.log" 2>&1 & wp=$!;trap 'kill "$wp" "$vp" 2>/dev/null || true' EXIT;fi
timeout 100 "$unity" -force-glcore -projectPath "$buyer" \
 -executeMethod HprPrefabParityGraphicalQa.Run -logFile "$out/editor.log" > "$out/stdout.log" 2>&1 & pid=$!
sleep 55
import -display :147 -window root "$out/actual-product-unity-editor-window.png"
[[ -s "$out/actual-product-unity-editor-window.png" && -s "$out/actual-editor-window-receipt.txt" ]] || {
 grep -E 'HPR_PREFAB_GUI_QA_FAILURE|error CS' "$out/editor.log" | tail -25 >&2 || true;exit 5;
}
grep -q HPR_PREFAB_PARITY_GRAPHICAL_NATIVE_PASS "$out/editor.log"
convert "$out/actual-product-unity-editor-window.png" -resize 960x600 -quality 75 "$out/inspection-960.jpg"
cat "$out/actual-editor-window-receipt.txt"
wait "$pid"||true
