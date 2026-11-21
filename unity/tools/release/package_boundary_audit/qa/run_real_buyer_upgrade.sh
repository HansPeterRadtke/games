#!/usr/bin/env bash
# True existing-buyer installation of the old package followed by upgrade to
# the current package. Disposable project only; no publisher or owner assets.
set -euo pipefail
version=${1:?Unity Editor version}
label=${2:?Unique owner QA label}
[[ "$version" = 2022.3.22f1 || "$version" = 6000.6.8f1 ]] || exit 2
[[ "$label" =~ ^[a-zA-Z0-9-]+$ ]] || exit 2
source=$(cd "$(dirname "$0")" && pwd)
base=/data/var/marketplace-account-setup/unity-20261121-wave49/boundary-upgrade-${version//./-}-$label
[[ ! -e "$base" ]] || { echo 'Refusing duplicate or uncertain upgrade test' >&2; exit 3; }
mkdir -p "$base"
project="$base/independent-existing-buyer"
unity=/data/apps/Unity/Hub/Editor/$version/Editor/Unity
legacy=/data/var/marketplace-account-setup/unity-20261121-afternoon/native-2022-3-22f1-cleanmeta1/hpr-package-boundary-candidate.unitypackage
updated=/data/var/marketplace-account-setup/unity-20261121-afternoon/native-2022-3-22f1-upgrade-final1/hpr-package-boundary-candidate.unitypackage
[[ -x "$unity" && -s "$legacy" && -s "$updated" ]] || exit 4
export HOME=/home/hans USER=hans LOGNAME=hans
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
export HPR_BOUNDARY_UPGRADE_EVIDENCE_ROOT="$base"
run(){
 local phase=$1;shift
 echo "HPR_NATIVE_CUSTOMER_UPGRADE $version $phase"
 timeout 440 "$unity" -batchmode -nographics -quit "$@" -logFile "$base/$phase.unity.log" >"$base/$phase.stdout" 2>&1 || {
  echo "Native real buyer upgrade failed: $phase" >&2
  grep -E -C2 'error CS|Exception|HPR_REAL_UPGRADE_.*FAIL' "$base/$phase.unity.log" | tail -35 >&2 || true
  exit 5
 }
}
run fresh-buyer-create -createProject "$project"
run original-v1-import -projectPath "$project" -importPackage "$legacy"
mkdir -p "$project/Assets/Editor" "$project/Assets/HprBoundaryUpgradeCustomerFixture"
# Real buyer runtime script must have a MonoScript GUID in Assembly-CSharp;
# an Editor-only ScriptableObject source serialized with m_Script fileID 0
# and failed to reload after the genuine first upgrade in the negative run.
cp "$source/HprRealUpgradeBuyerReference.cs" "$project/Assets/HprBoundaryUpgradeCustomerFixture/"
cp "$source/HprBoundaryRealUpgradeBeforeQa.cs" "$project/Assets/Editor/"
run original-v1-buyer-baseline -projectPath "$project" -executeMethod HprBoundaryRealUpgradeBeforeQa.Run
grep -q 'HPR_REAL_UPGRADE_BEFORE_NATIVE_PASS' "$base/original-v1-buyer-baseline.unity.log"
[[ -s "$base/before-native-vendor-identity.json" ]] || exit 6
run existing-buyer-upgrade-to-v2 -projectPath "$project" -importPackage "$updated"
cp "$source/HprBoundaryRealUpgradeAfterQa.cs" "$project/Assets/Editor/"
run upgraded-v2-buyer-check -projectPath "$project" -executeMethod HprBoundaryRealUpgradeAfterQa.Run
grep -q 'HPR_REAL_BUYER_UPGRADE_NATIVE_PASS' "$base/upgraded-v2-buyer-check.unity.log"
[[ -s "$base/after-native-upgrade-receipt.txt" && -s "$base/actual-native-upgrade-diff.json" ]] || exit 7
cat "$base/after-native-upgrade-receipt.txt"
python3 - "$base" "$legacy" "$updated" <<'PY'
from pathlib import Path
import json,sys,tarfile,hashlib
p=Path(sys.argv[1]);assert json.loads((p/'actual-native-upgrade-diff.json').read_text())['status']=='ADDITIONS_ONLY'
for n,f in [('legacy_archive_sha256',Path(sys.argv[2])),('updated_archive_sha256',Path(sys.argv[3]))]:print(n,hashlib.sha256(f.read_bytes()).hexdigest())
print('HPR_REAL_PACKAGE_CUSTOMER_UPGRADE_RESULT=PASS')
PY
