#!/usr/bin/env bash
# Actual rendered Player screenshot, NEVER image generation or a mocked Unity Editor window.
set -euo pipefail
label=${1:?real Unity6 buyer label}
preview=${2:?new evidence label}
[[ "$label" =~ ^[a-z0-9_-]{4,30}$ && "$preview" =~ ^[a-z0-9_-]{4,30}$ ]]||exit 2
root=/data/var/marketplace-account-setup/unity-player-reference-probe-20261123-wave63
buyer="$root/$label/6000-6-8f1-qa"
player="$buyer/OriginalDemoLinux64.x86_64"
out="$root/$label/preview-$preview"
if [[ ! -s "$player" || -e "$out" || -e /tmp/.X11-unix/X146 ]];then
 echo 'Actual first-party Player missing, preview label reused, or virtual display already occupied' >&2;exit 3
fi
mkdir -p "$out" "$out/private-home/.config"
Xvfb :146 -screen 0 1440x900x24 -nolisten tcp >"$out/xvfb.log" 2>&1 & xvfb=$!
app='';wm=''
cleanup(){
 [[ -z "$app" ]] || { kill "$app" 2>/dev/null ||true;wait "$app" 2>/dev/null||true; }
 [[ -z "$wm" ]] || kill "$wm" 2>/dev/null||true
 kill "$xvfb" 2>/dev/null||true
}
trap cleanup EXIT
for i in $(seq 1 60);do [[ -S /tmp/.X11-unix/X146 ]] && break;sleep .2;done
[[ -S /tmp/.X11-unix/X146 ]] || exit 4
export DISPLAY=:146 LIBGL_ALWAYS_SOFTWARE=1
export HOME="$out/private-home" XDG_CONFIG_HOME="$out/private-home/.config"
export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/run/user/1000}
if command -v openbox >/dev/null;then openbox --sm-disable >"$out/window-manager.log" 2>&1 & wm=$!;fi
chmod u+x "$player"
"$player" -force-glcore -screen-fullscreen 0 -screen-width 1280 -screen-height 720 \
 -logFile "$out/actual-original-player.log" >"$out/actual-original-player.stdout" 2>&1 & app=$!
for i in $(seq 1 80);do
 if grep -q 'HPR_PLAYER_REFERENCE_RECEIPT=' "$out/actual-original-player.log" 2>/dev/null;then break;fi
 if ! kill -0 "$app" 2>/dev/null;then
  echo 'Actual sample game closed before displaying a Player reference receipt' >&2;
  tail -20 "$out/actual-original-player.stdout" >&2||true;exit 5
 fi
 sleep 1
done
grep -q 'HPR_PLAYER_REFERENCE_RECEIPT=' "$out/actual-original-player.log" || {
 echo 'Actual sample game did not produce runtime reference evidence' >&2;exit 6;
}
sleep 6
import -display :146 -window root "$out/original-unity-player-demo.png"
[[ -s "$out/original-unity-player-demo.png" ]] ||exit 7
# Keep the unmodified full-screen X capture; this crop is solely a truthful
# rectangular view of the game window, excluding the surrounding Xvfb desktop.
identify "$out/original-unity-player-demo.png" >"$out/original-image-dimensions.txt"
convert "$out/original-unity-player-demo.png" -crop 1280x720+0+0 +repage \
 "$out/actual-native-player-window-crop.png"
convert "$out/actual-native-player-window-crop.png" -resize 900x506 -quality 76 \
 "$out/manual-visual-inspection.jpg"
python3 - "$out" "$buyer/actual-original-demo-editor-baseline.json" <<'PYVERIFY'
from pathlib import Path
import json,sys
p=Path(sys.argv[1]);baseline_path=Path(sys.argv[2]);marker='HPR_PLAYER_REFERENCE_RECEIPT='
lines=[x.partition(marker)[2].strip() for x in (p/'actual-original-player.log').read_text(errors='replace').splitlines() if marker in x]
assert len(lines)==1,('expected one original Player probe receipt',len(lines))
r=json.loads(lines[0])
assert r['schema']==2 and r['origin']=='PLAYER' and r['checkedCount']==2
assert r['assignedCount']==1 and r['missingCount']==1 and r['unsupportedCount']==0
assert [(x['id'],x['sourceLookup'],x['status']) for x in r['cases']]==[
 ('demo-assigned','RESOURCES:HPRSample/AssignedItem','ASSIGNED'),
 ('demo-intentionally-empty','RESOURCES:HPRSample/OptionalItem','REFERENCE_NULL_OR_UNSET')]
assert r['cases'][0]['referencedName']=='HPR_Demo_Reference'
editor=json.loads(baseline_path.read_text())
assert editor['origin']=='EDITOR' and editor['unityVersion']==r['unityVersion']
assert editor['schema']==r['schema'] and editor['checkedCount']==r['checkedCount']
for left,right in zip(editor['cases'],r['cases']):
    for field in ('id','assetName','fieldName','sourceLookup','status','referencedType','referencedName'):
        assert left[field]==right[field],(field,left.get(field),right.get(field))
assert (p/'original-unity-player-demo.png').stat().st_size>30000
assert (p/'actual-native-player-window-crop.png').stat().st_size>30000
with (p/'real-rendered-player-test-evidence.json').open('x') as f:
 json.dump({'original_Unity_version':r['unityVersion'],'original_Player_platform':r['platform'],
            'runtime_reference_receipt':'PASS_ASSIGNED_AND_INTENTIONALLY_EMPTY',
            'actual_3D_Player_screenshot':str(p/'original-unity-player-demo.png'),
            'manual_visual_review':'REQUIRED_NOT_YET_COMPLETE',
            'original_scene_test_only':True,
            'editor_vs_actual_release_player_direct_fields_match':True,
            'external_publication':'NONE'},f,indent=2)
print('HPR_ORIGINAL_REAL_PLAYER_SAMPLE_RENDER_AND_RUNTIME_RECEIPT_PASS')
PYVERIFY
printf 'REAL_RENDERED_SAMPLE_SCREENSHOT_CREATED_WITH_VISUAL_REVIEW_PENDING\n'
