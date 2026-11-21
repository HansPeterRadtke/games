#!/usr/bin/env bash
# Original archive pre-import tool: native author/export/independent buyer.
# Only operates in new, explicitly scoped private disposable Unity projects.
set -euo pipefail
version=${1:?Installed Unity Editor version required}
label=${2:?New unique QA label required}
[[ "$version" = 2022.3.22f1 || "$version" = 6000.6.8f1 ]] || exit 2
[[ "$label" =~ ^[a-zA-Z0-9-]+$ ]] || exit 2
root=$(cd "$(dirname "$0")/.." && pwd)
unity=/data/apps/Unity/Hub/Editor/${version}/Editor/Unity
[[ -x "$unity" ]] || exit 3
base=/data/var/marketplace-account-setup/unity-20261121-wave50/native-${version//./-}-$label
[[ ! -e "$base" ]] || { echo 'Refusing replay of existing native QA project' >&2;exit 4; }
mkdir -p "$base"
archive="$base/hpr-unitypackage-archive-preflight-candidate.unitypackage"
legacy=/data/var/marketplace-account-setup/unity-20261121-afternoon/native-2022-3-22f1-cleanmeta1/hpr-package-boundary-candidate.unitypackage
updated=/data/var/marketplace-account-setup/unity-20261121-afternoon/native-2022-3-22f1-upgrade-final1/hpr-package-boundary-candidate.unitypackage
negative=/data/var/marketplace-account-setup/unity-20261121-wave50/negative-archive-fixtures
[[ -s "$legacy" && -s "$updated" && -s "$negative/guid_changed.unitypackage" ]] || exit 5
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
export HPR_ARCHIVE_PREFLIGHT_OLD="$legacy"
export HPR_ARCHIVE_PREFLIGHT_NEW="$updated"
export HPR_ARCHIVE_PREFLIGHT_BAD_META="$negative/bad_meta.unitypackage"
export HPR_ARCHIVE_PREFLIGHT_CHANGED_GUID="$negative/guid_changed.unitypackage"
export HPR_ARCHIVE_PREFLIGHT_UNSAFE_PATH="$negative/path_traversal.unitypackage"
export HPR_ARCHIVE_PREFLIGHT_TRUNCATED="$negative/truncated.unitypackage"
export HPR_ARCHIVE_PREFLIGHT_SYMLINK="$negative/symlink.unitypackage"
run(){
  phase=$1;shift
  echo "UNITY_ARCHIVE_NATIVE $version $phase"
  timeout 500 "$unity" -batchmode -nographics -quit "$@" -logFile "$base/$phase.unity.log" > "$base/$phase.stdout" 2>&1 || {
    echo "Unity native QA step failed: $phase" >&2
    grep -E -C 1 'error CS|Exception|HPR_ARCHIVE_QA_FAIL|executeMethod' "$base/$phase.unity.log" | tail -55 >&2 || :
    exit 6
  }
}
stage_qa(){
  project=$1
  mkdir -p "$project/Assets/Editor"
  cp -- "$root/qa/HprArchivePreflightNativeQa.cs" "$project/Assets/Editor/"
}
author="$base/author-project"
buyer="$base/fresh-independent-buyer-project"
run author-create -createProject "$author"
cp -a "$root/Assets/HPRArchivePreflight" "$author/Assets/"
cp -a "$root/Assets/HPRArchivePreflight.meta" "$author/Assets/"
stage_qa "$author"
cp -- "$root/qa/HprArchivePreflightExporter.cs" "$author/Assets/Editor/"
export HPR_ARCHIVE_PREFLIGHT_QA_OUT="$base/author-qa-evidence"
run author-native-qa -projectPath "$author" -executeMethod HprArchivePreflightNativeQa.Run
grep -q 'HPR_ARCHIVE_PREFLIGHT_NATIVE_PASS' "$base/author-native-qa.unity.log"
export HPR_ARCHIVE_PREFLIGHT_EXPORT="$archive"
run author-real-export -projectPath "$author" -executeMethod HprArchivePreflightExporter.Run
grep -q 'HPR_ARCHIVE_PREFLIGHT_REAL_EXPORT_PASS' "$base/author-real-export.unity.log"
python3 "$root/qa/verify_archive.py" --archive "$archive" > "$base/verified-buyer-archive.json"
run buyer-create -createProject "$buyer"
run buyer-real-import -projectPath "$buyer" -importPackage "$archive"
stage_qa "$buyer"
export HPR_ARCHIVE_PREFLIGHT_QA_OUT="$base/buyer-qa-evidence"
run buyer-native-qa -projectPath "$buyer" -executeMethod HprArchivePreflightNativeQa.Run
grep -q 'HPR_ARCHIVE_PREFLIGHT_NATIVE_PASS' "$base/buyer-native-qa.unity.log"
python3 - "$base" <<'PY'
from pathlib import Path
import json,sys
p=Path(sys.argv[1]);author=(p/'author-qa-evidence/native-receipt.txt').read_text()
buyer=(p/'buyer-qa-evidence/native-receipt.txt').read_text()
assert author==buyer and all(x.endswith('=PASS') or x.startswith('unity_version=') for x in author.splitlines())
assert json.loads((p/'verified-buyer-archive.json').read_text())['result']=='PASS'
print(json.dumps({'result':'PASS','unity_version':author.split('unity_version=')[-1].strip(),
    'first_party_archive_install':'PASS','strict_comparison_and_negative_cases':'PASS',
    'native_checks':len(author.splitlines())-1,
    'buyer_archive_bytes':(p/'hpr-unitypackage-archive-preflight-candidate.unitypackage').stat().st_size}))
PY
