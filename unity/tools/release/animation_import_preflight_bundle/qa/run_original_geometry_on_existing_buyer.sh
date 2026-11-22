#!/usr/bin/env bash
# Native real original first-party mesh + prefab geometry checks on an
# already independently imported, privately owned disposable buyer project.
# Does not touch vendor roots, existing owner project or marketplace account.
set -euo pipefail
version=${1:?Unity version}
[[ "$version" = 2022.3.22f1 || "$version" = 6000.6.8f1 ]] || exit 2
base=/data/var/marketplace-account-setup/unity-20261122-wave55
run="$base/combined-animation-native-${version//./-}-clip-prefab-fix1"
project="$run/independent-buyer-project"
source=$(cd "$(dirname "$0")" && pwd)/HprOriginalAnimationGeometryQa.cs
unity=/data/apps/Unity/Hub/Editor/$version/Editor/Unity
out="$run/final-independent-buyer-original-geometry.txt"
[[ -x "$unity" && -d "$project/Assets" && -s "$source" && ! -e "$out" ]] || {
 echo 'Original buyer project or fresh proof destination missing'; exit 3;
}
[[ -s "$run/strict-original-first-party-package.json" &&
   -s "$run/buyer-customer-QA/combined-original-customer-warning.txt" ]] || {
 echo 'Original independent buyer and package acceptance receipt not complete';exit 4;
}
mkdir -p "$project/Assets/Editor"
target="$project/Assets/Editor/HprOriginalAnimationGeometryQa.cs"
[[ ! -e "$target" ]] || { echo 'Duplicate private geometry QA detected';exit 4; }
cp -- "$source" "$target"
export HPR_ORIGINAL_ANIM_GEOMETRY_QA_OUT="$out"
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
log="$run/final-independent-buyer-original-geometry.unity.log"
[[ ! -e "$log" ]] || exit 5
timeout 480 "$unity" -batchmode -nographics -quit -projectPath "$project" \
  -executeMethod HprOriginalAnimationGeometryQa.Run -logFile "$log" \
  > "$run/final-independent-buyer-original-geometry.stdout" 2>&1 || {
 grep -E -C2 'error CS|Exception|HPR_ORIGINAL_' "$log" | tail -42 >&2 || :
 exit 6;
}
grep -q HPR_ORIGINAL_COMBINED_GEOMETRY_QA_PASS "$log"
test -s "$out"
cat "$out"
