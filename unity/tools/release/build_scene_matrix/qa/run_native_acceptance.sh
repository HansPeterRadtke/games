#!/usr/bin/env bash
# Original first-party export, independent clean buyer install, real Build Profile fixtures.
set -euo pipefail
out=${1:?New isolated private evidence directory required}
[[ "$out" = /data/var/marketplace-account-setup/* && ! -e "$out" ]]
qa=$(cd "$(dirname "$0")" && pwd)
src=$(cd "$qa/../Assets" && pwd)
unity=/data/apps/Unity/Hub/Editor/6000.6.8f1/Editor/Unity
[[ -x "$unity" && -f "$src/HPRBuildSceneMatrix/Editor/HprBuildSceneMatrix.cs" ]]
mkdir -p "$out"
export HOME=/home/hans USER=hans LOGNAME=hans DISPLAY=${DISPLAY:-:1} XAUTHORITY=${XAUTHORITY:-/home/hans/.Xauthority}
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
export LP_NUM_THREADS=2
export HPR_MATRIX_ARCHIVE="$out/HPR_Build_Scene_Matrix_original.unitypackage" HPR_MATRIX_RECEIPT="$out/real-profile-receipt.txt"
run(){
 stage=$1;shift;echo "HPR_MATRIX_STAGE $stage"
 timeout 480 "$unity" -batchmode -nographics -quit "$@" -logFile "$out/$stage.unity.log" > "$out/$stage.stdout" 2>&1 || {
 grep -E 'error CS[0-9]|Exception|HPR_MATRIX_' "$out/$stage.unity.log" | tail -30 >&2 || true
 exit 4
 }
}
run author-create -createProject "$out/author"
cp -a "$src"/HPRBuildSceneMatrix "$src"/HPRBuildSceneMatrix.meta "$out/author/Assets/"
mkdir -p "$out/author/Assets/Editor"
cp "$qa/HprBuildSceneMatrixQa.cs" "$out/author/Assets/Editor/"
run author-export -projectPath "$out/author" -executeMethod HprBuildSceneMatrixQa.Export
grep -q HPR_MATRIX_EXPORT_PASS "$out/author-export.unity.log"
python3 "$qa/verify_archive.py" "$HPR_MATRIX_ARCHIVE" "$src" > "$out/archive-identity.json"
run buyer-create -createProject "$out/buyer"
run buyer-import -projectPath "$out/buyer" -importPackage "$HPR_MATRIX_ARCHIVE"
mkdir -p "$out/buyer/Assets/Editor"
cp "$qa/HprBuildSceneMatrixQa.cs" "$out/buyer/Assets/Editor/"
run real-profile-acceptance -projectPath "$out/buyer" -executeMethod HprBuildSceneMatrixQa.Run
grep -q HPR_MATRIX_REAL_PROFILE_PASS "$HPR_MATRIX_RECEIPT"
cat "$HPR_MATRIX_RECEIPT"
echo HPR_MATRIX_NATIVE_ACCEPTANCE_PASS
