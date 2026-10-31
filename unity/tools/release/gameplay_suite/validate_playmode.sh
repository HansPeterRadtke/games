#!/usr/bin/env bash
# Independent real Play Mode QA in freshly imported Unity project.
# No publishing, no networking, no mutations to original source.
set -euo pipefail
src=$(cd -- "$(dirname -- "$BASH_SOURCE")" && pwd)
unity=/data/apps/Unity/Hub/Editor/6000.4.0f1/Editor/Unity
release=/data/var/marketplace-account-setup/unity-consolidated-20261031-v4/release
project=/data/tmp/hpr_gameplay_suite_cleanroom_20261031_v4
test -f "$project/Assets/HPRGameplaySuite/Demo/GameplaySuiteShowcase.unity" || {
    echo 'Independent buyer archive must be imported first' >&2; exit 3;
}
mkdir -p "$project/Assets/Editor"
cp "$src/qa/HprGameplaySuitePlaymodeValidator.cs" "$project/Assets/Editor/"
export HOME=/home/hans USER=hans LOGNAME=hans DISPLAY=:1
export XAUTHORITY=/home/hans/.Xauthority XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export HPR_SUITE_PLAYMODE_RECEIPT="$release/actual-playmode-receipt.txt"
test ! -e "$HPR_SUITE_PLAYMODE_RECEIPT" || { echo 'Refusing to reuse playmode receipt' >&2; exit 4; }
timeout 420 "$unity" -batchmode -projectPath "$project" -executeMethod HprGameplaySuitePlaymodeValidator.Run -logFile "$release/actual-playmode.unity.log" >/dev/null 2>&1
test -s "$HPR_SUITE_PLAYMODE_RECEIPT"
cat "$HPR_SUITE_PLAYMODE_RECEIPT"
