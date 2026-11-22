#!/usr/bin/env bash
set -euo pipefail
repo=/data/src/worktrees/unity-package-boundary-audit-20261121
root=/data/var/marketplace-account-setup/unity-20261122-wave55
project="$root/combined-animation-native-6000-6-8f1-clip-prefab-fix1/independent-buyer-project"
source="$repo/unity/tools/release/animation_import_preflight_bundle/qa/HprOriginalFastEnterPlaymodeQa.cs"
unity=/data/apps/Unity/Hub/Editor/6000.6.8f1/Editor/Unity
out="$root/fast-enter-playmode-6000-6-8f1-real-original-buyer.txt"
log="$root/fast-enter-playmode-6000-6-8f1-real-original-buyer.unity.log"
[[ -x "$unity" && -d "$project/Assets/HPRAnimationImportPreflight" && ! -e "$out" && ! -e "$log" && -s "$source" ]] || exit 3
private="$project/Assets/Editor/HprOriginalFastEnterPlaymodeQa.cs"
[[ ! -e "$private" ]] || exit 3
cp -- "$source" "$private"
export HPR_ORIGINAL_FAST_PLAYMODE_QA_OUT="$out"
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
echo 'Testing native Unity 6.6 enter-and-exit Play Mode with domain reload disabled on disposable original buyer source'
# The private QA itself calls EditorApplication.Exit only after recording
# both actual transitions and the equivalent source scanner results.
timeout 230 "$unity" -batchmode -nographics -projectPath "$project" \
 -executeMethod HprOriginalFastEnterPlaymodeQa.Run -logFile "$log" \
 > "$root/fast-enter-playmode-6000-6-8f1-real-original-buyer.stdout" 2>&1 || {
 grep -E -C2 'error CS|Exception|HPR_ORIGINAL_FAST' "$log" | tail -50 >&2 || true
 exit 5
}
[[ -s "$out" ]] || { echo 'No real native Playmode proof observed' >&2;exit 7; }
grep -q HPR_ORIGINAL_FAST_PLAYMODE_NATIVE_PASS "$log"
cat "$out"
