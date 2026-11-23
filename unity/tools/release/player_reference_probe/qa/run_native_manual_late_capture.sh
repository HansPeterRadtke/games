#!/usr/bin/env bash
# Preserves original author archive, no duplicate author/export effect; new buyer only.
set -euo pipefail
origin=${1:?existing immutable original author test label}
caseid=${2:?fresh independent consumer test label}
[[ "$origin" =~ ^[a-z0-9_-]{4,30}$ && "$caseid" =~ ^[a-z0-9_-]{4,30}$ ]] ||exit 2
root=/data/var/marketplace-account-setup/unity-player-reference-probe-20261123-wave63
archive="$root/$origin/HPR_Player_Reference_Probe_original.unitypackage"
work="$root/$caseid"
qa=$(cd "$(dirname "$0")" && pwd)
unity=/data/apps/Unity/Hub/Editor/6000.6.8f1/Editor/Unity
[[ -x "$unity" && -s "$archive" && ! -e "$work" ]] ||{
 echo 'Missing original package or new buyer label already used' >&2;exit 3;
}
mkdir -p "$work"
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
run(){ name=$1;shift;echo "HPR_PLAYER_REFERENCE_MANUAL_LATE_BUYER_STAGE $name";
 timeout 700 "$unity" -batchmode -nographics -quit "$@" -logFile "$work/$name.unity.log" \
 >"$work/$name.stdout" 2>&1 || {
  grep -E 'HPR_PLAYER|error CS[0-9]|Exception|BuildFailed' "$work/$name.unity.log"|tail -30 >&2||true;exit 5;
 }
}
buyer="$work/independent-buyer-project"
run create-buyer -createProject "$buyer"
run original-product-package-import -projectPath "$buyer" -importPackage "$archive"
mkdir -p "$buyer/Assets/HPRPrivateQa" "$buyer/Assets/Editor"
cp "$qa/HprProbeQaItem.cs" "$qa/HprProbeQaAutoExit.cs" "$qa/HprProbeQaPlayerOnlyClear.cs" "$qa/HprProbeQaManualTrigger.cs" "$buyer/Assets/HPRPrivateQa/"
cp "$qa/HprProbeQaBuild.cs" "$buyer/Assets/Editor/"
export HPR_PROBE_QA_ROOT="$work" HPR_PROBE_QA_MANUAL_LATE=1
run editor-baseline-and-actual-Linux64-build -projectPath "$buyer" -executeMethod HprProbeQaBuild.Run
grep -q HPR_PROBE_QA_RELOADED_EDITOR_FIELDS "$work/editor-baseline-and-actual-Linux64-build.unity.log"
grep -q HPR_PLAYER_REFERENCE_ACTUAL_LINUX64_BUILT_PASS "$work/editor-baseline-and-actual-Linux64-build.unity.log"
player="$work/PlayerSmoke.x86_64"
[[ -s "$player" && -s "$work/editor-original-baseline.json" ]] || exit 6
chmod u+x "$player"
mkdir -p "$work/private-player-home/.config" "$work/private-player-config"
echo 'HPR_PLAYER_REFERENCE_MANUAL_LATE_BUYER_STAGE real_binary_execution'
(timeout 150 env HOME="$work/private-player-home" XDG_CONFIG_HOME="$work/private-player-config" \
 "$player" -batchmode -nographics -logFile "$work/actual-built-player.log" \
 >"$work/actual-built-player.stdout" 2>&1) || {
 cat "$work/actual-built-player.stdout"|tail -45 >&2||true;exit 7;
}
grep -q HPR_PRIVATE_MANUAL_LATE_QA_CAPTURE_SUCCESS "$work/actual-built-player.log"
grep -q HPR_PRIVATE_MANUAL_LATE_QA_CAPTURE_LIMIT_ENFORCED "$work/actual-built-player.log"
python3 "$qa/verify_real_player_receipt.py" \
 "$work/actual-built-player.log" "$work/editor-original-baseline.json" \
 "$work/actual-player-receipt.json" --expect-manual-late-loss >"$work/independent-real-player-verification.json"
cp "$qa/HprProbeQaCompareLoss.cs" "$buyer/Assets/Editor/"
run original-native-Csharp-comparison -projectPath "$buyer" -executeMethod HprProbeQaCompareLoss.Run
grep -q HPR_PLAYER_REFERENCE_REAL_PLAYER_LOSS_NEGATIVE_NATIVE_PASS "$work/original-native-Csharp-comparison.unity.log"
python3 - "$work" <<'PYRESULT'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]);r=json.loads((p/'real-player-reference-loss-comparison.json').read_text())
assert r['schema']==1 and r['status']=='PLAYER_REFERENCE_LOSS_REPRODUCED'
assert r['checkedCount']==3 and r['playerMissingCaseIds']==['assigned-prefab'] and not r['otherDifferences']
print('HPR_PLAYER_REFERENCE_REAL_LATE_MANUAL_PLAYER_NEGATIVE_REPRODUCED',r['status'])
PYRESULT
