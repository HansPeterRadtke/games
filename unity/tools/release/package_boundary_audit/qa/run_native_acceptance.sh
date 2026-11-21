#!/usr/bin/env bash
# Native author/export/independent buyer-import acceptance on disposable projects.
# Never touches an existing project, buyer source, Unity account, or storefront.
set -euo pipefail
version=${1:?Pass installed Unity version path segment}
base=/data/var/marketplace-account-setup/unity-20261121-afternoon
src=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
unity=/data/apps/Unity/Hub/Editor/$version/Editor/Unity
[[ -x "$unity" ]] || { echo "Unity Editor version unavailable: $version" >&2; exit 2; }
key=${version//./-}-${HPR_BOUNDARY_RUN_SUFFIX:-first}
out="$base/native-$key"
[[ ! -e "$out" ]] || { echo "Refusing to overwrite an existing native QA workspace $out" >&2; exit 3; }
mkdir -p "$out"
author="$out/author-project"
buyer="$out/independent-buyer-project"
archive="$out/hpr-package-boundary-candidate.unitypackage"
export HOME=/home/hans USER=hans LOGNAME=hans
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
run_unity() {
  local label=$1; shift
  echo "Unity $version: $label"
  timeout 510 "$unity" -batchmode -nographics -quit "$@" -logFile "$out/$label.unity.log" >"$out/$label.stdout" 2>&1 || {
    echo "Unity native $label failed. Tail of logfile:" >&2
    tail -65 "$out/$label.unity.log" >&2 || true
    exit 5
  }
}
run_unity author-create -createProject "$author"
mkdir -p "$author/Assets/Editor"
cp -a "$src/Assets/HPRPackageBoundary" "$author/Assets/"
cp -a "$src/Assets/HPRPackageBoundary.meta" "$author/Assets/"
cp "$src/qa/HprPackageBoundaryNativeQa.cs" "$author/Assets/Editor/"
cp "$src/qa/HprPackageBoundaryExporter.cs" "$author/Assets/Editor/"
export HPR_BOUNDARY_QA_OUT="$out/author-qa-evidence"
run_unity author-native-qa -projectPath "$author" -executeMethod HprPackageBoundaryNativeQa.Run
grep -q 'HPR_BOUNDARY_NATIVE_QA_PASS' "$out/author-native-qa.unity.log"
export HPR_BOUNDARY_RELEASE_OUT="$archive"
run_unity author-export -projectPath "$author" -executeMethod HprPackageBoundaryExporter.Run
grep -q 'HPR_BOUNDARY_RELEASE_EXPORT_PASS' "$out/author-export.unity.log"
python3 "$src/qa/verify_archive.py" --archive "$archive" >"$out/archive-verified.json"
run_unity buyer-create -createProject "$buyer"
run_unity buyer-import -projectPath "$buyer" -importPackage "$archive"
mkdir -p "$buyer/Assets/Editor"
cp "$src/qa/HprPackageBoundaryNativeQa.cs" "$buyer/Assets/Editor/"
export HPR_BOUNDARY_QA_OUT="$out/buyer-qa-evidence"
run_unity buyer-native-qa -projectPath "$buyer" -executeMethod HprPackageBoundaryNativeQa.Run
grep -q 'HPR_BOUNDARY_NATIVE_QA_PASS' "$out/buyer-native-qa.unity.log"
python3 - "$out" <<'PY'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]); a=p/'author-qa-evidence/receipt.txt'; b=p/'buyer-qa-evidence/receipt.txt'
assert a.is_file() and b.is_file(), 'native receipts missing'
assert a.read_text()==b.read_text(), 'consumer test results differ from author results'
assert all(line.endswith('=PASS') or line.startswith('unity_version=') for line in a.read_text().splitlines())
assert json.loads((p/'archive-verified.json').read_text())['status']=='PASS'
print(json.dumps({'status':'PASS','unity_version':a.read_text().split('unity_version=')[-1].strip(),
    'real_archive_bytes':(p/'hpr-package-boundary-candidate.unitypackage').stat().st_size,
    'checks':len(a.read_text().splitlines())-1,
    'author_and_independent_buyer_import':'PASS','archive_source_scope':'PASS'},indent=2))
PY
