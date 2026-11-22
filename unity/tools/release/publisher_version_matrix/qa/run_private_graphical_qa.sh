#!/usr/bin/env bash
set -euo pipefail
label=${1:?fresh unique graphical evidence label}
[[ "$label" =~ ^[a-z0-9_-]{4,25}$ ]]||exit 2
root=/data/var/marketplace-account-setup/unity-publisher-matrix-20261122-wave58
out="$root/graphical-windows-$label"
[[ ! -e "$out" && ! -e /tmp/.X11-unix/X141 ]] || { echo 'Refusing repeated or occupied GUI effect' >&2; exit 3; }
mkdir -p "$out"
source=$(cd "$(dirname "$0")" && pwd)
buyer=/data/var/marketplace-account-setup/unity-publisher-matrix-20261122-v1/2022-3-22f1-hashwave58a/independent-buyer-project
first=/data/var/marketplace-account-setup/unity-publisher-matrix-20261122-v1/2022-3-22f1-hashwave58a/independent-buyer-import-snapshot.json
second=/data/var/marketplace-account-setup/unity-publisher-matrix-20261122-v1/6000-6-8f1-hashwave58a/independent-buyer-import-snapshot.json
qa="$buyer/Assets/Editor/HprPublisherVersionGraphicalQa.cs"
[[ -d "$buyer/Assets/HPRPublisherVersionMatrix" && -s "$first" && -s "$second" && ! -e "$qa" ]]||exit 4
cp "$source/HprPublisherVersionGraphicalQa.cs" "$qa"
Xvfb :141 -screen 0 1600x920x24 -nolisten tcp > "$out/xvfb.log" 2>&1 & vp=$!
trap 'kill "$vp" 2>/dev/null || true' EXIT
for i in $(seq 1 30);do [[ -S /tmp/.X11-unix/X141 ]]&&break;sleep .2;done
[[ -S /tmp/.X11-unix/X141 ]]||exit 5
export DISPLAY=:141 LIBGL_ALWAYS_SOFTWARE=1 HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
export HPR_VERSION_GUI_QA_RECEIPT="$out/real-window-proof.txt"
export HPR_VERSION_GUI_FIRST="$first"
export HPR_VERSION_GUI_SECOND="$second"
if command -v openbox >/dev/null;then openbox --sm-disable > "$out/window-manager.log" 2>&1 & wp=$!;trap 'kill "$wp" "$vp" 2>/dev/null || true' EXIT;fi
unity=/data/apps/Unity/Hub/Editor/2022.3.22f1/Editor/Unity
timeout 100 "$unity" -force-glcore -projectPath "$buyer" -executeMethod HprPublisherVersionGraphicalQa.Run -logFile "$out/editor.log" > "$out/stdout.log" 2>&1 & p=$!
sleep 52
import -display :141 -window root "$out/actual-two-editor-windows.png"
[[ -s "$out/actual-two-editor-windows.png" && -s "$out/real-window-proof.txt" ]]||{
 echo 'Real native window evidence not produced' >&2;grep -E 'HPR_VERSION_GUI|error CS' "$out/editor.log"|tail -20 >&2||true;exit 6;
}
grep -q HPR_VERSION_GRAPHICAL_NATIVE_QA_PASS "$out/editor.log"
convert "$out/actual-two-editor-windows.png" -resize 1200x690 -quality 83 "$out/inspection.jpg"
cat "$out/real-window-proof.txt"
wait "$p"||true
