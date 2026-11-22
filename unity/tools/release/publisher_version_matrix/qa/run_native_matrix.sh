#!/usr/bin/env bash
set -euo pipefail
version=${1:?installed Unity version}
[[ "$version" = '2022.3.22f1' || "$version" = '6000.6.8f1' ]] || exit 2
label=${2:?fresh label}
[[ "$label" =~ ^[a-z0-9_-]{3,24}$ ]] || exit 2
unity=/data/apps/Unity/Hub/Editor/$version/Editor/Unity
product=$(cd "$(dirname "$0")/.." && pwd)
repo=$(cd "$product/.." && pwd)
root=/data/var/marketplace-account-setup/unity-publisher-matrix-20261122-v1
case_id=${version//./-}-$label
work="$root/$case_id"
package="$work/HPR_Publisher_Version_Matrix_original.unitypackage"
resume=${3:-fresh}
[[ -x "$unity" && -d "$product/Assets/HPRPublisherVersionMatrix" ]] || exit 3
if [[ "$resume" == fresh ]]; then
 [[ ! -e "$work" ]] || { echo 'Refusing any repeated author/export state' >&2;exit 3; }
 mkdir -p "$work"
elif [[ "$resume" == verified_author ]]; then
 [[ -d "$work" && -s "$work/author-export.unity.log" && -s "$package" && ! -e "$work/independent-buyer-project" ]] || exit 3
 grep -q HPR_PUBLISHER_VERSION_MATRIX_PACKAGE_EXPORT_PASS "$work/author-export.unity.log" || exit 3
else exit 2;fi
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
run(){ local name=$1;shift;echo "HPR_PUBLISHER_MATRIX_REAL_UNITY $version $name";
 timeout 490 "$unity" -batchmode -nographics -quit "$@" -logFile "$work/$name.unity.log" > "$work/$name.stdout" 2>&1 || {
  grep -E 'error CS|Exception|HPR_MATRIX' "$work/$name.unity.log" | tail -26 >&2 || true;exit 5;
 }
}
source_root="$product/Assets/HPRPublisherVersionMatrix"
qa="$product/qa"
author="$work/author-project"
buyer="$work/independent-buyer-project"
if [[ "$resume" == fresh ]]; then
 run create-author -createProject "$author"
 cp -a "$source_root" "$source_root.meta" "$author/Assets/"
 mkdir -p "$author/Assets/Editor"
 cp "$qa/HprPublisherVersionMatrixExporter.cs" "$author/Assets/Editor/"
 export HPR_MATRIX_PACKAGE_OUT="$package"
 run author-export -projectPath "$author" -executeMethod HprPublisherVersionMatrixExporter.Run
 grep -q HPR_PUBLISHER_VERSION_MATRIX_PACKAGE_EXPORT_PASS "$work/author-export.unity.log"
fi
python3 "$qa/verify_original_archive.py" "$package" > "$work/original-vendor-scope.json"
run create-buyer -createProject "$buyer"
run buyer-import-original -projectPath "$buyer" -importPackage "$package"
# Install separately validated original FBX importer product to provide REAL model dependencies.
original=/data/var/marketplace-account-setup/unity-20261122-wave55/combined-animation-native-2022-3-22f1-browse-20261122-v1/HPR_Combined_Animation_Import_Preflight_Candidate.unitypackage
[[ -s "$original" ]] || exit 4
run buyer-import-real-first-party -projectPath "$buyer" -importPackage "$original"
mkdir -p "$buyer/Assets/Editor"
cp "$qa/HprPublisherVersionMatrixQa.cs" "$buyer/Assets/Editor/"
export HPR_MATRIX_QA_ROOTS='Assets/HPRAnimationImportPreflight;Assets/HPRFbxClipIdentity;Assets/HPRFbxSourceTakes'
export HPR_MATRIX_QA_OUT="$work/independent-buyer-import-snapshot.json"
run buyer-native-snapshot -projectPath "$buyer" -executeMethod HprPublisherVersionMatrixQa.Run
grep -q HPR_PUBLISHER_VERSION_MATRIX_NATIVE_PASS "$work/buyer-native-snapshot.unity.log"
cp "$qa/HprPublisherVersionCompareNativeQa.cs" "$buyer/Assets/Editor/"
export HPR_PUBLISHER_DIFF_QA_OUT="$work/independent-buyer-synthetic-negative-diff.json"
run buyer-native-diff -projectPath "$buyer" -executeMethod HprPublisherVersionCompareNativeQa.Run
grep -q HPR_PUBLISHER_VERSION_COMPARE_NATIVE_PASS "$work/buyer-native-diff.unity.log"
python3 - "$work" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]); report=json.loads((p/'independent-buyer-import-snapshot.json').read_text())
assert report['schema']==2 and report['status']=='SNAPSHOT_COMPLETE' and not report['incomplete'] and report['assetCount']>=15
assert json.loads((p/'original-vendor-scope.json').read_text())['status']=='PASS'
diff=json.loads((p/'independent-buyer-synthetic-negative-diff.json').read_text())
assert diff['status']=='REVIEW_IMPORT_DIFFERENCES' and len(diff['guidChanges'])==1
print('HPR_MATRIX_ORIGINAL_PACKAGE_NATIVE_AUTHOR_INDEPENDENT_BUYER_PASS',p.name,'tested_assets',report['assetCount'])
PY
