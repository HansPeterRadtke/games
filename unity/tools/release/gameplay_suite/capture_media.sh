#!/usr/bin/env bash
# Renders the genuine Unity imported demo scene; no AI-generated product art.
set -euo pipefail
src_dir=$(cd -- "$(dirname -- "$BASH_SOURCE")" && pwd)
unity=/data/apps/Unity/Hub/Editor/6000.4.0f1/Editor/Unity
release=${HPR_SUITE_RELEASE_ROOT:-/data/var/marketplace-account-setup/unity-consolidated-20261031-v4/release}
project=${HPR_SUITE_CLEANROOM_PROJECT:-/data/tmp/hpr_gameplay_suite_cleanroom_20261031_v4}
test -d "$project/Assets/HPRGameplaySuite" || { echo 'Requires actual cleanroom import' >&2; exit 3; }
mkdir -p "$project/Assets/Editor" "$release/media"
cp "$src_dir/qa/HprGameplaySuiteMediaCapture.cs" "$project/Assets/Editor/"
export HOME=/home/hans USER=hans LOGNAME=hans DISPLAY=:1
export XAUTHORITY=/home/hans/.Xauthority XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export HPR_SUITE_MEDIA_DIR="$release/media"
timeout 420 "$unity" -batchmode -quit -projectPath "$project" -executeMethod HprGameplaySuiteMediaCapture.Run -logFile "$release/media-capture.unity.log" >/dev/null 2>&1
python3 - "$release/media" <<'PY'
from pathlib import Path
from PIL import Image, ImageStat
import sys
root=Path(sys.argv[1])
for name in ("01-arena-actual-unity-camera.png", "02-encounter-actual-unity-camera.png"):
    file=root/name
    assert file.is_file() and file.stat().st_size>20000
    im=Image.open(file).convert("RGB")
    assert im.size==(1600,900)
    assert min(ImageStat.Stat(im).stddev)>2
    print("REAL_UNITY_CAMERA_PNG_VERIFIED",file,file.stat().st_size)
PY
