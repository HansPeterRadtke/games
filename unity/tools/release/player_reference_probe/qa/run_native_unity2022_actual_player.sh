#!/usr/bin/env bash
# True Unity 2022 first-party demo Player build in a previously verified
# independent buyer project. Adds only private QA files to that disposable copy.
set -euo pipefail
buyerlabel=${1:?existing unique current original independently installed buyer label}
label=${2:?fresh real Player QA evidence label}
[[ "$buyerlabel" =~ ^[a-z0-9_-]{4,30}$ && "$label" =~ ^[a-z0-9_-]{4,30}$ ]] ||exit 2
root=/data/var/marketplace-account-setup/unity-player-reference-probe-20261123-wave63
buyer="$root/$buyerlabel/2022-3-22f1-independent-buyer"
work="$root/$label"
qa=$(cd "$(dirname "$0")" && pwd)
unity=/data/apps/Unity/Hub/Editor/2022.3.22f1/Editor/Unity
[[ -x "$unity" && -f "$buyer/Assets/HPRPlayerReferenceProbe/Runtime/HprPlayerReferenceProbe.cs" &&
    -f "$root/$buyerlabel/2022-3-22f1-qa/actual-original-demo-editor-baseline.json" &&
    ! -e "$work" && ! -e "$buyer/Assets/Editor/HprProbeQa2022ActualPlayer.cs" ]] ||{
 echo 'Refusing unavailable original buyer or reused one-off QA evidence' >&2;exit 3;
}
python3 -B "$qa/stage_original_probe_source.py" --verify-existing "$qa/../Assets/HPRPlayerReferenceProbe" "$buyer/Assets"
mkdir -p "$work" "$buyer/Assets/HPRPrivateQa" "$buyer/Assets/Editor"
cp "$qa/HprProbeQaAutoExit.cs" "$buyer/Assets/HPRPrivateQa/"
cp "$qa/HprProbeQa2022ActualPlayer.cs" "$buyer/Assets/Editor/"
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
export HPR_UNITY2022_PLAYER_QA="$work"
echo 'HPR_TRUE_UNITY2022_ORIGINAL_GAME_BUILD_STARTED'
timeout 620 "$unity" -batchmode -nographics -quit -projectPath "$buyer" \
 -executeMethod HprProbeQa2022ActualPlayer.Run \
 -logFile "$work/actual-Unity2022-Player-build.unity.log" \
 > "$work/actual-Unity2022-Player-build.stdout" 2>&1 || {
 grep -E 'HPR_REAL_UNITY2022|error CS[0-9]|Exception' "$work/actual-Unity2022-Player-build.unity.log"|tail -25 >&2||true;exit 5;
}
grep -q HPR_REAL_UNITY2022_BUILT_PLAYER_PASS "$work/actual-Unity2022-Player-build.unity.log"
exe="$work/PrivateOriginalDemo2022.x86_64"
[[ -s "$exe" && -s "$work/private-Editor2022-baseline.json" ]]||exit 6
chmod u+x "$exe"
mkdir -p "$work/private-player-home/.config" "$work/private-player-config"
echo 'HPR_TRUE_UNITY2022_ORIGINAL_PLAYER_EXECUTION_STARTED'
timeout 120 env HOME="$work/private-player-home" XDG_CONFIG_HOME="$work/private-player-config" \
 "$exe" -batchmode -nographics -logFile "$work/actual-Unity2022-Player.log" \
 > "$work/actual-Unity2022-Player.stdout" 2>&1 || {
 tail -25 "$work/actual-Unity2022-Player.stdout" >&2||true;exit 7;
}
python3 "$qa/verify_unity2022_actual_demo_player.py" \
 "$work/actual-Unity2022-Player.log" "$work/private-Editor2022-baseline.json" \
 "$work/verified-original-Unity2022-Player.json" > "$work/independent-runtime-verification.stdout"
cat "$work/independent-runtime-verification.stdout"
printf 'HPR_TRUE_UNITY2022_ORIGINAL_BUILT_PLAYER_PASS\n'
