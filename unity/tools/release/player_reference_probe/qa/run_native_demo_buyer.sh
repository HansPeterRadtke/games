#!/usr/bin/env bash
# Fresh original Unity package -> two independent real buyer Editor projects -> actual Unity 6 Linux Player.
set -euo pipefail
origin=${1:?immutable first-party sample-package author label}
label=${2:?new independent buyer test label}
[[ "$origin" =~ ^[a-z0-9_-]{4,30}$ && "$label" =~ ^[a-z0-9_-]{4,30}$ ]] ||exit 2
root=/data/var/marketplace-account-setup/unity-player-reference-probe-20261123-wave63
archive_name=${HPR_DEMO_ARCHIVE_NAME:-HPR_Player_Reference_Probe_original_unity6_demo.unitypackage}
case "$archive_name" in
 HPR_Player_Reference_Probe_original_unity6_demo.unitypackage|HPR_Player_Reference_Probe_2022-3-22f1_current_original.unitypackage|HPR_Player_Reference_Probe_6000-6-8f1_current_original.unitypackage) ;;
 *) echo 'Refusing arbitrary unverified source package' >&2;exit 2;;
esac
archive="$root/$origin/$archive_name"
work="$root/$label"
qa=$(cd "$(dirname "$0")" && pwd)
editor22=/data/apps/Unity/Hub/Editor/2022.3.22f1/Editor/Unity
editor6=/data/apps/Unity/Hub/Editor/6000.6.8f1/Editor/Unity
[[ -x "$editor22" && -x "$editor6" && -s "$archive" && ! -e "$work" ]] ||{
 echo 'Original package missing or this buyer test was already performed' >&2;exit 3;
}
qa_dir=$(cd "$(dirname "$0")" && pwd)
current_source="$qa_dir/../Assets/HPRPlayerReferenceProbe"
python3 -B "$qa_dir/verify_original_demo_archive.py" "$archive" "$current_source"
mkdir -p "$work"
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
run(){ version=$1;phase=$2;shift 2;
 printf 'HPR_ORIGINAL_DEMO_NATIVE_BUYER_STAGE %s %s\n' "$version" "$phase"
 local exe="$editor22"; [[ "$version" == 6000.6.8f1 ]] && exe="$editor6"
 timeout 620 "$exe" -batchmode -nographics -quit "$@" -logFile "$work/${version//./-}-$phase.unity.log" \
 >"$work/${version//./-}-$phase.stdout" 2>&1 || {
 grep -E 'HPR_REAL_DEMO|error CS[0-9]|Exception|BuildFailed' "$work/${version//./-}-$phase.unity.log"|tail -18 >&2||true;exit 5;
 }
}
python3 - "$archive" <<'PYARCHIVE'
from pathlib import Path
import sys,tarfile
p=Path(sys.argv[1])
with tarfile.open(p,'r:gz') as t:
 paths={t.extractfile(m).read().decode().strip() for m in t.getmembers() if m.name.endswith('/pathname')}
root='Assets/HPRPlayerReferenceProbe/'
for part in ('README.md','Runtime/HprPlayerReferenceProbe.cs',
             'Editor/HprPlayerReferenceProbeWindow.cs',
             'Demo/Scripts/HprPlayerReferenceDemoItem.cs',
             'Demo/Resources/HPRSample/AssignedItem.asset',
             'Demo/Resources/HPRSample/OptionalItem.asset',
             'Demo/Resources/HPRSample/HPR_Demo_Reference.prefab',
             'Demo/Scenes/HPR_Player_Reference_Probe_Demo.unity',
             'Demo/README.md'):
 assert root+part in paths,(part, sorted(paths))
assert not any('/qa/' in x or 'HprProbeQa' in x for x in paths)
print('HPR_FIRST_PARTY_ORIGINAL_SOURCE_ARCHIVE_INTEGRITY_PASS',len(paths))
PYARCHIVE
for version in 2022.3.22f1 6000.6.8f1;do
 buyer="$work/${version//./-}-independent-buyer"
 run "$version" create -createProject "$buyer"
 run "$version" import-real-original-package -projectPath "$buyer" -importPackage "$archive"
 python3 -B "$qa/stage_original_probe_source.py" --verify-existing "$current_source" "$buyer/Assets" > "$work/${version//./-}-imported-source-identity.json"
 mkdir -p "$buyer/Assets/Editor" "$work/${version//./-}-qa"
 cp "$qa/HprProbeQaDemoBuyer.cs" "$buyer/Assets/Editor/"
 export HPR_DEMO_BUYER_ROOT="$work/${version//./-}-qa"
 export HPR_DEMO_BUYER_BUILD=0 HPR_DEMO_RELEASE_PLAYER=0
 if [[ "$version" == 6000.6.8f1 ]];then
  export HPR_DEMO_BUYER_BUILD=1 HPR_DEMO_RELEASE_PLAYER=1
 fi
 run "$version" real-native-demo-acceptance -projectPath "$buyer" -executeMethod HprProbeQaDemoBuyer.Run
 grep -q 'HPR_PLAYER_REFERENCE_ORIGINAL_DEMO_BUYER_NATIVE_PASS' "$work/${version//./-}-real-native-demo-acceptance.unity.log"
 python3 -B "$qa/stage_original_probe_source.py" --verify-existing "$current_source" "$buyer/Assets" > "$work/${version//./-}-post-qa-source-identity.json"
 if [[ "$version" == 6000.6.8f1 ]];then
  grep -q 'HPR_PLAYER_REFERENCE_ORIGINAL_DEMO_ACTUAL_LINUX_PLAYER_BUILD_PASS' "$work/${version//./-}-real-native-demo-acceptance.unity.log"
  [[ -s "$HPR_DEMO_BUYER_ROOT/OriginalDemoLinux64.x86_64" ]]||exit 6
 fi
done
python3 - "$work" <<'PYRECEIPTS'
import json,sys
from pathlib import Path
p=Path(sys.argv[1])
a=json.loads((p/'2022-3-22f1-qa/actual-original-demo-editor-baseline.json').read_text())
b=json.loads((p/'6000-6-8f1-qa/actual-original-demo-editor-baseline.json').read_text())
assert a['schema']==b['schema']==2
assert a['checkedCount']==b['checkedCount']==2
assert a['assignedCount']==b['assignedCount']==1
assert a['missingCount']==b['missingCount']==1
assert a['unsupportedCount']==b['unsupportedCount']==0
for x,y in zip(a['cases'],b['cases']):
 for k in ('id','sourceLookup','fieldName','status','referencedName','referencedType'):
  assert x[k]==y[k],(k,x[k],y[k])
assert a['unityVersion']!=b['unityVersion']
print('HPR_REAL_DEMO_SCENE_TWO_EDITORS_SOURCE_AND_SCOPED_REFERENCES_MATCH')
PYRECEIPTS
