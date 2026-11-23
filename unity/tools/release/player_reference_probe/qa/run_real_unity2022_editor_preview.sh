#!/usr/bin/env bash
set -euo pipefail
origin=${1:?existing immutable first-party package author label}
label=${2:?unique unmodified Unity2022 GUI test case}
[[ "$origin" =~ ^[a-z0-9_-]{4,30}$ && "$label" =~ ^[a-z0-9_-]{4,30}$ ]]||exit 2
root=/data/var/marketplace-account-setup/unity-player-reference-probe-20261123-wave63
package="$root/$origin/HPR_Player_Reference_Probe_original.unitypackage"
work="$root/$label"
project="$work/independent-buyer-project"
qa=$(cd "$(dirname "$0")" && pwd)
unity=/data/apps/Unity/Hub/Editor/2022.3.22f1/Editor/Unity
[[ -x "$unity" && -s "$package" && ! -e "$work" && ! -e /tmp/.X11-unix/X147 ]] ||{
 echo 'Refusing repeated GUI effect or missing original source' >&2;exit 3;
}
mkdir -p "$work"
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
run(){ name=$1;shift;echo "HPR_PLAYER_PROBE_UNITY2022_ORIGINAL_STAGE $name";
 timeout 420 "$unity" -batchmode -nographics -quit "$@" -logFile "$work/$name.unity.log" \
 >"$work/$name.stdout" 2>&1 || {
 grep -E 'HPR_PROBE|HPR_PLAYER|error CS[0-9]|Exception' "$work/$name.unity.log" |tail -25 >&2||true;exit 5;
 }
}
run create-buyer -createProject "$project"
run original-package-import -projectPath "$project" -importPackage "$package"
mkdir -p "$project/Assets/HPRPrivateQa" "$project/Assets/Editor"
cp "$qa/HprProbeQaItem.cs" "$qa/HprProbeQaAutoExit.cs" \
 "$qa/HprProbeQaPlayerOnlyClear.cs" "$project/Assets/HPRPrivateQa/"
cp "$qa/HprProbeQaBuild.cs" "$project/Assets/Editor/"
export HPR_PROBE_QA_ROOT="$work" HPR_PROBE_QA_EDITOR_ONLY=1
run native-real-Editor-only-source-acceptance -projectPath "$project" -executeMethod HprProbeQaBuild.Run
grep -q 'HPR_PROBE_PRIVATE_REAL_EDITOR_ONLY_ACCEPTANCE_PASS 2022.3.22f1' \
 "$work/native-real-Editor-only-source-acceptance.unity.log"
cp "$qa/HprProbeQaGraphicalEditorOnly.cs" "$project/Assets/Editor/"
mkdir -p "$work/graphical"
Xvfb :147 -screen 0 1440x900x24 -nolisten tcp > "$work/graphical/xvfb.log" 2>&1 & xv=$!
trap 'kill "$xv" 2>/dev/null || true' EXIT
for i in $(seq 1 30);do [[ -S /tmp/.X11-unix/X147 ]]&&break;sleep .2;done
[[ -S /tmp/.X11-unix/X147 ]]||exit 6
export DISPLAY=:147 LIBGL_ALWAYS_SOFTWARE=1
export HPR_PROBE_QA_GUI_RECEIPT="$work/graphical/native-gui-receipt.txt"
if command -v openbox >/dev/null;then openbox --sm-disable >"$work/graphical/wm.log" 2>&1 & wm=$!;trap 'kill "$wm" "$xv" 2>/dev/null || true' EXIT;fi
(timeout 132 "$unity" -force-glcore -projectPath "$project" \
 -executeMethod HprProbeQaGraphicalEditorOnly.Run \
 -logFile "$work/graphical/native-editor.log" \
 >"$work/graphical/native-editor.stdout" 2>&1) & gui=$!
sleep 59
import -display :147 -window root "$work/graphical/actual-original-unity2022-editor.png"
[[ -s "$work/graphical/native-gui-receipt.txt" && \
   -s "$work/graphical/actual-original-unity2022-editor.png" ]] || {
 grep -E 'HPR_PLAYER_PROBE_EDITOR_ONLY_GUI_QA_FAILURE|error CS|Exception' "$work/graphical/native-editor.log"|tail -20 >&2||true;exit 7;
}
grep -q HPR_PLAYER_REFERENCE_REAL_EDITOR_ONLY_GRAPHICAL_PASS "$work/graphical/native-editor.log"
convert "$work/graphical/actual-original-unity2022-editor.png" -resize 900x563 -quality 73 \
 "$work/graphical/visual-inspection-900.jpg"
cat "$work/graphical/native-gui-receipt.txt"
wait "$gui" ||true
