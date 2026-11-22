#!/usr/bin/env bash
# Test one exact first-party candidate with a genuine 2-take Blender source,
# native Unity author/export, independent buyer import and real customized
# importer omission detection. Never runs an actual customer or live project.
set -euo pipefail
version=${1:?Installed Unity version}
label=${2:?Fresh unique label}
[[ "$version" = 2022.3.22f1 || "$version" = 6000.6.8f1 ]] || exit 2
[[ "$label" =~ ^[a-zA-Z0-9_-]{1,35}$ ]] || exit 2
root=$(cd "$(dirname "$0")/.." && pwd)
base=/data/var/marketplace-account-setup/unity-20261122-wave55/native-${version//./-}-$label
unity=/data/apps/Unity/Hub/Editor/$version/Editor/Unity
original="$root/Assets/HPRFbxSourceTakes/Samples/HPRTwoTakeCube.fbx"
[[ ! -e "$base" && -x "$unity" && -s "$original" ]] || {
 echo 'Duplicate native run or missing installed Unity original FBX' >&2; exit 3; }
mkdir -p "$base"
author="$base/author-project"
buyer="$base/independent-buyer-project"
archive="$base/hpr-original-fbx-source-take-candidate.unitypackage"
sha256sum "$original" > "$base/original-blender-source-before.sha256"
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
run(){
 name=$1; shift
 echo "ORIGINAL_FBXTakes_NATIVE $version $name"
 timeout 480 "$unity" -batchmode -nographics -quit "$@" -logFile "$base/$name.unity.log" > "$base/$name.stdout" 2>&1 || {
  echo "Unity source take check stopped at $name" >&2
  grep -E -C2 'error CS|Exception|HPR_SOURCE_TAKE|executeMethod' "$base/$name.unity.log" | tail -36 >&2 || :
  exit 5
 }
}
stage_qa(){
 target=$1
 mkdir -p "$target/Assets/Editor"
 cp -- "$root/qa/HprFbxSourceTakeNativeQa.cs" "$target/Assets/Editor/"
}
stage_private(){
 target=$1
 mkdir -p "$target/Assets/HPRPrivateSourceTakes"
 test ! -e "$target/Assets/HPRPrivateSourceTakes/OriginalTwoTake.fbx"
 cp -- "$original" "$target/Assets/HPRPrivateSourceTakes/OriginalTwoTake.fbx"
}
run create-author -createProject "$author"
cp -a "$root/Assets/HPRFbxSourceTakes" "$author/Assets/"
cp -a "$root/Assets/HPRFbxSourceTakes.meta" "$author/Assets/"
stage_qa "$author"
cp -- "$root/qa/HprFbxSourceTakeExporter.cs" "$author/Assets/Editor/"
export HPR_SOURCE_TAKE_QA_OUT="$base/author-original-probe.txt"
run native-original-author-probe -projectPath "$author" -executeMethod HprFbxSourceTakeNativeQa.Probe
grep -q HPR_SOURCE_TAKE_PROBE_SUCCESS "$base/native-original-author-probe.unity.log"
export HPR_SOURCE_TAKE_PACKAGE_OUT="$archive"
run author-original-export -projectPath "$author" -executeMethod HprFbxSourceTakeExporter.Run
grep -q HPR_SOURCE_TAKE_EXPORT_PASS "$base/author-original-export.unity.log"
python3 "$root/qa/verify_archive.py" --archive "$archive" > "$base/original-export-verified.json"
stage_private "$author"
export HPR_SOURCE_TAKE_CUSTOM_QA_DIR="$base/author-custom-fixture-qa"
mkdir -p "$HPR_SOURCE_TAKE_CUSTOM_QA_DIR"
run author-private-customize -projectPath "$author" -executeMethod HprFbxSourceTakeNativeQa.CustomizePrivate
grep -q HPR_SOURCE_TAKE_PRIVATE_CUSTOMIZATION_PASS "$base/author-private-customize.unity.log"
run author-private-audit -projectPath "$author" -executeMethod HprFbxSourceTakeNativeQa.AuditCustomized
grep -q HPR_SOURCE_TAKE_REAL_CUSTOMIZED_AUDIT_PASS "$base/author-private-audit.unity.log"
run create-buyer -createProject "$buyer"
run import-original-package -projectPath "$buyer" -importPackage "$archive"
stage_qa "$buyer"
export HPR_SOURCE_TAKE_QA_OUT="$base/buyer-original-probe.txt"
run buyer-original-probe -projectPath "$buyer" -executeMethod HprFbxSourceTakeNativeQa.Probe
grep -q HPR_SOURCE_TAKE_PROBE_SUCCESS "$base/buyer-original-probe.unity.log"
stage_private "$buyer"
export HPR_SOURCE_TAKE_CUSTOM_QA_DIR="$base/buyer-custom-fixture-qa"
mkdir -p "$HPR_SOURCE_TAKE_CUSTOM_QA_DIR"
run buyer-private-customize -projectPath "$buyer" -executeMethod HprFbxSourceTakeNativeQa.CustomizePrivate
grep -q HPR_SOURCE_TAKE_PRIVATE_CUSTOMIZATION_PASS "$base/buyer-private-customize.unity.log"
run buyer-private-audit -projectPath "$buyer" -executeMethod HprFbxSourceTakeNativeQa.AuditCustomized
grep -q HPR_SOURCE_TAKE_REAL_CUSTOMIZED_AUDIT_PASS "$base/buyer-private-audit.unity.log"
python3 - "$base" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);src=p/'original-blender-source-before.sha256';a=p/'author-original-probe.txt';b=p/'buyer-original-probe.txt'
assert a.read_text()==b.read_text()
assert 'original_source_take_count=2' in a.read_text()
assert 'real_importer_report_status=NO_CUSTOMER_FBX_MODELS_SCANNED' in a.read_text()
for fn in ['private-customization-receipt.txt','private-source-take-audit.txt','original-source-take-review.json']:
 assert (p/'author-custom-fixture-qa'/fn).read_bytes()==(p/'buyer-custom-fixture-qa'/fn).read_bytes(),fn
assert 'private_custom_omission_flagged=PASS' in (p/'buyer-custom-fixture-qa/private-source-take-audit.txt').read_text()
assert json.loads((p/'original-export-verified.json').read_text())['result']=='PASS'
print('REAL_FBXTakes_TWO_UNITY_PROJECTS_AUTHOR_BUYER=PASS')
PY
sha256sum "$original" > "$base/original-blender-source-after.sha256"
diff "$base/original-blender-source-before.sha256" "$base/original-blender-source-after.sha256"
echo ORIGINAL_BUYER_SOURCE_TAKE_ACCEPTANCE_PASS
