#!/usr/bin/env bash
# Isolated owner-only non-batch Editor GUI observation, no ToS interaction.
set -euo pipefail
root=$(cd "$(dirname "$0")" && pwd)
version=2022.3.22f1
unity=/data/apps/Unity/Hub/Editor/$version/Editor/Unity
existing=/data/var/marketplace-account-setup/unity-20261121-wave51/native-2022-3-22f1-examples-final1
project="$existing/fresh-independent-buyer-project"
evidence=/data/var/marketplace-account-setup/unity-20261121-wave51/gui-2022-isolated-preferences
[[ ! -e "$evidence" && -x "$unity" && -s "$existing/buyer-qa-evidence/native-receipt.txt" &&
   -d "$project/Assets/HPRArchivePreflight" && ! -e /tmp/.X11-unix/X98 ]] || {
    echo 'Refusing unsafe/repeated isolated GUI acceptance attempt' >&2;exit 4;}
mkdir -p "$evidence/isolated-config" "$evidence/isolated-cache"
mkdir -p "$project/Assets/Editor"
[[ ! -e "$project/Assets/Editor/HprArchivePreflightGraphicalOpen.cs" ]] || exit 5
cp -- "$root/HprArchivePreflightGraphicalOpen.cs" "$project/Assets/Editor/"
Xvfb :98 -screen 0 1440x900x24 -nolisten tcp -ac > "$evidence/xvfb.log" 2>&1 &
xvfb=$!
cleanup() {
 if [[ -n "${unity_pid:-}" ]]; then
  kill "$unity_pid" 2>/dev/null || :
  wait "$unity_pid" 2>/dev/null || :
 fi
 kill "$xvfb" 2>/dev/null || :
 wait "$xvfb" 2>/dev/null || :
}
trap cleanup EXIT
sleep 3
kill -0 "$xvfb" || exit 6
export HOME=/home/hans USER=hans LOGNAME=hans DISPLAY=:98
export XDG_CONFIG_HOME="$evidence/isolated-config" XDG_CACHE_HOME="$evidence/isolated-cache"
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
export LIBGL_ALWAYS_SOFTWARE=1 HPR_PREFLIGHT_GUI_ACCEPTANCE=1
# Explicitly no switches to accept/decline/bypass Unity Terms. Capture actual
# display state only; screenshots are NOT automatically approved marketing art.
timeout -k 6 95 "$unity" -projectPath "$project" -force-glcore \
 -logFile "$evidence/unity-editor.log" > "$evidence/unity-editor.stdout" 2>&1 &
unity_pid=$!
for sec in $(seq 1 80); do
 sleep 1
 if [[ "$sec" == 20 || "$sec" == 40 || "$sec" == 65 ]]; then
  file="$evidence/screenshot-${sec}s.png"
  test ! -e "$file" || exit 7
  import -display :98 -window root "$file" > "$evidence/capture-${sec}s.stdout" 2>&1 || :
  [[ -s "$file" ]] && echo "ORIGINAL_UNRETOUCHED_DISPLAY_CAPTURE $sec $(stat -c%s "$file")" || echo "SCREENSHOT_CAPTURE_UNAVAILABLE $sec"
 fi
 if ! kill -0 "$unity_pid" 2>/dev/null; then
  echo "UNITY_EDITOR_PROCESS_EXITED_AT_SECONDS $sec";break
 fi
done
printf '===GUI_ONLY_RELEVANT_LOG===\n'
grep -nE 'HPR_GUI_PREFLIGHT_WINDOW_OPEN_ATTEMPTED|Software Terms|Crash|SIGSEGV|Fatal|error CS' "$evidence/unity-editor.log" 2>/dev/null | tail -16 || :
find "$evidence" -maxdepth 1 -name 'screenshot-*.png' -type f -printf '%f %s bytes\n'
