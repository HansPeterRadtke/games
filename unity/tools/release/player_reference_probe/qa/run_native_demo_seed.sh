#!/usr/bin/env bash
# One-off private authoring of actual sample Unity assets. Never alters a buyer project.
set -euo pipefail
label=${1:?unique private first-party scene author label}
[[ "$label" =~ ^[a-z0-9_-]{4,30}$ ]] ||exit 2
root=/data/var/marketplace-account-setup/unity-player-reference-probe-20261123-wave63
work="$root/$label"
qa=$(cd "$(dirname "$0")" && pwd)
original=$(cd "$qa/../Assets" && pwd)/HPRPlayerReferenceProbe
unity=/data/apps/Unity/Hub/Editor/6000.6.8f1/Editor/Unity
[[ -x "$unity" && ! -e "$work" && -s "$qa/HprProbeQaCreateDemo.cs" && -s "$original/Demo/Scripts/HprPlayerReferenceDemoItem.cs" ]] ||exit 3
mkdir -p "$work"
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
run(){ name=$1;shift;echo "HPR_PLAYER_REFERENCE_FIRST_PARTY_SAMPLE_STAGE $name";
 timeout 550 "$unity" -batchmode -nographics -quit "$@" -logFile "$work/$name.unity.log" >"$work/$name.stdout" 2>&1 || {
 grep -E 'HPR_DEMO|HPR_PLAYER|error CS[0-9]|Exception' "$work/$name.unity.log"|tail -22 >&2||true;exit 5;
 }
}
project="$work/original-demo-author-project"
run create-author -createProject "$project"
cp -r "$original" "$project/Assets/"
mkdir -p "$project/Assets/Editor"
cp "$qa/HprProbeQaCreateDemo.cs" "$project/Assets/Editor/"
export HPR_DEMO_AUTHOR_ROOT="$work"
run generate-native-sample -projectPath "$project" -executeMethod HprProbeQaCreateDemo.Run
grep -q HPR_PLAYER_REFERENCE_ORIGINAL_DEMO_AUTHOR_PASS "$work/generate-native-sample.unity.log"
cp "$qa/HprProbeQaAuthor.cs" "$project/Assets/Editor/"
export HPR_PLAYER_PROBE_PACKAGE="$work/HPR_Player_Reference_Probe_original_unity6_demo.unitypackage"
run export-first-party-native-package -projectPath "$project" -executeMethod HprProbeQaAuthor.Run
grep -q HPR_PLAYER_REFERENCE_ORIGINAL_PACKAGE_AUTHOR_PASS "$work/export-first-party-native-package.unity.log"
python3 - "$work" <<'PY'
from pathlib import Path
import tarfile,sys
p=Path(sys.argv[1]);package=p/'HPR_Player_Reference_Probe_original_unity6_demo.unitypackage'
scene='Assets/HPRPlayerReferenceProbe/Demo/Scenes/HPR_Player_Reference_Probe_Demo.unity'
with tarfile.open(package,'r:gz') as t:
    paths={t.extractfile(m).read().decode().strip() for m in t.getmembers() if m.name.endswith('/pathname')}
assert scene in paths
for suffix in ('Demo/Resources/HPRSample/HPR_Demo_Reference.prefab',
               'Demo/Resources/HPRSample/AssignedItem.asset',
               'Demo/Resources/HPRSample/OptionalItem.asset',
               'Demo/Scripts/HprPlayerReferenceDemoItem.cs',
               'Demo/README.md','README.md'):
    assert 'Assets/HPRPlayerReferenceProbe/'+suffix in paths,suffix
assert not any('HprProbeQa' in x or '/qa/' in x for x in paths)
print('HPR_PLAYER_REFERENCE_FIRST_PARTY_DEMO_ORIGINAL_ARCHIVE_PASS',len(paths),'original_paths')
PY
