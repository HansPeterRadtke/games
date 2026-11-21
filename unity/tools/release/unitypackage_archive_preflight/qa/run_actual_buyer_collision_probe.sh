#!/usr/bin/env bash
set -euo pipefail
version=${1:?Installed Unity version}
[[ "$version" = 2022.3.22f1 || "$version" = 6000.6.8f1 ]] || exit 2
qa=$(cd "$(dirname "$0")" && pwd)
base=/data/var/marketplace-account-setup/unity-20261121-wave52
out="$base/actual-buyer-guid-collision-${version//./-}"
first=/data/src/worktrees/unity-package-boundary-audit-20261121/unity/tools/release/unitypackage_archive_preflight/Assets/HPRArchivePreflight/Samples/HprExample-baseline.unitypackage
second="$base/real-moved-guid-fixture/moved-path-same-guid.unitypackage"
unity=/data/apps/Unity/Hub/Editor/$version/Editor/Unity
[[ -x "$unity" && -s "$first" && -s "$second" && ! -e "$out" ]] || {
 echo 'Refusing repeated/unknown buyer import experiment effect' >&2;exit 4; }
mkdir -p "$out"
project="$out/fresh-disposable-independent-project"
sha256sum "$first" "$second" > "$out/first-and-second-before.sha256"
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
run(){
 stage=$1;shift
 echo "REAL_BUYER_COEXISTENCE $version $stage"
 timeout 460 "$unity" -batchmode -nographics -quit "$@" -logFile "$out/$stage.unity.log" >"$out/$stage.stdout" 2>&1 || {
   echo "NATIVE_COLLISION_STAGE_FAILED=$stage; inspect retained log, do not infer outcome" >&2
   grep -E 'error CS|Exception|GUID collision|Import' "$out/$stage.unity.log" | tail -22 >&2 || :
   exit 6
 }
}
run project-create -createProject "$project"
run import-first -projectPath "$project" -importPackage "$first"
run import-second -projectPath "$project" -importPackage "$second"
mkdir -p "$project/Assets/Editor"
cp -- "$qa/HprCoexistenceActualBuyerProbe.cs" "$project/Assets/Editor/"
export HPR_COEXISTENCE_REAL_IMPORT_RECEIPT="$out/actual-imported-project-observation.txt"
export HPR_COEXISTENCE_EXPECTED_SHARED_GUID="$(python3 - "$base/real-moved-guid-fixture/verified-original-move.json" <<'PY'
import json,sys
m=json.load(open(sys.argv[1]));print(m['files']['Assets/HPRUpgradeExample/ExampleMoved.txt'])
PY
)"
run actual-native-observation -projectPath "$project" -executeMethod HprCoexistenceActualBuyerProbe.Run
grep -q 'HPR_COEXISTENCE_REAL_DISPOSABLE_BUYER_OBSERVATION_SAVED' "$out/actual-native-observation.unity.log"
sha256sum "$first" "$second" > "$out/first-and-second-after.sha256"
diff -u "$out/first-and-second-before.sha256" "$out/first-and-second-after.sha256"
cat "$out/actual-imported-project-observation.txt"
