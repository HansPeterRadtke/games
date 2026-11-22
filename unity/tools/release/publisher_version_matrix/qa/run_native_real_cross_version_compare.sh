#!/usr/bin/env bash
# Genuine original native Unity 2022 and Unity 6 imported receipts;
# run both inputs through the newly authored C# Editor comparison, not Python.
set -euo pipefail
label=${1:?existing fully tested Unity6 buyer label}
[[ "$label" =~ ^[a-z0-9_-]{3,24}$ ]] || exit 2
root=/data/var/marketplace-account-setup/unity-publisher-matrix-20261122-v1
base="$root/6000-6-8f1-$label"
project="$base/independent-buyer-project"
first="$root/2022-3-22f1-$label/independent-buyer-import-snapshot.json"
second="$base/independent-buyer-import-snapshot.json"
qa=$(cd "$(dirname "$0")" && pwd)/HprPublisherVersionRealReceiptsQa.cs
editor=/data/apps/Unity/Hub/Editor/6000.6.8f1/Editor/Unity
output="$base/real-cross-editor-Csharp-compare.json"
log="$base/real-cross-editor-Csharp-compare.unity.log"
private="$project/Assets/Editor/HprPublisherVersionRealReceiptsQa.cs"
[[ -x "$editor" && -s "$first" && -s "$second" && -s "$qa" &&
   -d "$project/Assets/HPRPublisherVersionMatrix" && ! -e "$output" &&
   ! -e "$log" && ! -e "$private" ]] || exit 3
cp -- "$qa" "$private"
export HPR_MATRIX_REAL_FIRST="$first"
export HPR_MATRIX_REAL_SECOND="$second"
export HPR_MATRIX_REAL_COMPARISON_OUT="$output"
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
timeout 300 "$editor" -batchmode -nographics -quit -projectPath "$project" \
 -executeMethod HprPublisherVersionRealReceiptsQa.Run -logFile "$log" \
 > "$base/real-cross-editor-Csharp-compare.stdout" 2>&1 || {
 grep -E 'error CS|HPR_MATRIX_REAL_VERSION_COMPARE|Exception' "$log" | tail -22 >&2 || true;exit 4;
}
[[ -s "$output" ]] || exit 5
grep -q 'HPR_MATRIX_REAL_TWO_EDITOR_COMPARE_PASS' "$log"
python3 - "$output" <<'PY'
import json,sys
r=json.load(open(sys.argv[1])); assert r['status']=='MATCHED_IMPORT_INPUT_BYTES_AND_METADATA'
for k in ['missingFromSecond','newInSecond','guidChanges','dependencyChanges']:
 assert r[k]==[],(k,r[k])
print('REAL_NATIVE_TWO_VERSION_IN_EDITOR_COMPARISON_PASS')
PY
