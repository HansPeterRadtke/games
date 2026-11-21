#!/usr/bin/env bash
# Explicitly verified recovery of prior failed TEST exporter, no owner effects.
# The first failed batch created an author project but *no* sample archive.
set -euo pipefail
root=$(cd "$(dirname "$0")" && pwd)
base=/data/var/marketplace-account-setup/unity-20261121-wave51/original-archive-sample-authoring
unity=/data/apps/Unity/Hub/Editor/2022.3.22f1/Editor/Unity
[[ -x "$unity" && -f "$base/source-manifest.json" ]] || exit 2
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
for variant in baseline additions_only changed_guid; do
  working="$base/$variant"
  project="$working/author-project"
  exported="$working/HprExample-$variant.unitypackage"
  [[ -d "$working/Assets/HPRUpgradeExample" && ! -e "$exported" ]] || {
    echo "Cannot safely create unknown/repeated Unity example $variant" >&2;exit 3; }
  if [[ "$variant" == baseline ]]; then
    [[ -d "$project" && -s "$working/original-export.unity.log" &&
       ! -e "$working/original-export-resume1.unity.log" ]] || exit 4
    grep -q 'Unexpected first-party training example asset scope' "$working/original-export.unity.log" || exit 4
  else
    [[ ! -e "$project" && ! -e "$working/project-create.unity.log" ]] || exit 5
    echo "FIRST_PARTY_UNITY_EXAMPLE $variant project-create"
    timeout 420 "$unity" -batchmode -nographics -quit -createProject "$project" \
      -logFile "$working/project-create.unity.log" > "$working/project-create.stdout" 2>&1
    cp -a "$working/Assets/HPRUpgradeExample" "$project/Assets/"
    cp -a "$working/Assets/HPRUpgradeExample.meta" "$project/Assets/"
  fi
  mkdir -p "$project/Assets/Editor"
  cp -- "$root/HprOriginalArchiveExamplesExporter.cs" "$project/Assets/Editor/"
  export HPR_ORIGINAL_EXAMPLE_OUTPUT="$exported"
  label=original-export
  [[ "$variant" == baseline ]] && label=original-export-resume1
  [[ ! -e "$working/$label.unity.log" ]] || exit 6
  echo "FIRST_PARTY_UNITY_EXAMPLE $variant $label"
  timeout 450 "$unity" -batchmode -nographics -quit -projectPath "$project" \
      -executeMethod HprOriginalArchiveExamplesExporter.Run \
      -logFile "$working/$label.unity.log" > "$working/$label.stdout" 2>&1
  grep -q 'HPR_FIRST_PARTY_TRAINING_EXAMPLE_EXPORTED' "$working/$label.unity.log"
  [[ -s "$exported" ]] || exit 7
done
python3 - "$base" <<'PY'
import tarfile,hashlib,json,sys
from pathlib import Path
base=Path(sys.argv[1]);manifest=json.loads((base/'source-manifest.json').read_text())
rows={}
for variant in ('baseline','additions_only','changed_guid'):
    p=base/variant/f'HprExample-{variant}.unitypackage'
    files={};contents={}
    with tarfile.open(p,'r:gz') as archive:
        for member in archive:
            if not member.isfile():continue
            name=member.name.removeprefix('./');parts=name.split('/')
            if len(parts)!=2:raise ValueError('Unexpected Unity sample archive member '+name)
            raw=archive.extractfile(member).read()
            if parts[1]=='pathname':files[raw.decode('utf-8').strip()]=parts[0]
            elif parts[1]=='asset':contents[parts[0]]=hashlib.sha256(raw).hexdigest()
    expected=3 if variant!='additions_only' else 4
    assert len(files)==expected,(variant,files)
    expected_source=next(x for x in manifest['variants'] if x['variant']==variant)
    for name,info in expected_source['source_assets'].items():
        path='Assets/HPRUpgradeExample/'+name
        assert files[path]==info['guid'] and contents[info['guid']]==info['sha256']
    rows[variant]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                   'bytes':p.stat().st_size,'assets':files,'source_hashes':contents}
original=rows['baseline']['assets'];add=rows['additions_only']['assets'];broken=rows['changed_guid']['assets']
assert len(original)==3 and len(add)==4 and len(broken)==3
assert all(add[key]==value for key,value in original.items())
assert all(broken[key]==value for key,value in original.items() if not key.endswith('README.md'))
assert broken['Assets/HPRUpgradeExample/README.md']!=original['Assets/HPRUpgradeExample/README.md']
with (base/'UNITY_NATIVE_EXPORT_VERIFIED.json').open('x') as f:json.dump(rows,f,indent=2)
print('FIRST_PARTY_UNITY_EXPORTED_EXAMPLES_CONFIRMED',len(rows),'variants')
for variant,row in rows.items():print(variant,row['bytes'],row['sha256'],len(row['assets']))
PY
