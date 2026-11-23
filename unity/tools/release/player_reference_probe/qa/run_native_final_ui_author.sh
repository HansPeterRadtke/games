#!/usr/bin/env bash
# Fresh first-party Unity-generated customer archive from the current documented, already QA-verified source.
set -euo pipefail
label=${1:?new unique first-party author label}
[[ "$label" =~ ^[a-z0-9_-]{4,30}$ ]]||exit 2
root=/data/var/marketplace-account-setup/unity-player-reference-probe-20261123-wave63
work="$root/$label"
qa=$(cd "$(dirname "$0")" && pwd)
source=$(cd "$qa/../Assets" && pwd)/HPRPlayerReferenceProbe
unity=/data/apps/Unity/Hub/Editor/6000.6.8f1/Editor/Unity
[[ ! -e "$work" && -x "$unity" && -s "$source/README.md" && -s "$source/Demo/Scenes/HPR_Player_Reference_Probe_Demo.unity" && -s "$qa/HprProbeQaAuthor.cs" ]]||exit 3
mkdir -p "$work"
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
run(){ phase=$1;shift;echo "HPR_ORIGINAL_FINAL_UI_AUTHOR $phase";
 timeout 510 "$unity" -batchmode -nographics -quit "$@" -logFile "$work/$phase.unity.log" >"$work/$phase.stdout" 2>&1 || {
 grep -E 'HPR_PLAYER|error CS[0-9]|Exception' "$work/$phase.unity.log"|tail -15 >&2||true;exit 5;
 }
}
project="$work/first-party-production-author"
run create-author -createProject "$project"
cp -r "$source" "$project/Assets/"
mkdir -p "$project/Assets/Editor"
cp "$qa/HprProbeQaAuthor.cs" "$project/Assets/Editor/"
export HPR_PLAYER_PROBE_PACKAGE="$work/HPR_Player_Reference_Probe_original_unity6_demo.unitypackage"
run original-export -projectPath "$project" -executeMethod HprProbeQaAuthor.Run
grep -q HPR_PLAYER_REFERENCE_ORIGINAL_PACKAGE_AUTHOR_PASS "$work/original-export.unity.log"
python3 "$qa/verify_original_demo_archive.py" "$HPR_PLAYER_PROBE_PACKAGE" "$source" >"$work/independent-original-package-byte-and-guid-parity.json"
printf 'HPR_FINAL_UI_NATIVE_FIRST_PARTY_PACKAGE_EXPORTED_AND_BYTE_VERIFIED\n'
