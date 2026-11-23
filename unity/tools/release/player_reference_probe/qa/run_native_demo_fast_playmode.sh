#!/usr/bin/env bash
set -euo pipefail
label=${1:?previous actual tested original Unity6 buyer label}
[[ "$label" =~ ^[a-z0-9_-]{4,30}$ ]]||exit 2
root=/data/var/marketplace-account-setup/unity-player-reference-probe-20261123-wave63
project="$root/$label/6000-6-8f1-independent-buyer"
out="$root/$label/real-fast-enter-playmode-receipt.txt"
log="$root/$label/real-fast-enter-playmode.unity.log"
qa=$(cd "$(dirname "$0")" && pwd)/HprProbeQaFastPlaymode.cs
target="$project/Assets/Editor/HprProbeQaFastPlaymode.cs"
unity=/data/apps/Unity/Hub/Editor/6000.6.8f1/Editor/Unity
[[ -x "$unity" && -s "$qa" && -d "$project/Assets/HPRPlayerReferenceProbe" &&
 ! -e "$target" && ! -e "$out" && ! -e "$log" ]] ||exit 3
cp "$qa" "$target"
export HPR_PLAYER_PROBE_FAST_PLAYMODE_OUT="$out"
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
timeout 230 "$unity" -batchmode -nographics -projectPath "$project" \
 -executeMethod HprProbeQaFastPlaymode.Run -logFile "$log" \
 >"$root/$label/real-fast-enter-playmode.stdout" 2>&1 || {
 grep -E 'HPR_PLAYER_PROBE_FAST_PLAYMODE|HPR_PLAYER_PROBE_REAL_UNITY6|error CS[0-9]|Exception' "$log"|tail -22 >&2||true;exit 5;
}
[[ -s "$out" ]]||exit 6
grep -q HPR_PLAYER_PROBE_REAL_UNITY6_FAST_PLAYMODE_NATIVE_PASS "$log"
cat "$out"
