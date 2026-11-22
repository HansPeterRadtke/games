#!/usr/bin/env bash
set -euo pipefail
base=/data/var/marketplace-account-setup/unity-20261122-wave55
source=/data/src/worktrees/unity-package-boundary-audit-20261121/unity/tools/release/animation_import_preflight_bundle/qa/HprOriginalScenePreviewCapture.cs
version=${1:?Installed supported Unity Editor version}
label=${2:?Exact fresh combined product native QA label}
[[ "$version" = 2022.3.22f1 || "$version" = 6000.6.8f1 ]] || exit 2
[[ "$label" =~ ^[a-z0-9_-]{2,30}$ ]] || exit 2
key=${version//./-}-$label
project=$base/combined-animation-native-$key/independent-buyer-project
unity=/data/apps/Unity/Hub/Editor/$version/Editor/Unity
out=$base/verified-real-unity-buyer-scene-preview-$key.png
log=$base/verified-real-unity-buyer-scene-preview-$key.unity.log
virtual_log=$base/verified-real-unity-buyer-scene-preview-$key.xvfb.log
[[ -x "$unity" && -s "$source" && -d "$project/Assets/HPRFbxSourceTakes" && ! -e "$out" && ! -e "$log" ]] || exit 3
# Must use a dedicated display, never owner desktop X:1.
display=129
[[ ! -e /tmp/.X11-unix/X${display} ]] || { echo 'Display number occupied';exit 4; }
target="$project/Assets/Editor/HprOriginalScenePreviewCapture.cs"
[[ ! -e "$target" ]] || exit 5
cp -- "$source" "$target"
Xvfb :${display} -screen 0 1440x900x24 -nolisten tcp > "$virtual_log" 2>&1 &
virtual_pid=$!
trap 'kill "$virtual_pid" 2>/dev/null || true' EXIT
for i in $(seq 1 30); do [[ -S /tmp/.X11-unix/X${display} ]] && break;sleep .2; done
[[ -S /tmp/.X11-unix/X${display} ]] || { echo 'Isolated Xvfb server did not start';exit 6; }
export DISPLAY=:${display}
export LIBGL_ALWAYS_SOFTWARE=1
export HPR_ORIGINAL_SCENE_PREVIEW_OUT="$out"
export HOME=/home/hans USER=hans LOGNAME=hans XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
export DBUS_SESSION_BUS_ADDRESS=${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/1000/bus}
echo 'Isolated first-party actual Unity camera rendering, NOT an EditorWindow screenshot'
timeout 240 "$unity" -batchmode -force-glcore -quit -projectPath "$project" \
 -executeMethod HprOriginalScenePreviewCapture.Run -logFile "$log" \
 > "$base/verified-real-unity-buyer-scene-preview-$key.stdout" 2>&1 || {
 grep -E -C2 'error CS|Exception|HPR_ORIGINAL|OpenGL|graphics' "$log" | tail -45 >&2 || true
 exit 7
}
grep -q 'HPR_ORIGINAL_UNITY_SCENE_CAPTURE_PASS' "$log"
[[ -s "$out" ]] || exit 8
python3 - "$out" <<'PY'
import sys
from PIL import Image,ImageStat
p=sys.argv[1]
i=Image.open(p).convert('RGB')
assert i.size==(1440,900)
print('UNALTERED_REAL_UNITY_SCENE_PNG',p,'size',i.size,'bytes',__import__('os').path.getsize(p),'extrema',i.getextrema())
PY
