#!/usr/bin/env bash
# Re-enter a previously independently imported original Unity2022 buyer project;
# make a fresh private visual UI observation without reimporting or touching the archived source.
set -euo pipefail
label=${1:?new unique private GTK choice test label}
[[ "$label" =~ ^[a-z0-9_-]{4,30}$ ]] || exit 2
root=/data/var/marketplace-account-setup/unity-player-reference-probe-20261123-wave65
previous=/data/var/marketplace-account-setup/unity-player-reference-probe-20261123-wave63
buyer="$root/nativefile65a/independent-native-unity2022-buyer"
work="$root/$label"
unity=/data/apps/Unity/Hub/Editor/2022.3.22f1/Editor/Unity
qa=$(cd "$(dirname "$0")" && pwd)
[[ -x "$unity" && -s "$buyer/Assets/Editor/HprProbeQaFileDialogs.cs" &&
  -s "$buyer/Assets/HPRPlayerReferenceProbe/Runtime/HprPlayerReferenceProbe.cs" &&
  ! -e "$work" && ! -e /tmp/.X11-unix/X143 ]] || {
  echo 'Refusing simultaneous GUI test, previous buyer missing, or a reused private label' >&2;exit 3;
}
mkdir -p "$work"
Xvfb :143 -screen 0 1440x900x24 -nolisten tcp > "$work/xvfb.log" 2>&1 & xv=$!
editor='';wm=''
cleanup(){
 [[ -z "$editor" ]] || { kill "$editor" 2>/dev/null||true;wait "$editor" 2>/dev/null||true; }
 [[ -z "$wm" ]]|| kill "$wm" 2>/dev/null||true
 kill "$xv" 2>/dev/null||true
}
trap cleanup EXIT
for i in $(seq 1 40);do [[ -S /tmp/.X11-unix/X143 ]] && break;sleep .2;done
[[ -S /tmp/.X11-unix/X143 ]] || exit 4
export DISPLAY=:143 LIBGL_ALWAYS_SOFTWARE=1 HOME=/home/hans USER=hans LOGNAME=hans
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
export HPR_DIALOG_QA_ROOT="$work"
export HPR_DIALOG_EXPORTED_FILE="$work/actual-exported-by-real-save-dialog.json"
export HPR_DIALOG_BASELINE_FILE="$previous/resources63a/editor-original-baseline.json"
export HPR_DIALOG_PLAYER_FILE="$previous/resources63a/actual-player-receipt.json"
if command -v openbox >/dev/null;then openbox --sm-disable > "$work/wm.log" 2>&1 & wm=$!;fi
"$unity" -force-glcore -projectPath "$buyer" -executeMethod HprProbeQaFileDialogs.Run \
 -logFile "$work/real-GUI.log" >"$work/real-GUI.stdout" 2>&1 & editor=$!
for i in $(seq 1 120);do
 [[ -s "$work/ready.txt" ]]&&break
 if ! kill -0 "$editor" 2>/dev/null;then break;fi
 sleep 1
done
[[ -s "$work/ready.txt" ]] || {
 import -display :143 -window root "$work/native-GUI-initialization-failure.png" ||true;
 echo 'Did not establish actual Editor window; no legal dialog accepted.' >&2;exit 5;
}
import -display :143 -window root "$work/before-native-file-dialogs.png"
cat "$work/ready.txt"
for i in $(seq 1 650);do
 [[ -s "$work/comparison-complete.txt" ]] && break
 [[ ! -f "$work/error.txt" ]] || { cat "$work/error.txt" >&2;exit 6; }
 if ! kill -0 "$editor" 2>/dev/null;then break;fi
 sleep 1
done
[[ -s "$work/comparison-complete.txt" ]] || {
 import -display :143 -window root "$work/native-partial-file-dialog-evidence.png" ||true;
 echo 'File-dialog interaction incomplete, do not claim all UI controls verified.' >&2;exit 7;
}
import -display :143 -window root "$work/actual-complete-native-file-dialog-qa.png"
cat "$work/inspected.txt" "$work/exported.txt" "$work/existing-baseline-selected.txt" \
 "$work/actual-player-selected.txt" "$work/comparison-complete.txt"
