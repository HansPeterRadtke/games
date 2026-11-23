#!/usr/bin/env bash
set -euo pipefail
label=${1:?existing exact nested original buyer test label}
[[ "$label" =~ ^[a-z0-9_-]{4,30}$ ]]||exit 2
root=/data/var/marketplace-account-setup/unity-nested-custom-20261123-wave62
work="$root/$label"
a="$work/2022-3-22f1-nested-custom-native-receipt.json"
b="$work/6000-6-8f1-nested-custom-native-receipt.json"
project="$work/6000-6-8f1-independent-buyer"
output="$work/real-native-two-editor-nested-custom-comparison.json"
log="$work/real-native-two-editor-nested-custom-comparison.unity.log"
qa=$(cd "$(dirname "$0")" && pwd)/HprNestedCustomTwoEditorQa.cs
target="$project/Assets/Editor/HprNestedCustomTwoEditorQa.cs"
unity=/data/apps/Unity/Hub/Editor/6000.6.8f1/Editor/Unity
[[ -x "$unity" && -s "$a" && -s "$b" && -d "$project/Assets/HPRImportedPrefabParity" &&
  -s "$qa" && ! -e "$target" && ! -e "$output" && ! -e "$log" ]] || {
  echo 'Refusing repeat comparison or missing authentic original private buyer artifacts' >&2;exit 3;
}
python3 - "$work/product-original-exact-archive-proof.json" "$a" "$b" <<'PYVERIFY'
import json,sys
origin=json.load(open(sys.argv[1]))
a=json.load(open(sys.argv[2]));b=json.load(open(sys.argv[3]))
assert origin['status']=='PASS' and origin['original_first_party_asset_paths']==5
assert a['schema']==b['schema']==2 and len(a['inputs'])==len(b['inputs'])==3
assert a['unityVersion']=='2022.3.22f1' and b['unityVersion']=='6000.6.8f1'
print('GENUINE_ORIGINAL_UNITY_BUYER_RECEIPTS_AND_PACKAGE_PRECHECK_PASS')
PYVERIFY
cp "$qa" "$target"
export HPR_NESTED_FIRST_RECEIPT="$a"
export HPR_NESTED_SECOND_RECEIPT="$b"
export HPR_NESTED_TWO_EDITOR_OUT="$output"
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
timeout 300 "$unity" -batchmode -nographics -quit -projectPath "$project" \
 -executeMethod HprNestedCustomTwoEditorQa.Run -logFile "$log" \
 >"$work/real-native-two-editor-nested-custom-comparison.stdout" 2>&1 || {
 grep -E 'HPR_NESTED_CUSTOM_TWO_EDITOR_QA_FAILURE|error CS|Exception' "$log"|tail -25 >&2 || true;exit 5;
}
[[ -s "$output" ]] || exit 6
grep -q HPR_NESTED_CUSTOM_TWO_REAL_EDITOR_PASS "$log"
python3 - "$output" <<'PYCHECK'
import json,sys
r=json.load(open(sys.argv[1]))
assert r['schema']==2 and r['status']=='COVERED_VALUES_MATCH_UNINSPECTED_COMPONENTS'
assert r['unsupportedComponents']==6
assert not any(r[k] for k in ('sourceDifferences','dependencyDifferences','unverifiedDependencyPaths','changedValueKeys','removedValueKeys','addedValueKeys'))
print('REAL_UNITY6_IN_EDITOR_CSHARP_NESTED_UNINSPECTED_VERDICT_PASS',r['status'],'six occurrences')
PYCHECK
