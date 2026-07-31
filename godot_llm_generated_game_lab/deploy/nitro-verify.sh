#!/usr/bin/env bash
set -euo pipefail
ROOT=/data/src/github/games/godot_llm_generated_game_lab
PUBLIC=https://nitro.jonnyontherun.org/llm_game
ENGINE=sdxl-reviewed-scene-assets+stableanimator-pose-driven-player+rvm-recurrent-soft-alpha
[[ $(hostname -s) == nitro ]]
cd "$ROOT"
systemctl is-active --quiet apache2
systemctl is-active --quiet llm-game-objects.service
apache2ctl configtest >/dev/null
/data/venv/bin/python3 - <<'PY'
import json
from pathlib import Path
from PIL import Image,ImageSequence
root=Path('/data/src/github/games/godot_llm_generated_game_lab')
manifest=json.loads((root/'data/generated_world.json').read_text())
assert manifest['version']==1 and manifest['complete'] is True and manifest['fallback_used'] is False
assert manifest['asset_engine']=='sdxl-reviewed-scene-assets+stableanimator-pose-driven-player+rvm-recurrent-soft-alpha'
assert manifest['gameplay_action_count']==30
assert manifest['scene_plan']['scene_name']=='Dining Room'
assert len(manifest['scene_plan']['player']['actions'])==3
assert all(len(obj['actions'])==3 for obj in manifest['scene_plan']['objects'])
assert len(manifest['assets'])==10
player=manifest['assets']['player']
assert player['pose_driven'] is True and player['engine'] == 'StableAnimator' and player['fallback_used'] is False
assert player['alpha_model'] == 'RobustVideoMatting mobilenetv3 official v1.0.0'
assert player['alpha_temporal_model'] is True
assert player['alpha_resize'] == 'premultiplied-alpha Lanczos4'
assert set(player['clips'])=={'idle','walk','player_interact','player_attack','player_use'}
for name,clip in player['clips'].items():
    assert clip['pose_driven'] is True and clip['engine'] == 'StableAnimator' and clip['fallback_used'] is False
    expected_gif_frames=clip['frame_count']-(1 if name in {'idle','walk'} else 0)
    assert clip['review_pass'] is True and clip['gif_frame_count']==expected_gif_frames and clip['distinct_gif_frames']==expected_gif_frames
    assert clip['gif_looped'] is (name in {'idle','walk'}) and clip['gif_duplicate_closure_frame'] is False
    assert clip['gif_palette_mode']=='single shared 254-color palette; index 0 transparent'
    assert len(clip['gif_frame_durations_ms'])==expected_gif_frames and set(clip['gif_frame_durations_ms'])=={120,130}
    assert sum(clip['gif_frame_durations_ms'])==expected_gif_frames*clip['frame_duration_ms']==clip['gif_total_duration_ms']
    assert clip['min_reference_cosine'] >= 0.60
    assert clip['min_adjacent_identity_cosine'] >= 0.94
    assert clip['max_foreground_coverage'] <= 0.65
    assert clip['max_border_visible_ratio'] == 0.0
    assert clip['alpha_model'] == 'RobustVideoMatting mobilenetv3 official v1.0.0'
    assert clip['alpha_temporal_model'] is True
    assert clip['min_soft_alpha_ratio'] >= 0.005
    assert clip['min_largest_component_ratio'] >= 0.98
    assert max(clip['gif_sheet_mask_disagreement']) <= 0.01
    assert clip['alpha_resize'] == 'premultiplied-alpha Lanczos4'
    assert clip['pose_driver'].startswith('explicit-openpose-')
    with Image.open(root/clip['gif_path']) as image:
        looped=image.info.get('loop')==0
        durations=[];palette_tables=[]
        for index in range(image.n_frames):
            image.seek(index);durations.append(image.info.get('duration'))
            palette=image.getpalette()
            if palette:palette_tables.append(tuple(palette))
        assert image.n_frames==clip['gif_frame_count'] and looped is clip['gif_looped']
        assert durations==clip['gif_frame_durations_ms']
        assert len(palette_tables)==1 and len(set(palette_tables))==1
assert player['clips']['walk']['semantic_motion']['semantic_pass'] is True
assert player['clips']['walk']['semantic_motion']['body_joints_detected_each_frame'] == 17
assert player['clips']['walk']['semantic_motion']['ankle_separation_range'] >= 0.4
print(json.dumps({'manifest':'ok','engine':manifest['asset_engine'],'actions':manifest['gameplay_action_count'],'clips':list(player['clips'])}))
PY
/data/venv/bin/python3 tests/test_temporal_player_clips.py
/data/venv/bin/python3 tests/test_scene_recognizability_evidence.py
/data/venv/bin/python3 tests/test_generated_action_runtime.py
parse_log=$(mktemp)
trap 'rm -f "$parse_log"' EXIT
godot --headless --path . --editor --quit 2>&1 | tee "$parse_log" >/dev/null
! grep -Eq 'SCRIPT ERROR|Parse Error|Failed to load script' "$parse_log"
runtime_log=$(mktemp)
timeout 30 godot --headless --path . --quit-after 20 2>&1 | tee "$runtime_log" >/dev/null
! grep -Eq 'SCRIPT ERROR|Parse Error|ERROR:|Invalid|Missing generated|Generated world manifest is missing' "$runtime_log"
rm -f "$runtime_log"
for base in http://127.0.0.1/llm_game "$PUBLIC"; do
    curl -fsS --max-time 30 "$base/" -o /tmp/temporal-index.html
    grep -q 'id="canvas"' /tmp/temporal-index.html
    curl -fsS --max-time 60 "$base/index.pck" -o /tmp/temporal-index.pck
    curl -fsS --max-time 90 "$base/index.wasm" -o /tmp/temporal-index.wasm
    curl -fsS --max-time 30 "$base/generated_assets/manifest.json" -o /tmp/temporal-public.json
    /data/venv/bin/python3 - <<'PY'
import json
v=json.load(open('/tmp/temporal-public.json')); player=v['assets']['player']
assert v['complete'] is True and v['fallback_used'] is False
assert v['asset_engine']=='sdxl-reviewed-scene-assets+stableanimator-pose-driven-player+rvm-recurrent-soft-alpha'
assert v['scene_name']=='Dining Room' and v['gameplay_action_count']==30 and len(v['assets'])==10
assert set(player['clips'])=={'idle','walk','player_interact','player_attack','player_use'}
assert all(c['pose_driven'] is True and c['engine'] == 'StableAnimator' and c['fallback_used'] is False and c['review_pass'] is True and c['distinct_gif_frames'] == c['frames'] and c['runtime_frames'] == c['frames'] + (1 if name in {'idle','walk'} else 0) and c['looping'] is (name in {'idle','walk'}) and c['duplicate_closure_frame'] is False and c['palette_mode'] == 'single shared 254-color palette; index 0 transparent' and len(c['frame_durations_ms']) == c['frames'] and set(c['frame_durations_ms']) == {120,130} and sum(c['frame_durations_ms']) == c['total_duration_ms'] == c['frames'] * c['duration_ms'] and c['max_foreground_coverage'] <= 0.65 and c['max_border_visible_ratio'] == 0.0 and c['alpha_model'] == 'RobustVideoMatting mobilenetv3 official v1.0.0' and c['alpha_temporal_model'] is True and c['min_soft_alpha_ratio'] >= 0.005 and c['min_largest_component_ratio'] >= 0.98 and max(c['gif_sheet_mask_disagreement']) <= 0.01 for name,c in player['clips'].items())
assert player['clips']['walk']['semantic_motion']['semantic_pass'] is True
review=v['scene_review']
expected={'player','mother','dining_table','chandelier','sideboard','curtains','wall_surface','carpet','kitchen_door','cookies'}
assert set(review['recognizability'])==expected
assert all(item['visible'] is True and item['recognizable'] is True and item['confidence']>=0.7 for item in review['recognizability'].values())
for key in ['large_white_bars','rectangular_source_backgrounds','character_halos','severe_overlap','objects_too_small']:
    assert review['defects'][key] is False,key
assert review['defects']['scene_coherent'] is True
assert review['defects']['player_complete'] is True and review['defects']['mother_complete'] is True
matte=review['player_matte_review']
assert matte['complete_head'] and matte['complete_hands'] and matte['complete_feet']
for key in ['white_halo','dark_halo','uniform_rectangular_background','visible_box_boundary','background_contamination']:
    assert matte[key] is False,key
assert matte['edge_quality']=='clean' and matte['confidence_percent']>=70 and matte['pass'] is True
assert review['player_boundary_metrics']['rectangular_matte_boundary_detected'] is False
assert review['player_boundary_metrics']['fraction_gt_20'] < 0.35
assert review['rvm_contact_review']['overall_pass'] is True
for key in ['white_fringes','dark_fringes','missing_body_parts','background_rectangles','edge_flicker_visible']:
    assert review['rvm_contact_review'][key] is False,key
PY
done
cmp web/index.pck /tmp/temporal-index.pck
cmp web/index.wasm /tmp/temporal-index.wasm
curl -fsSI --max-time 15 "$PUBLIC/" -o /tmp/temporal-public-head.txt
grep -qi 'cross-origin-opener-policy: same-origin' /tmp/temporal-public-head.txt
grep -qi 'cross-origin-embedder-policy: require-corp' /tmp/temporal-public-head.txt
grep -qi 'cross-origin-resource-policy: same-origin' /tmp/temporal-public-head.txt
for clip in idle walk player_interact player_attack player_use; do
    curl -fsSI --max-time 20 "$PUBLIC/generated_assets/player-clips/$clip/animation.gif" -o "/tmp/temporal-$clip-head.txt"
    grep -qi 'content-type: image/gif' "/tmp/temporal-$clip-head.txt"
    curl -fsS --max-time 30 -H 'Cache-Control: no-cache' "$PUBLIC/generated_assets/player-clips/$clip/animation.gif?verify=$(date +%s%N)" -o "/tmp/temporal-$clip.gif"
    CLIP="$clip" /data/venv/bin/python3 - <<'PY_GIF'
import json,os
from pathlib import Path
from PIL import Image
clip_name=os.environ['CLIP']
manifest=json.load(open('/tmp/temporal-public.json'))['assets']['player']['clips'][clip_name]
path=Path('/tmp')/f'temporal-{clip_name}.gif'
with Image.open(path) as image:
    durations=[];palette_tables=[]
    for index in range(image.n_frames):
        image.seek(index);durations.append(image.info.get('duration'))
        palette=image.getpalette()
        if palette:palette_tables.append(tuple(palette))
    assert image.n_frames==manifest['frames']
    assert (image.info.get('loop')==0) is manifest['looping']
    assert durations==manifest['frame_durations_ms']
    assert len(palette_tables)==1 and len(set(palette_tables))==1
PY_GIF
done
profile=$(mktemp -d /data/tmp/firefox-temporal-verify.XXXXXX)
firefox_log=$(mktemp /data/tmp/firefox-temporal-verify-log.XXXXXX)
firefox_port=$(python3 - <<'PY_PORT'
import socket
with socket.socket() as sock:
    sock.bind(('127.0.0.1',0)); print(sock.getsockname()[1])
PY_PORT
)
cat > "$profile/user.js" <<'EOF'
user_pref("webgl.disabled", false);
user_pref("webgl.force-enabled", true);
user_pref("webgl.enable-webgl2", true);
user_pref("gfx.webrender.software", true);
user_pref("gfx.webrender.all", true);
user_pref("layers.acceleration.force-enabled", true);
user_pref("remote.active-protocols", 1);
user_pref("browser.shell.checkDefaultBrowser", false);
user_pref("browser.startup.homepage_override.mstone", "ignore");
user_pref("datareporting.policy.dataSubmissionEnabled", false);
EOF
xvfb-run -a -s '-screen 0 1280x900x24 +extension GLX +render -noreset' env LIBGL_ALWAYS_SOFTWARE=1 MOZ_WEBRENDER=1 firefox --no-remote --profile "$profile" --remote-debugging-port "$firefox_port" "$PUBLIC/" >"$firefox_log" 2>&1 &
firefox_pid=$!
cleanup_browser(){ pkill -TERM -P "$firefox_pid" 2>/dev/null || true; sleep 1; pkill -KILL -P "$firefox_pid" 2>/dev/null || true; kill "$firefox_pid" 2>/dev/null || true; wait "$firefox_pid" 2>/dev/null || true; rm -rf "$profile" "$firefox_log"; }
trap cleanup_browser EXIT
for _ in $(seq 1 40); do grep -q 'WebDriver BiDi listening' "$firefox_log" && break; sleep 1; done
grep -q 'WebDriver BiDi listening' "$firefox_log"
NO_PROXY=127.0.0.1,localhost no_proxy=127.0.0.1,localhost /data/venv/bin/python3 tests/verify_temporal_public_browser.py --websocket "ws://127.0.0.1:$firefox_port/session" --screenshot /data/tmp/your-mom-temporal-public.png
! grep -Eq 'Failed to create WebGL context|SCRIPT ERROR|Parse Error|Failed to load script|Generated world manifest is missing' "$firefox_log"
/data/venv/bin/python3 tests/verify_gif_inspector_public.py --base "$PUBLIC/gif_inspector/"
NO_PROXY=127.0.0.1,localhost no_proxy=127.0.0.1,localhost /data/venv/bin/python3 tests/verify_gif_inspector_browser.py --url "$PUBLIC/gif_inspector/"
printf 'verification=ok route=%s engine=%s actions=30 clips=5 browser=firefox_webgl time=%s\n' "$PUBLIC/" "$ENGINE" "$(date -Is)"
