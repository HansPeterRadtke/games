#!/usr/bin/env bash
# Export an exact CURRENT first-party source package in a NEW Unity author project.
# Do not reuse an earlier release package, cache or source test result.
set -euo pipefail
version=${1:?2022.3.22f1 or 6000.6.8f1}
label=${2:?new unique author label}
[[ "$label" =~ ^[a-z0-9_-]{4,30}$ ]] || exit 2
case "$version" in
  2022.3.22f1|6000.6.8f1) ;;
  *) echo 'Unsupported native Unity version' >&2;exit 2;;
esac
root=/data/var/marketplace-account-setup/unity-player-reference-probe-20261123-wave63
work="$root/$label"
qa=$(cd "$(dirname "$0")" && pwd)
source=$(cd "$qa/../Assets" && pwd)/HPRPlayerReferenceProbe
unity="/data/apps/Unity/Hub/Editor/$version/Editor/Unity"
project="$work/independent-current-source-author"
archive="$work/HPR_Player_Reference_Probe_${version//./-}_current_original.unitypackage"
[[ -x "$unity" && -f "$qa/verify_original_demo_archive.py" && -s "$source/Runtime/HprPlayerReferenceProbe.cs" &&
    ! -e "$work" ]] || { echo 'Missing required original source or repeated label' >&2; exit 3; }
mkdir -p "$work"
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
run(){ stage=$1;shift;echo "HPR_CURRENT_MATCHED_NATIVE_STAGE $version $stage";
 timeout 480 "$unity" -batchmode -nographics -quit "$@" -logFile "$work/$stage.unity.log" \
 >"$work/$stage.stdout" 2>&1 ||{
  grep -E 'HPR_PLAYER_REFERENCE|error CS[0-9]|Exception' "$work/$stage.unity.log"|tail -25 >&2||true;exit 4;
 }
}
run create-independent-author -createProject "$project"
python3 "$qa/stage_original_probe_source.py" "$source" "$project/Assets"
mkdir -p "$project/Assets/Editor"
cp "$qa/HprProbeQaAuthor.cs" "$project/Assets/Editor/"
HPR_PLAYER_PROBE_EXPECTED_ROOT_GUID=$(python3 "$qa/stage_original_probe_source.py" --root-guid "$source")
export HPR_PLAYER_PROBE_EXPECTED_ROOT_GUID
export HPR_PLAYER_PROBE_PACKAGE="$archive"
run export-current-firstparty-original -projectPath "$project" -executeMethod HprProbeQaAuthor.Run
grep -q HPR_PLAYER_REFERENCE_ORIGINAL_PACKAGE_AUTHOR_PASS "$work/export-current-firstparty-original.unity.log"
python3 "$qa/verify_original_demo_archive.py" "$archive" "$source" >"$work/current-source-and-meta-exact-integrity.json"
python3 - "$archive" "$source" <<'PYVERIFY'
import sys,hashlib,tarfile,json,pathlib
archive=pathlib.Path(sys.argv[1]);source=pathlib.Path(sys.argv[2])
with tarfile.open(archive,'r:gz') as t:
 members={m.name:t.extractfile(m).read() for m in t.getmembers() if m.isfile()}
 paths={k.split('/')[0]: v.decode().strip() for k,v in members.items() if k.endswith('/pathname')}
 runtimes=[k for k,p in paths.items() if p.endswith('/Runtime/HprPlayerReferenceProbe.cs')]
 assert len(runtimes)==1 and b'CaptureNow()' in members[runtimes[0]+'/asset']
 assert b'manualOnly' in members[runtimes[0]+'/asset']
 assert len(paths)>=20 and not any('/qa/' in p or 'HprProbeQa' in p for p in paths.values())
 expected='Assets/HPRPlayerReferenceProbe/Runtime/HprPlayerReferenceProbe.cs'
 assert hashlib.sha256(members[runtimes[0]+'/asset']).hexdigest()==hashlib.sha256((source/'Runtime/HprPlayerReferenceProbe.cs').read_bytes()).hexdigest()
 print(json.dumps({'status':'PASS_ACTUAL_NATIVE_AUTHOR_EXPORT_OF_CURRENT_MANUAL_CAPTURE_SOURCE',
                   'unity_version':sys.argv[1].split('/')[-1], 'source_entries':len(paths),
                   'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}))
PYVERIFY
printf 'HPR_ACTUAL_NATIVE_CURRENT_SOURCE_ARCHIVE_VERIFIED %s\n' "$archive"
