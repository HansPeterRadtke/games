#!/usr/bin/env bash
# Resume only a fresh independent consumer test after a completed export.
# Never replays an uncertain author run or overwrites an existing consumer.
set -euo pipefail
version=${1:?Installed Unity Editor version required}
label=${2:?Private test run label required}
[[ "$version" == 2022.3.22f1 || "$version" == 6000.6.8f1 ]] || exit 2
[[ "$label" =~ ^[a-zA-Z0-9-]+$ ]] || exit 2
root=$(cd "$(dirname "$0")/.." && pwd)
unity=/data/apps/Unity/Hub/Editor/$version/Editor/Unity
base=/data/var/marketplace-account-setup/unity-20261121-evening/native-${version//./-}-$label
archive=$base/hpr-fbx-clip-identity-candidate.unitypackage
fixture=/data/var/marketplace-account-setup/unity-20261121-evening/original-fbx-fixture/OriginalMotion.fbx
buyer=$base/independent-buyer-project
[[ -x "$unity" && -s "$fixture" && -f "$archive" ]] || exit 3
[[ ! -e "$buyer" && ! -e "$base/buyer-create.unity.log" && ! -e "$base/buyer-native-qa" ]] || {
  echo 'Unsafe replay refused: consumer already exists, or result uncertain' >&2; exit 4;
}
python3 "$root/qa/verify_archive.py" --archive "$archive" >"$base/resumed-source-identity-verified.json"
export HOME=/home/hans USER=hans LOGNAME=hans
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
run(){
  local phase=$1; shift
  echo "UNITY_RESUMED_BUYER $version: $phase"
  timeout 480 "$unity" -batchmode -nographics -quit "$@" -logFile "$base/$phase.unity.log" >"$base/$phase.stdout" 2>&1 || {
    echo "FAILED consumer phase $phase" >&2
    grep -E -C 1 'error CS|Exception|HPR_FBX_ID_QA_FAILURE' "$base/$phase.unity.log" | tail -28 >&2 || true
    exit 6
  }
}
run buyer-create -createProject "$buyer"
run buyer-import -projectPath "$buyer" -importPackage "$archive"
mkdir -p "$buyer/Assets/Editor" "$buyer/Assets/HPRFbxIdentityPrivateFixture"
cp -- "$fixture" "$buyer/Assets/HPRFbxIdentityPrivateFixture/OriginalMotion.fbx"
cp -- "$root/qa/HprFbxClipIdentityNativeQa.cs" "$buyer/Assets/Editor/"
export HPR_FBX_ID_QA_OUT="$base/buyer-native-qa"
run buyer-real-model-qa -projectPath "$buyer" -executeMethod HprFbxClipIdentityNativeQa.Run
grep -q 'HPR_FBX_CLIP_IDENTITY_NATIVE_PASS' "$base/buyer-real-model-qa.unity.log"
python3 - "$base" <<'PY'
import json,sys
from pathlib import Path
base=Path(sys.argv[1]);auth=base/'author-native-qa/native-receipt.txt';buyer=base/'buyer-native-qa/native-receipt.txt'
assert auth.is_file() and buyer.is_file()
assert auth.read_bytes()==buyer.read_bytes(), 'Author and genuine buyer checks disagree'
assert all(x.endswith('=PASS') or x.startswith('unity_version=') for x in buyer.read_text().splitlines())
assert json.loads((base/'resumed-source-identity-verified.json').read_text())['result']=='PASS'
print(json.dumps({'result':'PASS','real_native_independent_buyer':True,
    'native_checks':len(buyer.read_text().splitlines())-1,'immutable_archive_source_scope':'PASS'}))
PY
