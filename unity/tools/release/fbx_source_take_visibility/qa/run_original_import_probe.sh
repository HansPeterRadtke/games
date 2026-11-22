#!/usr/bin/env bash
set -euo pipefail
version=${1:?installed Unity version}
[[ "$version" = 2022.3.22f1 || "$version" = 6000.6.8f1 ]] || exit 2
root=$(cd "$(dirname "$0")/.." && pwd)
base=/data/var/marketplace-account-setup/unity-20261122-wave54/native-${version//./-}-original-two-takes-probe
unity=/data/apps/Unity/Hub/Editor/${version}/Editor/Unity
[[ ! -e "$base" && -x "$unity" && -s "$root/Assets/HPRFbxSourceTakes/Samples/HPRTwoTakeCube.fbx" ]] || exit 3
mkdir -p "$base"
project="$base/author-project"
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
run(){ name=$1; shift; echo "UNITY_SOURCE_TAKE_PROBE $version $name"; timeout 470 "$unity" -batchmode -nographics -quit "$@" -logFile "$base/$name.unity.log" >"$base/$name.stdout" 2>&1 || { grep -E -C2 'error CS|Exception|HPR_TAKE' "$base/$name.unity.log" | tail -32 >&2 || true; exit 4; }; }
run create -createProject "$project"
cp -a "$root/Assets/HPRFbxSourceTakes" "$project/Assets/"
cp -a "$root/Assets/HPRFbxSourceTakes.meta" "$project/Assets/"
cp -- "$root/qa/HprFbxSourceTakeNativeQa.cs" "$project/Assets/Editor/HprFbxSourceTakeNativeQa.cs" 2>/dev/null || { mkdir -p "$project/Assets/Editor";cp -- "$root/qa/HprFbxSourceTakeNativeQa.cs" "$project/Assets/Editor/"; }
export HPR_SOURCE_TAKE_QA_OUT="$base/actual-original-unity-probe.txt"
run native-actual-two-take-probe -projectPath "$project" -executeMethod HprFbxSourceTakeNativeQa.Probe
grep -q 'HPR_SOURCE_TAKE_PROBE_SUCCESS' "$base/native-actual-two-take-probe.unity.log"
cat "$base/actual-original-unity-probe.txt"
