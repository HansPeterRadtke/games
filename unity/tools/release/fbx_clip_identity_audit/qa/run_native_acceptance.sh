#!/usr/bin/env bash
# Original Blender FBX + native Unity author/export + fresh independent buyer import.
# All working content lives only under the registered private directory.
set -euo pipefail
version=${1:?Unity version, e.g. 2022.3.22f1}
root=$(cd "$(dirname "$0")/.." && pwd)
unity=/data/apps/Unity/Hub/Editor/${version}/Editor/Unity
[[ -x "$unity" ]] || { echo 'Missing installed Unity Editor' >&2; exit 2; }
fixture=/data/var/marketplace-account-setup/unity-20261121-evening/original-fbx-fixture/OriginalMotion.fbx
[[ -s "$fixture" ]] || { echo 'Missing original Blender FBX fixture' >&2; exit 3; }
base=/data/var/marketplace-account-setup/unity-20261121-evening/native-${version//./-}-${HPR_FBX_QA_LABEL:-first}
[[ ! -e "$base" ]] || { echo 'Refusing to overwrite existing native test run' >&2; exit 4; }
mkdir -p "$base"
archive="$base/hpr-fbx-clip-identity-candidate.unitypackage"
author="$base/author-project"
buyer="$base/independent-buyer-project"
export HOME=/home/hans USER=hans LOGNAME=hans
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
run() {
 label=$1; shift
 echo "UNITY_NATIVE ${version}: ${label}"
 timeout 480 "$unity" -batchmode -nographics -quit "$@" -logFile "$base/$label.unity.log" >"$base/$label.stdout" 2>&1 || {
   echo "Native Editor step failed: $label" >&2
   grep -E -C 2 'error CS|Exception|HPR_FBX_ID_QA_FAILURE|executeMethod' "$base/$label.unity.log" 2>/dev/null | tail -34 >&2 || true
   exit 6
 }
}
stage() {
 target=$1
 mkdir -p "$target/Assets/Editor" "$target/Assets/HPRFbxIdentityPrivateFixture"
 cp -- "$fixture" "$target/Assets/HPRFbxIdentityPrivateFixture/OriginalMotion.fbx"
 cp -- "$root/qa/HprFbxClipIdentityNativeQa.cs" "$target/Assets/Editor/"
}
run author-create -createProject "$author"
cp -a "$root/Assets/HPRFbxClipIdentity" "$author/Assets/"
cp -a "$root/Assets/HPRFbxClipIdentity.meta" "$author/Assets/"
stage "$author"
cp -- "$root/qa/HprFbxClipIdentityExporter.cs" "$author/Assets/Editor/"
export HPR_FBX_ID_QA_OUT="$base/author-native-qa"
run author-real-model-qa -projectPath "$author" -executeMethod HprFbxClipIdentityNativeQa.Run
grep -q 'HPR_FBX_CLIP_IDENTITY_NATIVE_PASS' "$base/author-real-model-qa.unity.log"
export HPR_FBX_ID_ARCHIVE_OUT="$archive"
run unity-real-export -projectPath "$author" -executeMethod HprFbxClipIdentityExporter.Run
grep -q 'HPR_FBX_CLIP_IDENTITY_EXPORT_PASS' "$base/unity-real-export.unity.log"
python3 "$root/qa/verify_archive.py" --archive "$archive" > "$base/archive-verified.json"
run buyer-create -createProject "$buyer"
run buyer-import -projectPath "$buyer" -importPackage "$archive"
# Before adding any private test FBX, reproduce the actual one-sample-only
# buyer experience in the fresh imported project. Do not reuse a prior QA run.
mkdir -p "$buyer/Assets/Editor"
cp -- "$root/qa/HprFbxSampleOnlyQa.cs" "$buyer/Assets/Editor/"
export HPR_FBX_SAMPLE_ONLY_QA_OUT="$base/sample-only-native-qa"
run buyer-sample-only-native -projectPath "$buyer" -executeMethod HprFbxSampleOnlyQa.Run
grep -q 'HPR_FBX_SAMPLE_ONLY_QA_PASS' "$base/buyer-sample-only-native.unity.log"
stage "$buyer"
export HPR_FBX_ID_QA_OUT="$base/buyer-native-qa"
run buyer-real-model-qa -projectPath "$buyer" -executeMethod HprFbxClipIdentityNativeQa.Run
grep -q 'HPR_FBX_CLIP_IDENTITY_NATIVE_PASS' "$base/buyer-real-model-qa.unity.log"
python3 - "$base" <<'PY'
from pathlib import Path
import json,sys
p=Path(sys.argv[1])
a=(p/'author-native-qa/native-receipt.txt').read_text()
b=(p/'buyer-native-qa/native-receipt.txt').read_text()
assert a==b,'author and imported buyer results differ'
assert 'real_original_blender_fbx_import=PASS' in a
assert all(line.endswith('=PASS') or line.startswith('unity_version=') for line in a.splitlines())
assert json.loads((p/'archive-verified.json').read_text())['result']=='PASS'
sample_only=(p/'sample-only-native-qa/sample-only-receipt.txt').read_text()
assert 'sample_only_project_scan_reports_no_customer_fbx=PASS' in sample_only
assert all(x.endswith('=PASS') or x.startswith('unity_version=') for x in sample_only.splitlines())
assert a.split('unity_version=')[-1].strip()==sample_only.split('unity_version=')[-1].strip()
print(json.dumps({'status':'PASS','unity_version':a.split('unity_version=')[-1].strip(),
    'real_original_fbx':True,'author_and_buyer':'PASS','fixed_scope_archive':'PASS',
    'native_regressions':len(a.splitlines())-1,'sample_only_buyer_checks':len(sample_only.splitlines())-1,
    'archive_bytes':(p/'hpr-fbx-clip-identity-candidate.unitypackage').stat().st_size}))
PY
