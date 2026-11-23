#!/usr/bin/env bash
# Reauthor only a first-party demo scene, preserving original archived version and all GUIDs.
set -euo pipefail
label=${1:?new first-party layout-correction evidence label}
[[ "$label" =~ ^[a-z0-9_-]{4,30}$ ]]||exit 2
root=/data/var/marketplace-account-setup/unity-player-reference-probe-20261123-wave63
work="$root/$label"
qa=$(cd "$(dirname "$0")" && pwd)
source=$(cd "$qa/../Assets" && pwd)/HPRPlayerReferenceProbe
unity=/data/apps/Unity/Hub/Editor/6000.6.8f1/Editor/Unity
[[ -x "$unity" && ! -e "$work" && -s "$qa/HprProbeQaRefineDemo.cs" ]]||exit 3
mkdir -p "$work"
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
run(){ name=$1;shift;echo "HPR_ORIGINAL_SAMPLE_LAYOUT_QA $name";
 timeout 590 "$unity" -batchmode -nographics -quit "$@" -logFile "$work/$name.unity.log" \
 >"$work/$name.stdout" 2>&1 || {
  grep -E 'HPR_FIRST_PARTY_DEMO|error CS[0-9]|Exception' "$work/$name.unity.log"|tail -20 >&2||true;exit 5;
 }
}
project="$work/original-first-party-revision-author"
run create-author -createProject "$project"
cp -r "$source" "$project/Assets/"
mkdir -p "$project/Assets/Editor"
cp "$qa/HprProbeQaRefineDemo.cs" "$project/Assets/Editor/"
export HPR_DEMO_REFINE_ROOT="$work"
run revise-real-first-party-scene -projectPath "$project" -executeMethod HprProbeQaRefineDemo.Run
grep -q HPR_FIRST_PARTY_DEMO_REAL_NATIVE_LAYOUT_REFINEMENT_PASS "$work/revise-real-first-party-scene.unity.log"
cp "$qa/HprProbeQaAuthor.cs" "$project/Assets/Editor/"
export HPR_PLAYER_PROBE_PACKAGE="$work/HPR_Player_Reference_Probe_original_unity6_demo.unitypackage"
run export-actual-revised-sample -projectPath "$project" -executeMethod HprProbeQaAuthor.Run
grep -q HPR_PLAYER_REFERENCE_ORIGINAL_PACKAGE_AUTHOR_PASS "$work/export-actual-revised-sample.unity.log"
python3 - "$work" <<'PYARCHIVE'
from pathlib import Path
import tarfile,sys
p=Path(sys.argv[1]);b=p/'HPR_Player_Reference_Probe_original_unity6_demo.unitypackage'
with tarfile.open(b,'r:gz') as t:
 paths={t.extractfile(f).read().decode().strip() for f in t.getmembers() if f.name.endswith('/pathname')}
assert 'Assets/HPRPlayerReferenceProbe/Demo/Scenes/HPR_Player_Reference_Probe_Demo.unity' in paths
assert 'Assets/HPRPlayerReferenceProbe/README.md' in paths
assert not any('HprProbeQa' in path or '/qa/' in path for path in paths)
print('HPR_REVISED_REAL_UNITY_DEMO_ARCHIVE_SOURCE_ONLY_PASS',len(paths),'paths')
PYARCHIVE
