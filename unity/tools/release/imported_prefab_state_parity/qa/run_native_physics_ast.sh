#!/usr/bin/env bash
# Installed official Asset Store Tools v12, offline, disposable original package validation.
set -euo pipefail
caseid=${1:?existing immutable author label}
label=${2:?new unique validator label}
[[ "$caseid" =~ ^[a-z0-9_-]{4,30}$ && "$label" =~ ^[a-z0-9_-]{3,24}$ ]] || exit 2
root=/data/var/marketplace-account-setup/unity-player-reference-probe-20261123-wave63
original="$root/$caseid/HPR_ImportedPrefabParity_PhysicsOriginal.unitypackage"
out="$root/official-ast-$label"
[[ -s "$original" && ! -e "$out" ]] || { echo 'Source missing or repeated exact validation effect' >&2;exit 3; }
mkdir -p "$out"
project="$out/independent-ast-validation-project"
unity=/data/apps/Unity/Hub/Editor/2022.3.22f1/Editor/Unity
ast=/data/src/external/com.unity.asset-store-tools/com.unity.asset-store-tools
runner=$(cd "$(dirname "$0")/../.." && pwd)/HprAssetStoreToolsValidatorRunner.cs
[[ -x "$unity" && -d "$ast" && -s "$runner" ]] || exit 4
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
run(){ name=$1;shift;echo "HPR_COLLIDER_PHYSICS_OFFICIAL_AST $name";
 timeout 490 "$unity" -batchmode -nographics -quit "$@" -logFile "$out/$name.unity.log" > "$out/$name.stdout" 2>&1 || {
  grep -E 'error CS|Exception|Asset Store Tools' "$out/$name.unity.log" | tail -25 >&2 || true;exit 5;
 }
}
run create -createProject "$project"
python3 - "$project/Packages/manifest.json" "$ast" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);d=json.loads(p.read_text());d.setdefault('dependencies',{})['com.unity.asset-store-tools']='file:'+sys.argv[2];p.write_text(json.dumps(d,indent=2)+'\n')
PY
run buyer-import-original -projectPath "$project" -importPackage "$original"
mkdir -p "$project/Assets/Editor"
cp -- "$runner" "$project/Assets/Editor/HprAssetStoreToolsValidatorRunner.cs"
export HPR_AST_RESULTS="$out/official-results.txt"
export HPR_AST_PATHS='Assets/HPRImportedPrefabParity'
run official-validation -projectPath "$project" -executeMethod HprAssetStoreToolsValidatorRunner.ValidateFromEnvironment
[[ -s "$HPR_AST_RESULTS" ]] || exit 6
cat "$HPR_AST_RESULTS"
