#!/usr/bin/env bash
set -euo pipefail
version=${1:?installed version}
label=${2:?new immutable native label}
[[ "$version" = '2022.3.22f1' || "$version" = '6000.6.8f1' ]] || exit 2
[[ "$label" =~ ^[a-z0-9_-]{4,30}$ ]] || exit 2
root=/data/var/marketplace-account-setup/unity-prefab-dependency-20261123-wave61
work="$root/${version//./-}-$label"
product=$(cd "$(dirname "$0")/.." && pwd)
qa="$product/qa"
source="$product/Assets/HPRImportedPrefabParity"
unity=/data/apps/Unity/Hub/Editor/$version/Editor/Unity
vendor=/data/var/marketplace-account-setup/unity-publisher-matrix-20261122-v1/2022-3-22f1-hashwave58a/HPR_Publisher_Version_Matrix_original.unitypackage
original=/data/var/marketplace-account-setup/unity-20261122-wave55/combined-animation-native-2022-3-22f1-browse-20261122-v1/HPR_Combined_Animation_Import_Preflight_Candidate.unitypackage
[[ -x "$unity" && -d "$source" && -s "$original" && ! -e "$work" ]] || { echo 'Refusing repeated effects or missing product inputs' >&2; exit 3; }
mkdir -p "$work"
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
run() { name=$1; shift; echo "HPR_PREFAB_NATIVE_PHASE $version $name";
 timeout 490 "$unity" -batchmode -nographics -quit "$@" -logFile "$work/$name.unity.log" >"$work/$name.stdout" 2>&1 || {
  grep -E 'HPR_PREFAB|error CS[0-9]|Exception' "$work/$name.unity.log" | tail -26 >&2 || true;exit 5;
 }
}
author="$work/author-project"
buyer="$work/independent-buyer-project"
run create-author -createProject "$author"
cp -a "$source" "$source.meta" "$author/Assets/"
mkdir -p "$author/Assets/Editor"
cp "$qa/HprPrefabParityExporter.cs" "$author/Assets/Editor/"
export HPR_PREFAB_PACKAGE_OUT="$work/HPR_Imported_Prefab_State_Parity_original.unitypackage"
run author-export -projectPath "$author" -executeMethod HprPrefabParityExporter.Run
grep -q HPR_PREFAB_PARITY_ORIGINAL_PACKAGE_EXPORT_PASS "$work/author-export.unity.log"
python3 "$qa/verify_original_archive.py" "$HPR_PREFAB_PACKAGE_OUT" >"$work/exact-original-vendor-archive.json"
run create-buyer -createProject "$buyer"
run buyer-import-original -projectPath "$buyer" -importPackage "$HPR_PREFAB_PACKAGE_OUT"
run buyer-import-genuine-supplier -projectPath "$buyer" -importPackage "$original"
mkdir -p "$buyer/Assets/Editor"
cp "$qa/HprPrefabParityNativeQa.cs" "$buyer/Assets/Editor/"
export HPR_PREFAB_NATIVE_RECEIPT="$work/real-imported-prefab-states.json"
run buyer-native-scan -projectPath "$buyer" -executeMethod HprPrefabParityNativeQa.Run
grep -q HPR_PREFAB_STATE_PARITY_NATIVE_PASS "$work/buyer-native-scan.unity.log"
python3 - "$work" <<'PY'
import json,sys
from pathlib import Path
r=Path(sys.argv[1]);data=json.loads((r/'real-imported-prefab-states.json').read_text())
assert data['schema']==2 and data['status']=='CAPTURED_COVERED_PREFAB_VALUES' and data['incomplete'] is False
assert len(data['inputs'])==3 and data['valuesCaptured']>=30 and len(data['dependencies'])>=1
assert json.loads((r/'exact-original-vendor-archive.json').read_text())['status']=='PASS'
print('HPR_PREFAB_NATIVE_REAL_BUYER_PASS',r.name,'original_prefabs',len(data['inputs']),'covered_values',data['valuesCaptured'],'uncovered_components',data['unsupportedComponents'],'verified_dependencies',len(data['dependencies']),'unverified',len(data['unverifiedDependencyPaths']))
PY
