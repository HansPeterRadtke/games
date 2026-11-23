#!/usr/bin/env bash
set -euo pipefail
label=${1:?existing unique tested Unity 6 buyer label}
[[ "$label" =~ ^[a-z0-9_-]{3,24}$ ]] || exit 2
root=/data/var/marketplace-account-setup/unity-nested-custom-20261123-wave62
caseid=$label
project="$root/$caseid/6000-6-8f1-independent-buyer"
product=$(cd "$(dirname "$0")/.." && pwd)
qa="$product/qa/HprNestedCustomPlaymodeQa.cs"
editor=/data/apps/Unity/Hub/Editor/6000.6.8f1/Editor/Unity
out="$root/$caseid/real-fast-enter-playmode-receipt.txt"
log="$root/$caseid/real-fast-enter-playmode.unity.log"
private="$project/Assets/Editor/HprNestedCustomPlaymodeQa.cs"
[[ -x "$editor" && -d "$project/Assets/HPRImportedPrefabParity" && -s "$qa" &&
   ! -e "$out" && ! -e "$log" && ! -e "$private" ]] || exit 3
cp -- "$qa" "$private"
export HPR_NESTED_CUSTOM_PLAYMODE_OUT="$out"
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
timeout 230 "$editor" -batchmode -nographics -projectPath "$project" \
 -executeMethod HprNestedCustomPlaymodeQa.Run -logFile "$log" > "$root/$caseid/real-fast-enter-playmode.stdout" 2>&1 || {
 grep -E 'HPR_NESTED_CUSTOM_PLAYMODE|error CS|Exception' "$log" | tail -18 >&2 || true;exit 5;
}
[[ -s "$out" ]] || exit 6
grep -q HPR_NESTED_CUSTOM_PLAYMODE_NATIVE_PASS "$log"
cat "$out"
