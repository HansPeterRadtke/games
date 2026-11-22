#!/usr/bin/env bash
set -euo pipefail
repo=/data/src/worktrees/unity-package-boundary-audit-20261121
source="$repo/unity/tools/release/fbx_source_take_visibility/Assets/HPRFbxSourceTakes"
qa="$repo/unity/tools/release/fbx_source_take_visibility/qa/HprOriginalSampleCaptionRepair.cs"
base=/data/var/marketplace-account-setup/unity-20261122-wave55
out="$base/original-two-caption-repair-author-2022"
unity=/data/apps/Unity/Hub/Editor/2022.3.22f1/Editor/Unity
[[ ! -e "$out" && -x "$unity" && -s "$qa" ]] || exit 3
mkdir -p "$out"
project="$out/fresh-original-author-project"
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
run(){
 stage=$1;shift
 echo "REAL_UNITY_ORIGINAL_CAPTION $stage"
 timeout 480 "$unity" -batchmode -nographics -quit "$@" -logFile "$out/$stage.unity.log" > "$out/$stage.stdout" 2>&1 || {
 grep -E -C2 'error CS|Exception|HPR_ORIGINAL_' "$out/$stage.unity.log" | tail -35 >&2 || :;exit 5;
 }
}
run create -createProject "$project"
cp -a "$source" "$project/Assets/"
cp -a "$source.meta" "$project/Assets/"
mkdir -p "$project/Assets/Editor"
cp -- "$qa" "$project/Assets/Editor/"
export HPR_ORIGINAL_CAPTION_REPAIR_QA_OUT="$out/original-prefab-caption-repair-receipt.txt"
run update-real-two-original-prefabs -projectPath "$project" -executeMethod HprOriginalSampleCaptionRepair.Run
grep -q HPR_ORIGINAL_TWO_PREFAB_CAPTION_REPAIR_PASS "$out/update-real-two-original-prefabs.unity.log"
for name in OriginalAutoTwoTake OriginalConfiguredMissingTake; do
 orig="$source/Samples/Prefabs/$name.prefab"
 fixed="$project/Assets/HPRFbxSourceTakes/Samples/Prefabs/$name.prefab"
 [[ -s "$orig" && -s "$fixed" ]] || exit 7
 # Exact associated Unity GUID metadata must be unchanged.
 cmp "$orig.meta" "$fixed.meta"
done
cat "$HPR_ORIGINAL_CAPTION_REPAIR_QA_OUT"
