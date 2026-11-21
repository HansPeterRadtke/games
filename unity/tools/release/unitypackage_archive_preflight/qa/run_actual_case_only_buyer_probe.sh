#!/usr/bin/env bash
# No original package is modified: two first-party archives imported only
# into a brand-new disposable owner-specific Unity project.
set -euo pipefail
version=${1:?Installed Unity version required}
[[ "$version" = 2022.3.22f1 || "$version" = 6000.6.8f1 ]] || exit 2
qa=$(cd "$(dirname "$0")" && pwd)
base=/data/var/marketplace-account-setup/unity-20261121-wave52
out="$base/actual-case-only-coexistence-buyer-${version//./-}"
first=/data/src/worktrees/unity-package-boundary-audit-20261121/unity/tools/release/unitypackage_archive_preflight/Assets/HPRArchivePreflight/Samples/HprExample-baseline.unitypackage
second="$base/real-case-only-path-fixture/case-only-path-distinct-guid.unitypackage"
unity=/data/apps/Unity/Hub/Editor/$version/Editor/Unity
[[ ! -e "$out" && -x "$unity" && -s "$first" && -s "$second" ]] || {
 echo 'Refusing duplicate/unknown original case-only buyer-import effect' >&2; exit 4; }
mkdir -p "$out"
project="$out/disposable-buyer-project"
sha256sum "$first" "$second" > "$out/originals-before.sha256"
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
run(){
 stage=$1;shift
 echo "ORIGINAL_CASE_ONLY_REAL_BUYER $version $stage"
 timeout 460 "$unity" -batchmode -nographics -quit "$@" -logFile "$out/$stage.unity.log" > "$out/$stage.stdout" 2>&1 || {
  grep -E -C2 'error CS|Exception|GUID|Import' "$out/$stage.unity.log" | tail -35 >&2 || :
  exit 6
 }
}
run create-project -createProject "$project"
run import-original -projectPath "$project" -importPackage "$first"
run import-competing-case -projectPath "$project" -importPackage "$second"
mkdir -p "$project/Assets/Editor"
cp -- "$qa/HprCoexistenceCaseOnlyBuyerProbe.cs" "$project/Assets/Editor/"
export HPR_CASE_ONLY_REAL_OBSERVATION="$out/actual-native-case-only-path-observation.txt"
run actual-assetdatabase-observation -projectPath "$project" -executeMethod HprCoexistenceCaseOnlyBuyerProbe.Run
grep -q 'HPR_CASE_ONLY_REAL_BUYER_OBSERVATION_SAVED' "$out/actual-assetdatabase-observation.unity.log"
sha256sum "$first" "$second" > "$out/originals-after.sha256"
diff -q "$out/originals-before.sha256" "$out/originals-after.sha256"
cat "$out/actual-native-case-only-path-observation.txt"
