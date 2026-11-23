#!/usr/bin/env bash
# Private actual X11 mouse interaction test in fresh Unity2022 buyer copy.
# Deliberately does not auto-click; operator must inspect first. No source mutation/publishing.
# Never accept software terms or other legal dialogs. Abort if the native GUI shows one.
set -euo pipefail
label=${1:?fresh original private test label}
[[ "$label" =~ ^[a-z0-9_-]{4,30}$ ]]||exit 2
root=/data/var/marketplace-account-setup/unity-player-reference-probe-20261123-wave65
prior=/data/var/marketplace-account-setup/unity-player-reference-probe-20261123-wave63
work="$root/$label"
project="$work/independent-native-unity2022-buyer"
qa=$(cd "$(dirname "$0")" && pwd)
unity=/data/apps/Unity/Hub/Editor/2022.3.22f1/Editor/Unity
archive="$prior/retail2022final64/HPR_Player_Reference_Probe_Unity2022_original.unitypackage"
[[ -x "$unity" && -s "$archive" && ! -e "$work" && ! -e /tmp/.X11-unix/X143 ]]||{
 echo 'Missing original immutable archive or already used GUI evidence label' >&2;exit 3;
}
mkdir -p "$work"
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
run(){ name=$1;shift;echo "HPR_ACTUAL_NATIVE_CLICK_STAGE $name";
 timeout 360 "$unity" -batchmode -nographics -quit "$@" -logFile "$work/$name.unity.log" \
 >"$work/$name.stdout" 2>&1 || {
  grep -E 'HPR_|error CS[0-9]|Exception' "$work/$name.unity.log" |tail -25 >&2||true;exit 5;
 }
}
run create-clean-buyer -createProject "$project"
run install-original-buyer-package -projectPath "$project" -importPackage "$archive"
[[ -s "$project/Assets/HPRPlayerReferenceProbe/Editor/HprPlayerReferenceProbeWindow.cs" ]]||exit 6
mkdir -p "$project/Assets/Editor"
cp "$qa/HprProbeQaActualClicks.cs" "$project/Assets/Editor/"
Xvfb :143 -screen 0 1440x900x24 -nolisten tcp >"$work/xvfb.log" 2>&1 & xv=$!
editor='';wm=''
cleanup(){
 [[ -z "$editor" ]]||{ kill "$editor" 2>/dev/null||true;wait "$editor" 2>/dev/null||true;}
 [[ -z "$wm" ]]||kill "$wm" 2>/dev/null||true
 kill "$xv" 2>/dev/null||true
}
trap cleanup EXIT
for i in $(seq 1 50);do [[ -S /tmp/.X11-unix/X143 ]]&&break;sleep .2;done
[[ -S /tmp/.X11-unix/X143 ]]||exit 7
export DISPLAY=:143 LIBGL_ALWAYS_SOFTWARE=1
export HPR_ACTUAL_UI_ROOT="$work"
export HPR_ACTUAL_UI_BASELINE="$prior/resources63a/editor-original-baseline.json"
export HPR_ACTUAL_UI_PLAYER="$prior/resources63a/actual-player-receipt.json"
if command -v openbox >/dev/null;then openbox --sm-disable >"$work/wm.log" 2>&1 & wm=$!;fi
"$unity" -force-glcore -projectPath "$project" -executeMethod HprProbeQaActualClicks.Run \
 -logFile "$work/real-GUI.log" >"$work/real-GUI.stdout" 2>&1 & editor=$!
for i in $(seq 1 95);do
 [[ -s "$work/ready.txt" ]]&&break
 if ! kill -0 "$editor" 2>/dev/null;then break;fi
 sleep 1
done
[[ -s "$work/ready.txt" ]]||{
 echo 'Native Editor did not reach opt-in UI ready state; preserve screenshot and do not accept terms' >&2;
 import -display :143 -window root "$work/first-run-blocker.png"||true;
 grep -E 'HPR_ACTUAL_UI|error CS[0-9]|Exception' "$work/real-GUI.log"|tail -16 >&2||true;exit 8;
}
import -display :143 -window root "$work/before-real-button-clicks.png"
echo "HPR_ACTUAL_MOUSE_BUTTONS_READY $(cat "$work/ready.txt")"
for i in $(seq 1 260);do
 [[ -s "$work/compared-by-actual-click.txt" ]]&&break
 if [[ -f "$work/error.txt" ]];then cat "$work/error.txt" >&2;exit 9;fi
 if ! kill -0 "$editor" 2>/dev/null;then break;fi
 sleep 1
done
[[ -s "$work/compared-by-actual-click.txt" ]]||{
 echo 'Not all click results confirmed. Did not silently claim success.' >&2;
 import -display :143 -window root "$work/partial-after-clicks.png"||true;
 exit 10;
}
import -display :143 -window root "$work/after-actual-real-button-clicks.png"
cat "$work/scanned-by-actual-click.txt" "$work/compared-by-actual-click.txt"
