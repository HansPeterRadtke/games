#!/usr/bin/env bash
# Fresh and independent first-party Unity 2022 native package export; no marketplace upload.
set -euo pipefail
buyer=${1:?existing verified original 2022 buyer label}
label=${2:?unique first-party 2022 retail author evidence label}
[[ "$buyer" =~ ^[a-z0-9_-]{4,30}$ && "$label" =~ ^[a-z0-9_-]{4,30}$ ]]||exit 2
root=/data/var/marketplace-account-setup/unity-player-reference-probe-20261123-wave63
project="$root/$buyer/2022-3-22f1-independent-buyer"
out="$root/$label"
qa=$(cd "$(dirname "$0")" && pwd)
retail=$(cd "$qa/../Assets" && pwd)/HPRPlayerReferenceProbe
unity=/data/apps/Unity/Hub/Editor/2022.3.22f1/Editor/Unity
[[ -x "$unity" && -d "$project/Assets/HPRPlayerReferenceProbe" && -s "$qa/HprProbeQaAuthor.cs" && ! -e "$out" && ! -e "$project/Assets/Editor/HprProbeQaAuthor.cs" ]]||{
 echo 'Current customer copy is unavailable or this author effect has already happened' >&2;exit 3;
}
mkdir -p "$out"
cp "$qa/HprProbeQaAuthor.cs" "$project/Assets/Editor/HprProbeQaAuthor.cs"
export HPR_PLAYER_PROBE_PACKAGE="$out/HPR_Player_Reference_Probe_Unity2022_original.unitypackage"
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
timeout 420 "$unity" -batchmode -nographics -quit -projectPath "$project" \
 -executeMethod HprProbeQaAuthor.Run -logFile "$out/original-unity2022-author.unity.log" \
 >"$out/original-unity2022-author.stdout" 2>&1 || {
 grep -E 'HPR_PLAYER_REFERENCE_ORIGINAL_PACKAGE_AUTHOR_PASS|error CS[0-9]|Exception' "$out/original-unity2022-author.unity.log"|tail -18 >&2||true;exit 5;
}
grep -q HPR_PLAYER_REFERENCE_ORIGINAL_PACKAGE_AUTHOR_PASS "$out/original-unity2022-author.unity.log"
python3 "$qa/verify_original_demo_archive.py" "$HPR_PLAYER_PROBE_PACKAGE" "$retail" \
 > "$out/original-unity2022-customer-source-guid-integrity.json"
cat "$out/original-unity2022-customer-source-guid-integrity.json"
printf 'NATIVE_UNITY2022_ORIGINAL_RETAIL_PACKAGE_SOURCE_AND_META_INTEGRITY_PASS\n'
