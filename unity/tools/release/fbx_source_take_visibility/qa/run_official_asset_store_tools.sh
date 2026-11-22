#!/usr/bin/env bash
# Isolated OFFLINE official Unity Asset Store Tools validator for the exact
# first-party Unity package. No portal login, terms acceptance or submission.
set -euo pipefail
archive=${1:?Fresh native owner package archive path}
label=${2:?Fresh unique validation label}
[[ "$label" =~ ^[a-zA-Z0-9_-]{1,35}$ ]] || exit 2
base=/data/var/marketplace-account-setup/unity-20261122-wave55
out="$base/official-ast-2022-$label"
[[ ! -e "$out" && -s "$archive" ]] || { echo 'Refusing duplicate or missing package' >&2;exit 3; }
case "$archive" in
 "$base"/native-2022-3-22f1-*/hpr-original-fbx-source-take-candidate.unitypackage) ;;
 *) echo 'Archive must be original Unity2022 source take candidate' >&2;exit 3;;
esac
unity=/data/apps/Unity/Hub/Editor/2022.3.22f1/Editor/Unity
ast=/data/src/external/com.unity.asset-store-tools/com.unity.asset-store-tools
runner=/data/src/worktrees/unity-package-boundary-audit-20261121/unity/tools/release/HprAssetStoreToolsValidatorRunner.cs
[[ -x "$unity" && -d "$ast" && -f "$runner" ]] || exit 4
mkdir -p "$out"
project="$out/disposable-validation-project"
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
run(){
 stage=$1;shift
 echo "OFFICIAL_AST_FBX_TAKES $stage"
 timeout 500 "$unity" -batchmode -nographics -quit "$@" -logFile "$out/$stage.unity.log" > "$out/$stage.stdout" 2>&1 || {
  grep -E -C2 'error CS|Exception|Validation|executeMethod' "$out/$stage.unity.log" | tail -34 >&2 || :
  exit 5
 }
}
run create -createProject "$project"
python3 - "$project/Packages/manifest.json" "$ast" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);data=json.loads(p.read_text())
data.setdefault('dependencies',{})['com.unity.asset-store-tools']='file:'+sys.argv[2]
p.write_text(json.dumps(data,indent=2)+'\n')
PY
run import-exact-original-package -projectPath "$project" -importPackage "$archive"
mkdir -p "$project/Assets/Editor"
cp -- "$runner" "$project/Assets/Editor/HprAssetStoreToolsValidatorRunner.cs"
export HPR_AST_RESULTS="$out/asset-store-tools-counted-results.txt"
export HPR_AST_PATHS=Assets/HPRFbxSourceTakes
[[ ! -e "$HPR_AST_RESULTS" ]] || exit 6
run offline-official-check -projectPath "$project" -executeMethod HprAssetStoreToolsValidatorRunner.ValidateFromEnvironment
[[ -s "$HPR_AST_RESULTS" ]] || exit 7
cat "$HPR_AST_RESULTS"
