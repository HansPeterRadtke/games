#!/usr/bin/env bash
# Fresh Unity 6 Editor export/import/native fixture; private buyer projects only.
set -euo pipefail
out=${1:?New private evidence directory required}
[[ "$out" = /data/var/marketplace-account-setup/* && ! -e "$out" ]] || { echo 'Refusing to overwrite evidence directory' >&2; exit 3; }
qa=$(cd "$(dirname "$0")" && pwd)
src=$(cd "$qa/../Assets" && pwd)
unity=${UNITY_BIN:-/data/apps/Unity/Hub/Editor/6000.6.8f1/Editor/Unity}
[[ -x "$unity" && -f "$src/HPRDefineMatrix/Editor/HprDefineMatrix.cs" ]]
mkdir -p "$out"
chmod 0700 "$out"
export HOME=/home/hans USER=hans LOGNAME=hans DISPLAY=${DISPLAY:-:1} XAUTHORITY=${XAUTHORITY:-/home/hans/.Xauthority}
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000} DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
export LP_NUM_THREADS=2
export HPR_DEFINES_ARCHIVE="$out/HPR_Define_Matrix_PRIVATE.unitypackage" HPR_DEFINES_RECEIPT="$out/real-profile-acceptance.txt"
run(){
  stage=$1; shift; echo "HPR_DEFINES_STAGE $stage"
  timeout 480 "$unity" -batchmode -nographics -quit "$@" -logFile "$out/$stage.unity.log" > "$out/$stage.stdout" 2>&1 || {
    grep -E 'error CS[0-9]|Exception|HPR_DEFINES_' "$out/$stage.unity.log" | tail -30 >&2 || true
    exit 4
  }
}
run author-create -createProject "$out/author"
cp -a "$src/HPRDefineMatrix" "$src/HPRDefineMatrix.meta" "$out/author/Assets/"
mkdir -p "$out/author/Assets/Editor"
cp "$qa/HprDefineMatrixQa.cs" "$out/author/Assets/Editor/"
run author-export -projectPath "$out/author" -executeMethod HprDefineMatrixQa.Export
grep -q HPR_DEFINES_EXPORT_PASS "$out/author-export.unity.log"
python3 "$qa/verify_archive.py" "$HPR_DEFINES_ARCHIVE" "$src" > "$out/archive-identity.json"
run buyer-create -createProject "$out/buyer"
run buyer-import -projectPath "$out/buyer" -importPackage "$HPR_DEFINES_ARCHIVE"
mkdir -p "$out/buyer/Assets/Editor"
cp "$qa/HprDefineMatrixQa.cs" "$out/buyer/Assets/Editor/"
run buyer-native -projectPath "$out/buyer" -executeMethod HprDefineMatrixQa.Run
grep -q HPR_DEFINES_NATIVE_PASS "$HPR_DEFINES_RECEIPT"
cat "$HPR_DEFINES_RECEIPT"
echo HPR_DEFINES_NATIVE_ACCEPTANCE_PASS
