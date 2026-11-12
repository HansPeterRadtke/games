#!/usr/bin/env bash
# Independent real Play Mode QA in freshly imported Unity project.
# No publishing, no networking, no mutations to original source.
set -euo pipefail
src=$(cd -- "$(dirname -- "$BASH_SOURCE")" && pwd)
unity=${UNITY_BIN:-/data/apps/Unity/Hub/Editor/6000.6.8f1/Editor/Unity}
release=${HPR_SUITE_RELEASE_ROOT:-/data/var/marketplace-account-setup/unity-consolidated-20261031-v2/release}
project=${HPR_SUITE_CLEANROOM_PROJECT:-/data/tmp/hpr_gameplay_suite_cleanroom_20261031_v2}
export HOME=/home/hans USER=hans LOGNAME=hans DISPLAY=:1
export XAUTHORITY=/home/hans/.Xauthority XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
exec python3 "$src/qa/run_verified_playmode.py" --editor "$unity" --release "$release" --project "$project"
