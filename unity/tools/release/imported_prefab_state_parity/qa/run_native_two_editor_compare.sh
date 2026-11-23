#!/usr/bin/env bash
set -euo pipefail
label=${1:?existing original genuine two-Unity-editor native test label}
[[ "$label" =~ ^[a-z0-9_-]{4,30}$ ]]||exit 2
base=/data/var/marketplace-account-setup/unity-prefab-dependency-20261123-wave61
A="$base/2022-3-22f1-$label/real-imported-prefab-states.json"
B="$base/6000-6-8f1-$label/real-imported-prefab-states.json"
project="$base/6000-6-8f1-$label/independent-buyer-project"
output="$base/6000-6-8f1-$label/real-native-two-editor-prefab-comparison.json"
log="$base/6000-6-8f1-$label/real-native-two-editor-prefab-comparison.unity.log"
qa=$(cd "$(dirname "$0")" && pwd)/HprPrefabParityTwoEditorQa.cs
target="$project/Assets/Editor/HprPrefabParityTwoEditorQa.cs"
unity=/data/apps/Unity/Hub/Editor/6000.6.8f1/Editor/Unity
[[ -x "$unity" && -s "$A" && -s "$B" && -d "$project/Assets/HPRImportedPrefabParity" &&
   -s "$qa" && ! -e "$target" && ! -e "$output" && ! -e "$log" ]] || { echo 'Missing genuine original scan evidence or attempted repeated effect' >&2; exit 3; }
python3 - "$base/2022-3-22f1-$label/exact-original-vendor-archive.json" \
          "$base/6000-6-8f1-$label/exact-original-vendor-archive.json" <<'PYVERIFY'
import json,sys
A=json.load(open(sys.argv[1]));B=json.load(open(sys.argv[2]))
assert A['status']==B['status']=='PASS'
assert A['source_sha256']==B['source_sha256'], 'Scanner source revisions differ: no Unity inference allowed'
assert A['original_first_party_asset_paths']==B['original_first_party_asset_paths']
print('IDENTICAL_ORIGINAL_SCANNER_SOURCE_BEFORE_REAL_EDITOR_COMPARISON',A['source_sha256'][:18])
PYVERIFY
cp "$qa" "$target"
export HPR_PREFAB_FIRST_RECEIPT="$A"
export HPR_PREFAB_SECOND_RECEIPT="$B"
export HPR_PREFAB_TWO_EDITOR_OUT="$output"
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
timeout 300 "$unity" -batchmode -nographics -quit -projectPath "$project" \
 -executeMethod HprPrefabParityTwoEditorQa.Run -logFile "$log" \
 > "$base/6000-6-8f1-$label/real-native-two-editor-prefab-comparison.stdout" 2>&1 || {
 grep -E 'HPR_PREFAB_TWO_EDITOR_QA_FAILURE|error CS|Exception' "$log"|tail -25 >&2 || true;exit 5;
}
[[ -s "$output" ]] || exit 6
grep -q HPR_PREFAB_PARITY_TWO_REAL_EDITOR_PASS "$log"
python3 - "$output" <<'PY'
import json,sys
r=json.load(open(sys.argv[1]));assert r['status'] in ('REVIEW_IMPORTED_PREFAB_VALUE_DIFFERENCES','MATCHED_COVERED_IMPORTED_PREFAB_VALUES')
assert r['sourceDifferences']==[]
print('REAL_TWO_EDITOR_IMPORTED_PREFAB_STATE_COMPARISON',r['status'], 'changed',len(r['changedValueKeys']), 'added',len(r['addedValueKeys']),'removed',len(r['removedValueKeys']),'unsupported_components',r['unsupportedComponents'])
PY
