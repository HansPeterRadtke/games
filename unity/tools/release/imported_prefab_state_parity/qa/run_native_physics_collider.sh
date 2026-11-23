#!/usr/bin/env bash
# Original first-party capsule and character-controller geometry acceptance.
# Production source and private fixture in separate real Unity buyer projects.
set -euo pipefail
label=${1:?fresh native version evidence label}
[[ "$label" =~ ^[a-z0-9_-]{4,30}$ ]] || exit 2
root=/data/var/marketplace-account-setup/unity-player-reference-probe-20261123-wave63
work="$root/$label"
qa=$(cd "$(dirname "$0")" && pwd)
source=$(cd "$qa/../Assets" && pwd)/HPRImportedPrefabParity
editor22=/data/apps/Unity/Hub/Editor/2022.3.22f1/Editor/Unity
editor6=/data/apps/Unity/Hub/Editor/6000.6.8f1/Editor/Unity
[[ -x "$editor22" && -x "$editor6" && -d "$source" && ! -e "$work" ]] || exit 3
mkdir -p "$work"
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
run(){ local version=$1 step=$2;shift 2;
 echo "HPR_COLLIDER_ACTUAL_UNITY_STAGE $version $step"
 local cmd=$editor22;[[ "$version" == 6000.6.8f1 ]]&&cmd=$editor6
 timeout 440 "$cmd" -batchmode -nographics -quit "$@" -logFile "$work/${version//./-}-$step.unity.log" \
 >"$work/${version//./-}-$step.stdout" 2>&1 || {
  grep -E 'HPR_COLLIDER|error CS[0-9]|Exception' "$work/${version//./-}-$step.unity.log"|tail -24 >&2 || true;exit 5;
 }
}
author="$work/original-first-party-author"
run 2022.3.22f1 create-author -createProject "$author"
cp -r "$source" "$author/Assets/"
mkdir -p "$author/Assets/Editor"
cp "$qa/HprColliderPhysicsAuthorQa.cs" "$author/Assets/Editor/"
export HPR_COLLIDER_AUTHOR_ROOT="$work"
run 2022.3.22f1 export-original-collider-and-tool -projectPath "$author" -executeMethod HprColliderPhysicsAuthorQa.Run
grep -q HPR_COLLIDER_AUTHOR_ORIGINAL_PACKAGES_PASS "$work/2022-3-22f1-export-original-collider-and-tool.unity.log"
product="$work/HPR_ImportedPrefabParity_PhysicsOriginal.unitypackage"
fixture="$work/HPR_ColliderPhysicsOriginal_Qa_Fixture.unitypackage"
python3 - "$product" "$fixture" <<'PYA'
from pathlib import Path
import sys,tarfile
packages=[]
for raw in sys.argv[1:]:
 p=Path(raw);assert p.stat().st_size>400
 with tarfile.open(p,'r:gz') as t:
  paths={t.extractfile(m).read().decode().strip() for m in t.getmembers() if m.name.endswith('/pathname')}
 packages.append(paths)
assert 'Assets/HPRImportedPrefabParity/Editor/HprImportedPrefabStateParity.cs' in packages[0]
assert 'Assets/HPRColliderOriginal/CapsuleAndController.prefab' in packages[1]
assert not any('HprColliderPhysics' in x or '/qa/' in x for p in packages for x in p)
print('PRIVATE_ORIGINAL_SOURCE_AND_CAPSULE_TOOL_ARCHIVES_VERIFIED',list(map(len,packages)))
PYA
for version in 2022.3.22f1 6000.6.8f1;do
 buyer="$work/${version//./-}-buyer"
 run "$version" create-independent-buyer -createProject "$buyer"
 run "$version" import-original-prefab-tool -projectPath "$buyer" -importPackage "$product"
 run "$version" import-original-collider -projectPath "$buyer" -importPackage "$fixture"
 mkdir -p "$buyer/Assets/Editor"
 cp "$qa/HprColliderPhysicsBuyerQa.cs" "$buyer/Assets/Editor/"
 export HPR_COLLIDER_BUYER_REPORT="$work/${version//./-}-physics-original-receipt.json"
 run "$version" capture-native-physics -projectPath "$buyer" -executeMethod HprColliderPhysicsBuyerQa.Run
 grep -q HPR_COLLIDER_PHYSICS_BUYER_NATIVE_PASS "$work/${version//./-}-capture-native-physics.unity.log"
 python3 "$qa/verify_native_prefab_receipt.py" "$buyer" "$HPR_COLLIDER_BUYER_REPORT" \
 > "$work/${version//./-}-verified-file-rehash.json"
done
python3 "$qa/compare_native_receipts.py" \
 "$work/2022-3-22f1-physics-original-receipt.json" \
 "$work/6000-6-8f1-physics-original-receipt.json" \
 --output "$work/two-real-editors-collider-comparison.json"
python3 - "$work/two-real-editors-collider-comparison.json" <<'PYC'
import sys,json
j=json.load(open(sys.argv[1]));assert not any(j[k] for k in ('source_differences','dependency_differences','unverified_dependency_paths'))
print('HPR_COLLIDER_TWO_REAL_EDITORS_SOURCE_CONSISTENT',j['status'],'value_changes',len(j['changed_keys']))
PYC
