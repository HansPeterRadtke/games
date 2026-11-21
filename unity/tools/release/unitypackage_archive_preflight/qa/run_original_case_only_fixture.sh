#!/usr/bin/env bash
set -euo pipefail
orig=/data/var/marketplace-account-setup/unity-20261121-wave51/original-archive-sample-authoring/baseline/Assets
base=/data/var/marketplace-account-setup/unity-20261121-wave52/real-case-only-path-fixture
qa=$(cd "$(dirname "$0")" && pwd)
unity=/data/apps/Unity/Hub/Editor/2022.3.22f1/Editor/Unity
[[ ! -e "$base" && -x "$unity" && -d "$orig/HPRUpgradeExample" ]] || {
 echo 'Refusing uncertain repeated case-only fixture effect' >&2; exit 3; }
mkdir -p "$base/source/Assets"
cp -a "$orig/HPRUpgradeExample" "$base/source/Assets/"
cp -a "$orig/HPRUpgradeExample.meta" "$base/source/Assets/"
path="$base/source/Assets/HPRUpgradeExample/Example.txt"
meta="$path.meta"
[[ -s "$path" && -s "$meta" ]] || exit 4
mv -- "$path" "$base/source/Assets/HPRUpgradeExample/example.TXT"
mv -- "$meta" "$base/source/Assets/HPRUpgradeExample/example.TXT.meta"
python3 - "$base/source/Assets/HPRUpgradeExample/example.TXT.meta" <<'PY'
import sys,hashlib,re
from pathlib import Path
p=Path(sys.argv[1]);s=p.read_text()
new=hashlib.sha256(b'original-hpr-unity-independent-case-only-collision-2026-11-21').hexdigest()[:32]
s2,count=re.subn(r'(?m)^guid: [a-f0-9]{32}$','guid: '+new,s)
assert count==1 and s2!=s
p.write_text(s2)
print('ORIGINAL_CASE_ONLY_INDEPENDENT_GUID',new)
PY
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
project="$base/author-project"
echo CASE_ONLY_ORIGINAL_AUTHOR_PROJECT
 timeout 450 "$unity" -batchmode -nographics -quit -createProject "$project" -logFile "$base/create.unity.log" > "$base/create.stdout" 2>&1
cp -a "$base/source/Assets/HPRUpgradeExample" "$project/Assets/"
cp -a "$base/source/Assets/HPRUpgradeExample.meta" "$project/Assets/"
mkdir -p "$project/Assets/Editor"
cp -- "$qa/HprCoexistenceCaseOnlyRealExporter.cs" "$project/Assets/Editor/"
export HPR_COEXISTENCE_CASE_EXPORT="$base/case-only-path-distinct-guid.unitypackage"
echo CASE_ONLY_ORIGINAL_UNITY_EXPORT
 timeout 450 "$unity" -batchmode -nographics -quit -projectPath "$project" -executeMethod HprCoexistenceCaseOnlyRealExporter.Run -logFile "$base/export.unity.log" > "$base/export.stdout" 2>&1
grep -q HPR_REAL_CASE_ONLY_PATH_EXPORTED "$base/export.unity.log"
python3 - "$base" "$orig" <<'PY'
import sys,hashlib,tarfile,re,json
from pathlib import Path
base=Path(sys.argv[1]);orig=Path(sys.argv[2]);p=base/'case-only-path-distinct-guid.unitypackage'
paths={};meta={};content={}
with tarfile.open(p,'r:gz') as z:
 for member in z:
  if not member.isfile():continue
  name=member.name.removeprefix('./');pair=name.split('/')
  assert len(pair)==2 and re.fullmatch('[a-f0-9]{32}',pair[0])
  b=z.extractfile(member).read()
  if pair[1]=='pathname':paths[b.decode('utf8').strip()]=pair[0]
  elif pair[1]=='asset':content[pair[0]]=b
  elif pair[1]=='asset.meta':meta[pair[0]]=b
assert set(paths)=={'Assets/HPRUpgradeExample','Assets/HPRUpgradeExample/README.md','Assets/HPRUpgradeExample/example.TXT'}
new=paths['Assets/HPRUpgradeExample/example.TXT'];old=re.search(rb'(?m)^guid: ([a-f0-9]{32})',
 (orig/'HPRUpgradeExample/Example.txt.meta').read_bytes()).group(1).decode()
assert new!=old and content[new]==(orig/'HPRUpgradeExample/Example.txt').read_bytes()
assert meta[new]==(base/'source/Assets/HPRUpgradeExample/example.TXT.meta').read_bytes()
assert paths['Assets/HPRUpgradeExample/README.md']==re.search(rb'(?m)^guid: ([a-f0-9]{32})',
 (orig/'HPRUpgradeExample/README.md.meta').read_bytes()).group(1).decode()
receipt={'result':'PASS','source':'original_first_party_real_Unity_ExportPackage',
 'archive_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
 'source_path':'Assets/HPRUpgradeExample/example.TXT',
 'comparison_baseline_path':'Assets/HPRUpgradeExample/Example.txt',
 'distinct_guid':new,'previous_guid':old,'verified_assets':paths}
with (base/'verified-real-case-only-source.json').open('x') as f:json.dump(receipt,f,indent=2)
print('ORIGINAL_REAL_UNITY_CASE_ONLY_PACKAGE_VERIFIED',receipt['archive_sha256'],len(paths))
PY
