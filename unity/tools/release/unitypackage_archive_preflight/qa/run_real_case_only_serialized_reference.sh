#!/usr/bin/env bash
set -euo pipefail
version=${1:?Installed Unity version required}
[[ "$version" = 2022.3.22f1 || "$version" = 6000.6.8f1 ]] || exit 2
root=$(cd "$(dirname "$0")" && pwd)
base=/data/var/marketplace-account-setup/unity-20261121-wave52
out="$base/serialized-reference-case-only-${version//./-}"
first=/data/src/worktrees/unity-package-boundary-audit-20261121/unity/tools/release/unitypackage_archive_preflight/Assets/HPRArchivePreflight/Samples/HprExample-baseline.unitypackage
second="$base/real-case-only-path-fixture/case-only-path-distinct-guid.unitypackage"
unity=/data/apps/Unity/Hub/Editor/$version/Editor/Unity
[[ ! -e "$out" && -s "$first" && -s "$second" && -x "$unity" ]] || {
 echo 'Refusing repeated/unknown serialized buyer case-only effects' >&2;exit 4; }
mkdir -p "$out"
project="$out/disposable-buyer-project"
sha256sum "$first" "$second" > "$out/input-archives-before.sha256"
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
run(){
 stage=$1;shift
 echo "ORIGINAL_CASE_ONLY_SERIALIZED_REFERENCE $version $stage"
 timeout 500 "$unity" -batchmode -nographics -quit "$@" -logFile "$out/$stage.unity.log" > "$out/$stage.stdout" 2>&1 || {
  echo "Stage failed: $stage; preserving full actual Unity log" >&2
  grep -E -C2 'error CS|Exception|HPR_CASE_ONLY|GUID' "$out/$stage.unity.log" | tail -40 >&2 || :
  exit 5
 }
}
run create -createProject "$project"
run import-original -projectPath "$project" -importPackage "$first"
mkdir -p "$project/Assets/Editor"
cp -- "$root/HprCaseOnlyReferenceHolder.cs" "$project/Assets/"
cp -- "$root/HprCaseOnlyReferenceBuyerProbe.cs" "$project/Assets/Editor/"
export HPR_CASE_ONLY_REFERENCE_PROOF_DIR="$out"
run prepare-buyer-reference -projectPath "$project" -executeMethod HprCaseOnlyReferenceBuyerProbe.Prepare
grep -q HPR_CASE_ONLY_SERIALIZED_BUYER_REFERENCE_PREPARED "$out/prepare-buyer-reference.unity.log"
sha256sum "$project/Assets/BuyerOwned/ExistingReference.asset" > "$out/owner-asset-before.sha256"
run import-conflicting-case -projectPath "$project" -importPackage "$second"
run audit-buyer-reference -projectPath "$project" -executeMethod HprCaseOnlyReferenceBuyerProbe.Audit
grep -q HPR_CASE_ONLY_SERIALIZED_BUYER_REFERENCE_AUDITED "$out/audit-buyer-reference.unity.log"
sha256sum "$project/Assets/BuyerOwned/ExistingReference.asset" > "$out/owner-asset-after.sha256"
diff -u "$out/owner-asset-before.sha256" "$out/owner-asset-after.sha256"
sha256sum "$first" "$second" > "$out/input-archives-after.sha256"
diff -u "$out/input-archives-before.sha256" "$out/input-archives-after.sha256"
cat "$out/buyer-reference-before.txt" "$out/buyer-reference-after.txt"
