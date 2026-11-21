#!/usr/bin/env bash
# First-party genuine Unity .unitypackage exports, no pre-existing project mutations.
set -euo pipefail
root=$(cd "$(dirname "$0")" && pwd)
base=/data/var/marketplace-account-setup/unity-20261121-wave51/original-archive-sample-authoring
unity=/data/apps/Unity/Hub/Editor/2022.3.22f1/Editor/Unity
[[ -x "$unity" ]] || exit 3
[[ ! -e "$base" ]] || { echo 'Refusing to repeat uncertain training archive effects' >&2;exit 4; }
python3 "$root/build_original_sample_sources.py"
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
for variant in baseline additions_only changed_guid; do
  working="$base/$variant"
  project="$working/author-project"
  exported="$working/HprExample-$variant.unitypackage"
  [[ ! -e "$project" && ! -e "$exported" ]] || { echo "Existing training sample: $variant" >&2;exit 5; }
  echo "EXAMPLE_UNITY_NATIVE_EXPORT $variant project-create"
  timeout 400 "$unity" -batchmode -nographics -quit -createProject "$project" -logFile "$working/project-create.unity.log" >"$working/project-create.stdout" 2>&1
  cp -a "$working/Assets/HPRUpgradeExample" "$project/Assets/"
  cp -a "$working/Assets/HPRUpgradeExample.meta" "$project/Assets/"
  mkdir -p "$project/Assets/Editor"
  cp -- "$root/HprOriginalArchiveExamplesExporter.cs" "$project/Assets/Editor/"
  export HPR_ORIGINAL_EXAMPLE_OUTPUT="$exported"
  echo "EXAMPLE_UNITY_NATIVE_EXPORT $variant export-original"
  timeout 450 "$unity" -batchmode -nographics -quit -projectPath "$project" -executeMethod HprOriginalArchiveExamplesExporter.Run -logFile "$working/original-export.unity.log" >"$working/original-export.stdout" 2>&1
  grep -q 'HPR_FIRST_PARTY_TRAINING_EXAMPLE_EXPORTED' "$working/original-export.unity.log"
  test -s "$exported"
done
python3 - "$base" <<'PY'
import tarfile,hashlib,json,sys
from pathlib import Path
base=Path(sys.argv[1]);rows={}
for variant in ('baseline','additions_only','changed_guid'):
    p=base/variant/f'HprExample-{variant}.unitypackage'
    files={};asset_blob={}
    with tarfile.open(p,'r:gz') as archive:
        for m in archive:
            if not m.isfile():continue
            name=m.name.removeprefix('./')
            parts=name.split('/')
            if len(parts)!=2:raise RuntimeError('Unexpected member: '+name)
            data=archive.extractfile(m).read()
            if parts[1]=='pathname':files[data.decode().strip()]=parts[0]
            elif parts[1]=='asset':asset_blob[parts[0]]=hashlib.sha256(data).hexdigest()
    expected=3 if variant!='additions_only' else 4
    assert len(files)==expected,(variant,files)
    rows[variant]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,'assets':files,'source_hashes':asset_blob}
original=rows['baseline']['assets'];add=rows['additions_only']['assets'];broken=rows['changed_guid']['assets']
assert len(set(original)-set(add))==0
assert all(add[key]==value for key,value in original.items())
assert all(broken[key]==value for key,value in original.items() if not key.endswith('README.md'))
assert broken['Assets/HPRUpgradeExample/README.md']!=original['Assets/HPRUpgradeExample/README.md']
with (base/'UNITY_NATIVE_EXPORT_VERIFIED.json').open('x') as f:json.dump(rows,f,indent=2)
print('FIRST_PARTY_UNITY_EXPORTED_EXAMPLES_CONFIRMED',len(rows),'variants')
for variant,row in rows.items():print(variant,row['bytes'],row['sha256'],len(row['assets']))
PY
