#!/usr/bin/env bash
set -euo pipefail
src=/data/var/marketplace-account-setup/unity-20261121-wave51/original-archive-sample-authoring/baseline/Assets
work=/data/var/marketplace-account-setup/unity-20261121-wave52/real-moved-guid-fixture
qa=$(cd "$(dirname "$0")" && pwd)
unity=/data/apps/Unity/Hub/Editor/2022.3.22f1/Editor/Unity
[[ ! -e "$work" && -d "$src/HPRUpgradeExample" && -x "$unity" ]] || {
 echo "Refusing duplicate or missing original fixture" >&2; exit 3; }
mkdir -p "$work/source/Assets"
cp -a "$src/HPRUpgradeExample" "$work/source/Assets/"
cp -a "$src/HPRUpgradeExample.meta" "$work/source/Assets/"
sourcefile="$work/source/Assets/HPRUpgradeExample/Example.txt"
source_meta="$sourcefile.meta"
[[ -s "$sourcefile" && -s "$source_meta" && ! -e "$work/source/Assets/HPRUpgradeExample/ExampleMoved.txt" ]] || exit 4
mv -- "$sourcefile" "$work/source/Assets/HPRUpgradeExample/ExampleMoved.txt"
mv -- "$source_meta" "$work/source/Assets/HPRUpgradeExample/ExampleMoved.txt.meta"
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
project="$work/author-project"
timeout 450 "$unity" -batchmode -nographics -quit -createProject "$project" -logFile "$work/create.unity.log" > "$work/create.stdout" 2>&1
cp -a "$work/source/Assets/HPRUpgradeExample" "$project/Assets/"
cp -a "$work/source/Assets/HPRUpgradeExample.meta" "$project/Assets/"
mkdir -p "$project/Assets/Editor"
cp -- "$qa/HprCoexistenceMovedRealExporter.cs" "$project/Assets/Editor/"
export HPR_COEXISTENCE_MOVED_EXPORT="$work/moved-path-same-guid.unitypackage"
timeout 450 "$unity" -batchmode -nographics -quit -projectPath "$project" -executeMethod HprCoexistenceMovedRealExporter.Run \
  -logFile "$work/export.unity.log" > "$work/export.stdout" 2>&1
grep -q 'HPR_REAL_MOVED_GUID_EXPORTED' "$work/export.unity.log"
python3 - "$src" "$work" <<'PY'
from pathlib import Path
import sys,tarfile,hashlib,json,re
source=Path(sys.argv[1]);work=Path(sys.argv[2]);p=work/'moved-path-same-guid.unitypackage'
assets={};content={};meta={}
with tarfile.open(p,'r:gz') as f:
 for item in f:
  if not item.isfile():continue
  name=item.name.removeprefix('./');part=name.split('/')
  if len(part)!=2 or not re.fullmatch('[0-9a-f]{32}',part[0]):raise ValueError('Bad Unity member '+name)
  raw=f.extractfile(item).read()
  if part[1]=='pathname':assets[raw.decode('utf8').strip()]=part[0]
  elif part[1]=='asset':content[part[0]]=raw
  elif part[1]=='asset.meta':meta[part[0]]=raw
expected={
 'Assets/HPRUpgradeExample': source/'HPRUpgradeExample.meta',
 'Assets/HPRUpgradeExample/README.md': source/'HPRUpgradeExample/README.md.meta',
 'Assets/HPRUpgradeExample/ExampleMoved.txt': source/'HPRUpgradeExample/Example.txt.meta'
}
assert set(assets)==set(expected)
for path,original_meta in expected.items():
 guid=re.search(rb'(?m)^guid: ([a-f0-9]{32})',original_meta.read_bytes()).group(1).decode()
 assert assets[path]==guid and meta[guid]==original_meta.read_bytes()
 if not path.endswith('HPRUpgradeExample'):
  original=source/'HPRUpgradeExample'/Path(path).name.replace('ExampleMoved','Example')
  assert content[guid]==original.read_bytes()
result={'unity_export':'PASS','three_correct_paths':True,'original_guids_unchanged':True,
 'moved_path':'Assets/HPRUpgradeExample/ExampleMoved.txt',
 'old_path':'Assets/HPRUpgradeExample/Example.txt',
 'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'files':assets}
with (work/'verified-original-move.json').open('x') as f:json.dump(result,f,indent=2)
print('UNITY_REAL_MOVED_PATH_ORIGINAL_GUID_PASS',result['source_sha256'],len(assets))
PY
