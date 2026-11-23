#!/usr/bin/env bash
# Native 2022 Editor UI screenshot of already-validated imported demo; no terms acceptance.
set -euo pipefail
label=${1:?existing independent buyer label}
name=${2:?fresh graphical run label}
[[ "$label" =~ ^[a-z0-9_-]{4,30}$ && "$name" =~ ^[a-z0-9_-]{4,30}$ ]]||exit 2
root=/data/var/marketplace-account-setup/unity-player-reference-probe-20261123-wave63
project="$root/$label/2022-3-22f1-independent-buyer"
out="$root/$label/editor-visual-$name"
qa=$(cd "$(dirname "$0")" && pwd)/HprProbeQaDemoGraphical.cs
unity=/data/apps/Unity/Hub/Editor/2022.3.22f1/Editor/Unity
[[ -x "$unity" && -s "$qa" && -d "$project/Assets/HPRPlayerReferenceProbe" &&
  ! -e "$project/Assets/Editor/HprProbeQaDemoGraphical.cs" &&
  ! -e "$out" && ! -e /tmp/.X11-unix/X145 ]]||{
 echo 'Cannot safely enter this already-tested actual original buyer Editor' >&2;exit 3;
}
mkdir -p "$out"
cp "$qa" "$project/Assets/Editor/HprProbeQaDemoGraphical.cs"
Xvfb :145 -screen 0 1440x900x24 -nolisten tcp >"$out/xvfb.log" 2>&1 & xv=$!
editor='';wm=''
cleanup(){
 [[ -z "$editor" ]]||{ kill "$editor" 2>/dev/null||true;wait "$editor" 2>/dev/null||true;}
 [[ -z "$wm" ]]||kill "$wm" 2>/dev/null||true
 kill "$xv" 2>/dev/null||true
}
trap cleanup EXIT
for i in $(seq 1 60);do [[ -S /tmp/.X11-unix/X145 ]]&&break;sleep .2;done
[[ -S /tmp/.X11-unix/X145 ]]||exit 4
export DISPLAY=:145 LIBGL_ALWAYS_SOFTWARE=1
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
export HPR_REAL_DEMO_GUI_RECEIPT="$out/original-unity-editor-window.txt"
if command -v openbox >/dev/null;then openbox --sm-disable >"$out/window-manager.log" 2>&1 & wm=$!;fi
"$unity" -force-glcore -projectPath "$project" -executeMethod HprProbeQaDemoGraphical.Run \
 -logFile "$out/actual-original-editor.log" >"$out/actual-original-editor.stdout" 2>&1 & editor=$!
for i in $(seq 1 65);do
 [[ -s "$out/original-unity-editor-window.txt" ]]&&break
 if ! kill -0 "$editor" 2>/dev/null;then break;fi
 sleep 1
done
sleep 4
import -display :145 -window root "$out/actual-native-original-unity-editor.png"
convert "$out/actual-native-original-unity-editor.png" -resize 900x563 -quality 73 \
 "$out/manual-editor-window-inspection.jpg"
if [[ ! -s "$out/original-unity-editor-window.txt" ]] ||
 ! grep -q HPR_ORIGINAL_REAL_EDITOR_PRODUCT_WINDOW_QA_PASS "$out/actual-original-editor.log";then
 echo 'GUI blocked or did not open. Original screenshot retained; never accept any legal dialog.' >&2
 grep -E 'HPR_REAL_EDITOR_WINDOW_QA_FAIL|error CS[0-9]|Exception' "$out/actual-original-editor.log"|tail -12 >&2 || true
 exit 5
fi
cat "$out/original-unity-editor-window.txt"
printf 'ACTUAL_UNITY_EDITOR_WINDOW_OPENED_AND_CAPTURED_FOR_MANUAL_VISUAL_REVIEW\n'
