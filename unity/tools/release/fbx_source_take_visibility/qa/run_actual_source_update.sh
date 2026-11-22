#!/usr/bin/env bash
# Tests actual change from one original Blender Action to two while the Unity
# importer retains one customized clip list, in a NEW disposable buyer project.
set -euo pipefail
version=${1:?installed Unity Editor version}
[[ "$version" = 2022.3.22f1 || "$version" = 6000.6.8f1 ]] || exit 2
root=$(cd "$(dirname "$0")/.." && pwd)
base=/data/var/marketplace-account-setup/unity-20261122-wave55
out="$base/actual-one-to-two-take-reexport-${version//./-}"
unity=/data/apps/Unity/Hub/Editor/$version/Editor/Unity
initial="$base/original-fbx-fixture/HPRFirstTakeOnly.fbx"
second="$root/Assets/HPRFbxSourceTakes/Samples/HPRTwoTakeCube.fbx"
[[ -x "$unity" && -s "$initial" && -s "$second" && ! -e "$out" ]] || {
 echo 'Invalid/repeated actual source-update test effect' >&2; exit 3; }
mkdir -p "$out"
project="$out/disposable-buyer-project"
sha256sum "$initial" "$second" > "$out/first-party-inputs-before.sha256"
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
run(){
 stage=$1; shift
 echo "ACTUAL_ONE_TO_TWO_TAKES $version $stage"
 timeout 500 "$unity" -batchmode -nographics -quit "$@" -logFile "$out/$stage.unity.log" > "$out/$stage.stdout" 2>&1 || {
  grep -E -C2 'error CS|Exception|HPR_ACTUAL_|executeMethod' "$out/$stage.unity.log" | tail -40 >&2 || :
  exit 5
 }
}
run create -createProject "$project"
mkdir -p "$project/Assets/HPRPrivateSourceChange" "$project/Assets/Editor"
cp -- "$initial" "$project/Assets/HPRPrivateSourceChange/Source.fbx"
cp -- "$root/qa/HprFbxSourceTakeNativeQa.cs" "$project/Assets/Editor/"
cp -a "$root/Assets/HPRFbxSourceTakes" "$project/Assets/"
cp -a "$root/Assets/HPRFbxSourceTakes.meta" "$project/Assets/"
export HPR_SOURCE_TAKE_CUSTOM_QA_DIR="$out"
run prepare-original-custom-import -projectPath "$project" -executeMethod HprFbxSourceTakeNativeQa.PrepareActualSourceChange
grep -q HPR_ACTUAL_ONE_TAKE_CUSTOMIZED_BEFORE_SOURCE_UPDATE_PASS "$out/prepare-original-custom-import.unity.log"
# Intentional data change ONLY in the new disposable first-party FBX. The
# original authored one-take/two-take files are preserved exactly.
test -f "$project/Assets/HPRPrivateSourceChange/Source.fbx"
cp -- "$second" "$project/Assets/HPRPrivateSourceChange/Source.fbx"
run reimport-changed-Blender-source -projectPath "$project" -executeMethod HprFbxSourceTakeNativeQa.AuditActualSourceChange
grep -q HPR_ACTUAL_FBX_SOURCE_UPDATE_VISIBILITY_PASS "$out/reimport-changed-Blender-source.unity.log"
sha256sum "$initial" "$second" > "$out/first-party-inputs-after.sha256"
diff -u "$out/first-party-inputs-before.sha256" "$out/first-party-inputs-after.sha256"
grep -q 'original_one_to_two_take_source_change_diagnostic=PASS' "$out/source-change-after.txt"
cat "$out/source-change-before.txt" "$out/source-change-after.txt"
