#!/usr/bin/env bash
# Read-only real Gameplay Suite 161-asset check after successful buyer import.
set -euo pipefail
version=${1:?Editor version required}
[[ "$version" = 2022.3.22f1 || "$version" = 6000.6.8f1 ]] || exit 2
root=$(cd "$(dirname "$0")" && pwd)
unity=/data/apps/Unity/Hub/Editor/$version/Editor/Unity
base=/data/var/marketplace-account-setup/unity-20261121-wave51/native-${version//./-}-examples-final1
project="$base/fresh-independent-buyer-project"
evidence="$base/large-real-archive-evidence"
source=/data/var/marketplace-account-setup/unity-20261121-production/current-suite-release/hpr-gameplay-systems-suite-candidate.unitypackage
[[ -x "$unity" && -s "$source" && -s "$base/buyer-qa-evidence/native-receipt.txt" &&
   -d "$project/Assets/HPRArchivePreflight" && ! -e "$evidence" &&
   ! -e "$base/large-real-archive-qa.unity.log" ]] || {
  echo 'Refusing uncertain native large-archive QA replay' >&2; exit 4; }
grep -q 'included_changed_guid_sample_warns_accurately=PASS' "$base/buyer-qa-evidence/native-receipt.txt"
[[ ! -e "$project/Assets/Editor/HprArchivePreflightLargeRealQa.cs" ]] || exit 5
mkdir -p "$project/Assets/Editor"
cp -- "$root/HprArchivePreflightLargeRealQa.cs" "$project/Assets/Editor/"
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
export HPR_ARCHIVE_LARGE_REAL_INPUT="$source" HPR_ARCHIVE_LARGE_REAL_OUT="$evidence"
timeout 480 "$unity" -batchmode -nographics -quit -projectPath "$project" -executeMethod HprArchivePreflightLargeRealQa.Run \
    -logFile "$base/large-real-archive-qa.unity.log" >"$base/large-real-archive-qa.stdout" 2>&1 || {
  grep -E -C2 'HPR_ARCHIVE_LARGE_REAL_QA_FAIL|error CS|Exception' "$base/large-real-archive-qa.unity.log" | tail -40 >&2 || :
  exit 6;
}
grep -q 'HPR_ARCHIVE_LARGE_REAL_NATIVE_PASS' "$base/large-real-archive-qa.unity.log"
[[ -s "$evidence/large-real-receipt.txt" ]] || exit 7
cat "$evidence/large-real-receipt.txt"
