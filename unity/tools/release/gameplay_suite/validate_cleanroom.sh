#!/usr/bin/env bash
# Create a fresh disposable Unity project and independently verify buyer .unitypackage import.
# No Unity publisher API, purchases, browser state or account writes.
set -euo pipefail
src_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
unity=${UNITY_BIN:-/data/apps/Unity/Hub/Editor/6000.4.0f1/Editor/Unity}
release=${HPR_SUITE_RELEASE_ROOT:-/data/var/marketplace-account-setup/unity-consolidated-20261031/release}
project=${HPR_SUITE_CLEANROOM_PROJECT:-/data/tmp/hpr_gameplay_suite_cleanroom_20261031}
archive="$release/hpr-gameplay-systems-suite-candidate.unitypackage"
[[ -f "$archive" ]] || { echo 'Missing verified buyer archive' >&2; exit 3; }
[[ ! -e "$project" ]] || { echo 'Refusing to replace an existing test project' >&2; exit 4; }
mkdir -p "$project" "$release"
export HOME=/home/hans USER=hans LOGNAME=hans
export DISPLAY=${DISPLAY:-:1} XAUTHORITY=${XAUTHORITY:-/home/hans/.Xauthority}
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
echo 'CREATE_CLEANROOM_PROJECT'
timeout 420 "$unity" -batchmode -nographics -quit -createProject "$project" -logFile "$release/cleanroom-create.unity.log" >/dev/null 2>&1
echo 'IMPORT_BUYER_ARCHIVE'
timeout 420 "$unity" -batchmode -nographics -quit -projectPath "$project" -importPackage "$archive" -logFile "$release/cleanroom-import.unity.log" >/dev/null 2>&1
mkdir -p "$project/Assets/Editor"
cp -- "$src_dir/qa/HprGameplaySuiteCleanroomValidator.cs" "$project/Assets/Editor/"
export HPR_SUITE_CLEANROOM_RECEIPT="$release/$(basename "$project")-scene-receipt.txt"
[[ ! -e "$HPR_SUITE_CLEANROOM_RECEIPT" ]] || { echo "Existing scene receipt" >&2; exit 5; }
echo 'VERIFY_ACTUAL_IMPORTED_SCENE'
timeout 420 "$unity" -batchmode -nographics -quit -projectPath "$project" -executeMethod HprGameplaySuiteCleanroomValidator.Run -logFile "$release/cleanroom-qa.unity.log" >/dev/null 2>&1
test -s "$HPR_SUITE_CLEANROOM_RECEIPT"
cat "$HPR_SUITE_CLEANROOM_RECEIPT"
echo 'VERIFY_ACTUAL_RUNTIME_INTEGRATION'
cp -- "$src_dir/qa/HprGameplaySuiteRuntimeSmokeValidator.cs" "$project/Assets/Editor/"
export HPR_SUITE_SMOKE_RECEIPT="$release/$(basename "$project")-runtime-receipt.txt"
[[ ! -e "$HPR_SUITE_SMOKE_RECEIPT" ]] || { echo "Existing runtime receipt" >&2; exit 6; }
timeout 420 "$unity" -batchmode -nographics -quit -projectPath "$project" -executeMethod HprGameplaySuiteRuntimeSmokeValidator.Run -logFile "$release/cleanroom-runtime.unity.log" >/dev/null 2>&1
test -s "$HPR_SUITE_SMOKE_RECEIPT"
cat "$HPR_SUITE_SMOKE_RECEIPT"
echo 'CLEANROOM_VERIFIED'
