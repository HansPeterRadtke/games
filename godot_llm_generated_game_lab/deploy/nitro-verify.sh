#!/usr/bin/env bash
set -euo pipefail
ROOT=/data/src/github/games/godot_llm_generated_game_lab
PUBLIC=https://nitro.jonnyontherun.org/llm_game
ENGINE=sdxl-reviewed-canonical+ltx-video-temporal+birefnet-matting
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
assert manifest['asset_engine']=='sdxl-reviewed-canonical+ltx-video-temporal+birefnet-matting'
assert manifest['gameplay_action_count']==30
assert manifest['scene_plan']['scene_name']=='Dining Room'
assert len(manifest['scene_plan']['player']['actions'])==3
assert all(len(obj['actions'])==3 for obj in manifest['scene_plan']['objects'])
assert len(manifest['assets'])==10
player=manifest['assets']['player']
assert player['temporal_model'] is True and player['native_video_frames'] is True and player['fallback_used'] is False
assert set(player['clips'])=={'idle','player_interact','player_attack','player_use'}
for name,clip in player['clips'].items():
    assert clip['temporal_model'] is True and clip['native_video_frames'] is True and clip['fallback_used'] is False
    assert clip['review_pass'] is True and clip['distinct_gif_frames']==9 and clip['frame_count']==9
    with Image.open(root/clip['gif_path']) as image:
        frames=list(ImageSequence.Iterator(image))
        assert len(frames)==9 and image.info.get('loop')==0
print(json.dumps({'manifest':'ok','engine':manifest['asset_engine'],'actions':manifest['gameplay_action_count'],'clips':list(player['clips'])}))
PY
/data/venv/bin/python3 tests/test_temporal_player_clips.py
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
assert v['asset_engine']=='sdxl-reviewed-canonical+ltx-video-temporal+birefnet-matting'
assert v['scene_name']=='Dining Room' and v['gameplay_action_count']==30 and len(v['assets'])==10
assert set(player['clips'])=={'idle','player_interact','player_attack','player_use'}
assert all(c['temporal_model'] is True and c['native_video_frames'] is True and c['fallback_used'] is False and c['review_pass'] is True and c['distinct_gif_frames']==9 for c in player['clips'].values())
PY
done
cmp web/index.pck /tmp/temporal-index.pck
cmp web/index.wasm /tmp/temporal-index.wasm
curl -fsSI --max-time 15 "$PUBLIC/" -o /tmp/temporal-public-head.txt
grep -qi 'cross-origin-opener-policy: same-origin' /tmp/temporal-public-head.txt
grep -qi 'cross-origin-embedder-policy: require-corp' /tmp/temporal-public-head.txt
grep -qi 'cross-origin-resource-policy: same-origin' /tmp/temporal-public-head.txt
for clip in idle player_interact player_attack player_use; do
    curl -fsSI --max-time 20 "$PUBLIC/generated_assets/player-clips/$clip/animation.gif" | grep -qi 'content-type: image/gif'
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
printf 'verification=ok route=%s engine=%s actions=30 clips=4 browser=firefox_webgl time=%s\n' "$PUBLIC/" "$ENGINE" "$(date -Is)"
