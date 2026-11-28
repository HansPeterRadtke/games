#!/usr/bin/env bash
# Private Xvfb screenshot and actual mouse-click scan on self-owned Unity project.
set -euo pipefail
out=${1:?Actual test output folder is required}
project="$out/buyer"
# Optional independent output folder preserves earlier exact GUI evidence.
visual=${2:-$out}
qa=$(cd "$(dirname "$0")" && pwd)
unity=${UNITY_BIN:-/data/apps/Unity/Hub/Editor/6000.6.8f1/Editor/Unity}
[[ "$out" = /data/var/marketplace-account-setup/* &&
   "$visual" = /data/var/marketplace-account-setup/* &&
   -f "$project/Assets/HPRAnimationEventAudit/Editor/HprAnimationEventAudit.cs" ]]
[[ -f "$out/real-native-event-receipt.txt" && ! -e "$visual/actual-event-audit-editor.png" && ! -e /tmp/.X147-lock ]] || { echo 'Missing verified native result, image exists or private display busy'; exit 3; }
[[ -d "$visual" && ! -L "$visual" ]] || { echo 'Use an existing real private evidence directory'; exit 3; }
mkdir -p "$project/Assets/Editor"
cp "$qa/HprEventAuditPreview.cs" "$project/Assets/Editor/HprEventAuditPreview.cs"
export HOME=/home/hans USER=hans LOGNAME=hans DISPLAY=:147 XAUTHORITY=/home/hans/.Xauthority
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus LP_NUM_THREADS=2
Xvfb :147 -screen 0 1680x1050x24 -nolisten tcp >"$visual/native-gui-xvfb.log" 2>&1 &
xvfb_pid=$!
editor_pid=''
cleanup(){
 if [[ -n "$editor_pid" ]] && kill -0 "$editor_pid" 2>/dev/null; then
   kill -TERM "$editor_pid" 2>/dev/null || true
   for i in {1..10}; do kill -0 "$editor_pid" 2>/dev/null || break; sleep 1; done
   if kill -0 "$editor_pid" 2>/dev/null; then kill -KILL "$editor_pid" 2>/dev/null || true; fi
 fi
 if [[ -n "$editor_pid" ]]; then wait "$editor_pid" 2>/dev/null || true; fi
 kill -TERM "$xvfb_pid" 2>/dev/null || true
 wait "$xvfb_pid" 2>/dev/null || true
}
trap cleanup EXIT
for i in {1..15}; do [[ -S /tmp/.X11-unix/X147 ]] && break; sleep 1; done
[[ -S /tmp/.X11-unix/X147 ]] || { echo 'Xvfb did not start'; exit 4; }
"$unity" -projectPath "$project" -executeMethod HprEventAuditPreview.Open -logFile "$visual/native-gui-editor.unity.log" >"$visual/native-gui-editor.stdout" 2>&1 &
editor_pid=$!
window=''
for i in {1..135}; do
 kill -0 "$editor_pid" 2>/dev/null || { echo 'Unity Editor exited before screenshot'; exit 5; }
 if grep -q 'HPR_ANIMATION_EVENT_REAL_PREVIEW_READY' "$visual/native-gui-editor.unity.log" 2>/dev/null; then
   window=$(xdotool search --onlyvisible --name 'Animation Event Audit' 2>/dev/null | tail -1 || true)
   [[ -z "$window" ]] || break
 fi
 sleep 2
done
[[ -n "$window" ]] || { echo 'Native Editor audit window unavailable'; exit 6; }
xdotool windowraise "$window" 2>/dev/null || true
sleep 3
import -window "$window" "$visual/actual-event-audit-editor.png"
[[ -s "$visual/actual-event-audit-editor.png" ]]
# Mouse click uses coordinates relative to the actual test-only window. Scan
# button is below the informational banner AND optional scope folder field;
# verify the click through the actual Unity rescan callback.
xdotool mousemove --window "$window" 480 112 click 1
for i in {1..12}; do
 if grep -q 'HPR_ANIMATION_EVENT_REAL_BUTTON_RESCAN_PASS' "$visual/native-gui-editor.unity.log"; then break; fi
 sleep 1
done
if grep -q 'HPR_ANIMATION_EVENT_REAL_BUTTON_RESCAN_PASS' "$visual/native-gui-editor.unity.log"; then
 import -window "$window" "$visual/actual-event-audit-after-click.png"
 # Show findings that naturally fall below the first screen in larger audits.
 xdotool mousemove --window "$window" 510 455 click --repeat 6 --delay 100 5
 sleep 2
 import -window "$window" "$visual/actual-event-audit-scrolled-details.png"
 echo HPR_EVENT_UI_BUTTON_SCAN_AND_SCREENSHOT_PASS
else
 echo HPR_EVENT_UI_SCREENSHOT_RETAINED_BUT_BUTTON_INTERACTION_FAILED
 exit 8
fi
