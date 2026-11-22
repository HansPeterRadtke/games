#!/usr/bin/env bash
# Offline official installed Unity Asset Store Tools 12 compatibility check
# for exact combined Editor vendor roots in fresh independent Unity 2022 project.
# No Marketplace account, Terms acceptance, review or publication effects.
set -euo pipefail
archive=${1:?actual exact original Unity package archive}
label=${2:?new unique label}
[[ "$label" =~ ^[a-z0-9_-]{2,35}$ ]] || exit 2
base=/data/var/marketplace-account-setup/unity-20261122-wave55
case "$archive" in
 "$base"/combined-animation-native-2022-3-22f1-*/HPR_Combined_Animation_Import_Preflight_Candidate.unitypackage) ;;
 *) echo 'Only genuine original combined Unity2022 package exports may be validated' >&2;exit 3;;
esac
[[ -s "$archive" ]] || exit 3
out=$base/combined-ast-2022-$label
[[ ! -e "$out" ]] || { echo 'Refusing repeated official validation destination' >&2;exit 4; }
mkdir -p "$out"
project=$out/new-offline-validation-project
unity=/data/apps/Unity/Hub/Editor/2022.3.22f1/Editor/Unity
ast=/data/src/external/com.unity.asset-store-tools/com.unity.asset-store-tools
runner=$(cd "$(dirname "$0")/../.." && pwd)/HprAssetStoreToolsValidatorRunner.cs
[[ -x "$unity" && -d "$ast" && -s "$runner" ]] || exit 5
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
run(){ step=$1;shift;echo "OFFICIAL_COMBINED_ANIMATION $step";
 timeout 500 "$unity" -batchmode -nographics -quit "$@" -logFile "$out/$step.unity.log" > "$out/$step.stdout" 2>&1 || {
  echo "Official validation process exited nonzero at $step" >&2;
  grep -E -C2 'error CS|Exception|Asset Store Tools validation' "$out/$step.unity.log" | tail -32 >&2 || :
  exit 6;
 }
}
run create -createProject "$project"
python3 - "$project/Packages/manifest.json" "$ast" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);d=json.loads(p.read_text())
d.setdefault('dependencies',{})['com.unity.asset-store-tools']='file:'+sys.argv[2]
p.write_text(json.dumps(d,indent=2)+'\n')
PY
run install-original-three-vendor-roots -projectPath "$project" -importPackage "$archive"
mkdir -p "$project/Assets/Editor"
cp -- "$runner" "$project/Assets/Editor/HprAssetStoreToolsValidatorRunner.cs"
export HPR_AST_RESULTS="$out/official-validation-counted-results.txt"
export HPR_AST_PATHS='Assets/HPRAnimationImportPreflight;Assets/HPRFbxClipIdentity;Assets/HPRFbxSourceTakes'
run official-validation -projectPath "$project" -executeMethod HprAssetStoreToolsValidatorRunner.ValidateFromEnvironment
[[ -s "$HPR_AST_RESULTS" ]] || exit 7
cat "$HPR_AST_RESULTS"
