#!/usr/bin/env bash
# Original two-FBX, two-prefab, one-scene Unity authoring only in a fresh
# private project. Never edits an existing customer/project/tool source.
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
base=/data/var/marketplace-account-setup/unity-20261122-wave54/original-real-unity-demo-author
editor=/data/apps/Unity/Hub/Editor/2022.3.22f1/Editor/Unity
[[ ! -e "$base" && -x "$editor" ]] || { echo 'Refusing duplicate original demo author run';exit 3; }
mkdir -p "$base"
project="$base/fresh-original-author-project"
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
run(){
 stage=$1;shift
 echo "FIRST_PARTY_UNITY_DEMO_AUTHOR $stage"
 timeout 450 "$editor" -batchmode -nographics -quit "$@" -logFile "$base/$stage.unity.log" > "$base/$stage.stdout" 2>&1 || {
  grep -E -C2 'error CS|Exception|HPR_ORIGINAL_' "$base/$stage.unity.log" | tail -32 >&2 || :
  exit 5
 }
}
run create -createProject "$project"
cp -a "$root/Assets/HPRFbxSourceTakes" "$project/Assets/"
cp -a "$root/Assets/HPRFbxSourceTakes.meta" "$project/Assets/"
mkdir -p "$project/Assets/Editor"
cp -- "$root/qa/HprFbxDemoSceneAuthor.cs" "$project/Assets/Editor/"
export HPR_SOURCE_TAKE_DEMO_AUTHOR_RECEIPT="$base/real-original-demo-receipt.txt"
run generate-original-Unity-scenes -projectPath "$project" -executeMethod HprFbxDemoSceneAuthor.Generate
grep -q HPR_ORIGINAL_UNITY_SOURCE_TAKE_DEMO_CREATED "$base/generate-original-Unity-scenes.unity.log"
# Copy only the two generated directories (each includes its own files and
# .meta files), then copy the folder metadata separately. Never recurse-copy
# a folder and then mistakenly treat its children as if not already copied.
for dir in Prefabs Scenes; do
 source="$project/Assets/HPRFbxSourceTakes/Samples/$dir"
 target="$root/Assets/HPRFbxSourceTakes/Samples/$dir"
 [[ -d "$source" && -s "$source.meta" && ! -e "$target" && ! -e "$target.meta" ]] || {
  echo "Original Unity demo directory already exists or is missing: $dir" >&2; exit 7;
 }
 cp -a "$source" "$target"
 cp -a "$source.meta" "$target.meta"
 diff -rq "$source" "$target"
 cmp -s "$source.meta" "$target.meta"
done
cat "$base/real-original-demo-receipt.txt"
