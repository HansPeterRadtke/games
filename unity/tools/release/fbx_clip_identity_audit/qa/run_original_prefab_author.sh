#!/usr/bin/env bash
# Original first-party prefab author, fresh disposable Unity 2022 project.
# Does not change the retail source until the separate source verification.
set -euo pipefail
base=/data/var/marketplace-account-setup/unity-20261122-wave55
out=$base/original-clip-id-prefab-author-2022
repo=/data/src/worktrees/unity-package-boundary-audit-20261121
vendor=$repo/unity/tools/release/fbx_clip_identity_audit
unity=/data/apps/Unity/Hub/Editor/2022.3.22f1/Editor/Unity
original=$base/OriginalMotionBaked.fbx
[[ ! -e "$out" && -x "$unity" && -s "$original" ]] || {
 echo 'Missing original model or duplicate prefab author work' >&2; exit 3;
}
mkdir -p "$out"
project=$out/fresh-original-unity-project
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
run(){
 stage=$1;shift
 echo "CLIP_ID_PREFAB_AUTHOR $stage"
 timeout 470 "$unity" -batchmode -nographics -quit "$@" -logFile "$out/$stage.unity.log" > "$out/$stage.stdout" 2>&1 || {
 grep -E -C 2 'error CS|Exception|HPR_CLIP_ID' "$out/$stage.unity.log" | tail -30 >&2 || true;exit 5;
 }
}
run create -createProject "$project"
cp -a "$vendor/Assets/HPRFbxClipIdentity" "$project/Assets/"
cp -a "$vendor/Assets/HPRFbxClipIdentity.meta" "$project/Assets/"
cp -- "$original" "$project/Assets/HPRFbxClipIdentity/Samples/OriginalMotion.fbx"
mkdir -p "$project/Assets/Editor"
cp -- "$vendor/qa/HprOriginalClipIdPrefabAuthor.cs" "$project/Assets/Editor/"
export HPR_CLIP_ID_PREFAB_AUTHOR_RECEIPT="$out/prefab-original-author-receipt.txt"
run first-party-prefab -projectPath "$project" -executeMethod HprOriginalClipIdPrefabAuthor.Build
grep -q HPR_CLIP_ID_PREFAB_NATIVE_AUTHOR_PASS "$out/first-party-prefab.unity.log"
cat "$HPR_CLIP_ID_PREFAB_AUTHOR_RECEIPT"
