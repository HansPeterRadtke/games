#!/usr/bin/env bash
# Create only new isolated source-author and independent-buyer projects.
# Exactly one real Linux64 Player build and run; preserve all originals.
set -euo pipefail
label=${1:?unique test evidence label}
[[ "$label" =~ ^[a-z0-9_-]{4,30}$ ]]||exit 2
root=/data/var/marketplace-account-setup/unity-player-reference-probe-20261123-wave63
work="$root/$label"
qa=$(cd "$(dirname "$0")" && pwd)
original=$(cd "$qa/../Assets" && pwd)/HPRPlayerReferenceProbe
unity=/data/apps/Unity/Hub/Editor/6000.6.8f1/Editor/Unity
[[ -x "$unity" && -d "$original/Runtime" && -s "$qa/HprProbeQaAuthor.cs" &&
  ! -e "$work" ]] || { echo 'Refusing missing source or repeated original test label' >&2;exit 3; }
mkdir -p "$work"
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
run(){ name=$1;shift;echo "HPR_PLAYER_REFERENCE_REAL_STAGE $name";
 timeout 700 "$unity" -batchmode -nographics -quit "$@" -logFile "$work/$name.unity.log" \
 >"$work/$name.stdout" 2>&1 || {
  grep -E 'HPR_PLAYER|error CS[0-9]|Exception|BuildFailed' "$work/$name.unity.log"|tail -30 >&2||true;
  exit 5;
 }
}
author="$work/original-author-project"
buyer="$work/independent-buyer-project"
run create-author -createProject "$author"
cp -r "$original" "$author/Assets/"
mkdir -p "$author/Assets/Editor"
cp "$qa/HprProbeQaAuthor.cs" "$author/Assets/Editor/"
export HPR_PLAYER_PROBE_PACKAGE="$work/HPR_Player_Reference_Probe_original.unitypackage"
run original-package-export -projectPath "$author" -executeMethod HprProbeQaAuthor.Run
grep -q HPR_PLAYER_REFERENCE_ORIGINAL_PACKAGE_AUTHOR_PASS "$work/original-package-export.unity.log"
python3 - "$HPR_PLAYER_PROBE_PACKAGE" <<'PYARCHIVE'
import pathlib,sys,tarfile
p=pathlib.Path(sys.argv[1]);assert p.is_file() and p.stat().st_size>300
with tarfile.open(p,'r:gz') as archive:
 paths={archive.extractfile(x).read().decode().strip()
        for x in archive.getmembers() if x.name.endswith('/pathname')}
expected={'Assets/HPRPlayerReferenceProbe/Runtime/HprPlayerReferenceProbe.cs',
          'Assets/HPRPlayerReferenceProbe/Editor/HprPlayerReferenceProbeWindow.cs'}
assert expected.issubset(paths),(expected-paths)
assert not any('ProbeQa' in x or '/qa/' in x for x in paths)
print('HPR_PLAYER_REFERENCE_ORIGINAL_SOURCE_ARCHIVE_PASS',len(paths),'first_party_paths')
PYARCHIVE
run create-buyer -createProject "$buyer"
run buyer-original-package-import -projectPath "$buyer" -importPackage "$HPR_PLAYER_PROBE_PACKAGE"
mkdir -p "$buyer/Assets/HPRPrivateQa" "$buyer/Assets/Editor"
cp "$qa/HprProbeQaItem.cs" "$qa/HprProbeQaAutoExit.cs" "$qa/HprProbeQaPlayerOnlyClear.cs" \
 "$qa/HprProbeQaManualTrigger.cs" "$buyer/Assets/HPRPrivateQa/"
cp "$qa/HprProbeQaBuild.cs" "$buyer/Assets/Editor/"
export HPR_PROBE_QA_ROOT="$work"
run original-editor-and-actual-player-build -projectPath "$buyer" -executeMethod HprProbeQaBuild.Run
grep -q HPR_PLAYER_REFERENCE_EDITOR_BASELINE_NATIVE_PASS "$work/original-editor-and-actual-player-build.unity.log"
grep -q HPR_PLAYER_REFERENCE_ACTUAL_LINUX64_BUILT_PASS "$work/original-editor-and-actual-player-build.unity.log"
player="$work/PlayerSmoke.x86_64"
[[ -s "$player" && -s "$work/editor-original-baseline.json" ]] || exit 6
chmod u+x "$player"
mkdir -p "$work/private-player-home/.config" "$work/private-player-config"
echo 'HPR_PLAYER_REFERENCE_REAL_STAGE actual-Linux64-binary-run'
(timeout 120 env HOME="$work/private-player-home" XDG_CONFIG_HOME="$work/private-player-config" \
 "$player" -batchmode -nographics -logFile "$work/actual-built-player.log" \
 >"$work/actual-built-player.stdout" 2>&1) || {
 cat "$work/actual-built-player.stdout"|tail -50 >&2 || true;
 grep -E 'HPR_PLAYER|Exception|ERROR' "$work/actual-built-player.log"|tail -40 >&2 || true;
 exit 7;
}
python3 "$qa/verify_real_player_receipt.py" \
 "$work/actual-built-player.log" "$work/editor-original-baseline.json" \
 "$work/actual-player-receipt.json" > "$work/independent-real-player-verification.json"
cp "$qa/HprProbeQaCompare.cs" "$buyer/Assets/Editor/"
run genuine-Csharp-compare -projectPath "$buyer" -executeMethod HprProbeQaCompare.Run
grep -q HPR_PLAYER_REFERENCE_REAL_EDITOR_VS_BUILT_PLAYER_NATIVE_PASS "$work/genuine-Csharp-compare.unity.log"
[[ -s "$work/actual-editor-versus-player-comparison.json" ]] || exit 8
python3 - "$work" <<'PYCOMPLETE'
from pathlib import Path
import sys,json
p=Path(sys.argv[1]);obj=json.loads((p/'actual-editor-versus-player-comparison.json').read_text())
assert obj['schema']==1 and obj['status']=='CONSISTENT_NULL_OR_UNSET_FIELDS'
assert obj['checkedCount']==3 and not obj['playerMissingCaseIds'] and not obj['otherDifferences']
print('HPR_PLAYER_REFERENCE_TRUE_BUILT_LINUX_PLAYER_AND_NATIVE_EDITOR_COMPARISON_PASS',obj['status'])
PYCOMPLETE
