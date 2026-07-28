#!/usr/bin/env bash
set -euo pipefail
ROOT=/data/src/github/games/godot_llm_generated_game_lab
PUBLIC=https://nitro.jonnyontherun.org/llm_game
[[ $(hostname -s) == nitro ]]
cd "$ROOT"
systemctl is-active --quiet apache2
systemctl is-active --quiet llm-game-objects.service
apache2ctl configtest >/dev/null
python3 - <<'PY'
import json
from pathlib import Path
from PIL import Image,ImageSequence
root=Path('/data/src/github/games/godot_llm_generated_game_lab')
manifest=json.loads((root/'data/generated_world.json').read_text())
assert manifest['version']==1
assert manifest['complete'] is True
assert manifest['fallback_used'] is False
assert manifest['asset_engine']=='thor-sdxl-reviewed-identity-anchored-animation'
assert manifest['scene_plan']['scene_name']=='Dining Room'
assert manifest['scene_plan']['visual_generator']=='thor_sdxl'
assert len(manifest['assets'])==10
for asset_id,asset in manifest['assets'].items():
    assert asset['verification']['canonical_pass'] is True
    assert asset['verification']['animation_pass'] is True
    assert asset['identity_anchored'] is True
    assert asset['motion_generated'] is True
    with Image.open(asset['gif_path']) as gif:
        frames=list(ImageSequence.Iterator(gif))
        assert len(frames)==asset['frame_count']
        assert gif.info.get('loop')==0
print(json.dumps({'manifest':'ok','scene':manifest['scene_plan']['scene_name'],'assets':len(manifest['assets']),'fallback':manifest['fallback_used']}))
PY
parse_log=$(mktemp)
trap 'rm -f "$parse_log"' EXIT
godot --headless --path . --editor --quit 2>&1 | tee "$parse_log" >/dev/null
! grep -Eq 'SCRIPT ERROR|Parse Error|Failed to load script' "$parse_log"
runtime_log=$(mktemp)
timeout 30 godot --headless --path . --quit-after 20 2>&1 | tee "$runtime_log" >/dev/null
! grep -Eq 'SCRIPT ERROR|Parse Error|ERROR:|Invalid|Missing generated|Generated world manifest is missing' "$runtime_log"
rm -f "$runtime_log"
for base in http://127.0.0.1/llm_game "$PUBLIC"; do
    curl -fsS --max-time 30 "$base/" -o /tmp/generated-world-index.html
    grep -q 'id="canvas"' /tmp/generated-world-index.html
    curl -fsS --max-time 60 "$base/index.pck" -o /tmp/generated-world-index.pck
    curl -fsS --max-time 90 "$base/index.wasm" -o /tmp/generated-world-index.wasm
    curl -fsS --max-time 30 "$base/generated_assets/manifest.json" -o /tmp/generated-world-public.json
    python3 - <<'PY'
import json
v=json.load(open('/tmp/generated-world-public.json'))
assert v['complete'] is True and v['fallback_used'] is False
assert v['scene_name']=='Dining Room' and len(v['assets'])==10
assert all(a['canonical_pass'] is True and a['animation_pass'] is True for a in v['assets'].values())
PY
done
cmp web/index.pck /tmp/generated-world-index.pck
cmp web/index.wasm /tmp/generated-world-index.wasm
curl -fsSI --max-time 15 "$PUBLIC/" -o /tmp/generated-world-public-head.txt
curl -fsS --max-time 15 "$PUBLIC/" -o /tmp/generated-world-public-index.html
curl -fsSI --max-time 15 "$PUBLIC/index.wasm" -o /tmp/generated-world-wasm-head.txt
curl -fsSI --max-time 15 "$PUBLIC/generated_assets/player.gif" -o /tmp/generated-world-gif-head.txt
grep -qi 'cross-origin-opener-policy: same-origin' /tmp/generated-world-public-head.txt
grep -qi 'cross-origin-embedder-policy: require-corp' /tmp/generated-world-public-head.txt
grep -qi 'cross-origin-resource-policy: same-origin' /tmp/generated-world-public-head.txt
grep -q 'Loading Your Mom — generated entirely by models' /tmp/generated-world-public-index.html
! grep -q 'Loading Grounded Medieval RPG' /tmp/generated-world-public-index.html
grep -qi 'content-type: application/wasm' /tmp/generated-world-wasm-head.txt
grep -qi 'content-type: image/gif' /tmp/generated-world-gif-head.txt
curl -fsS --max-time 15 http://10.8.0.7:14831/health >/dev/null
curl -fsS --max-time 15 http://10.8.0.7:15310/health >/dev/null
profile=$(mktemp -d /data/tmp/firefox-generated-world-verify.XXXXXX)
firefox_log=$(mktemp /data/tmp/firefox-generated-world-verify-log.XXXXXX)
firefox_port=$(python3 - <<'PY_PORT'
import socket
with socket.socket() as sock:
    sock.bind(('127.0.0.1',0))
    print(sock.getsockname()[1])
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
cleanup_browser(){
    pkill -TERM -P "$firefox_pid" 2>/dev/null || true
    sleep 1
    pkill -KILL -P "$firefox_pid" 2>/dev/null || true
    kill "$firefox_pid" 2>/dev/null || true
    wait "$firefox_pid" 2>/dev/null || true
    rm -rf "$profile" "$firefox_log"
}
trap cleanup_browser EXIT
for _ in $(seq 1 30); do grep -q 'WebDriver BiDi listening' "$firefox_log" && break; sleep 1; done
grep -q 'WebDriver BiDi listening' "$firefox_log"
NO_PROXY=127.0.0.1,localhost no_proxy=127.0.0.1,localhost /data/venv/bin/python3 tests/verify_generated_world_browser.py --websocket ws://127.0.0.1:$firefox_port/session --screenshot /data/tmp/generated-world-firefox.png
! grep -Eq 'Failed to create WebGL context|SCRIPT ERROR|Parse Error|Failed to load script|Generated world manifest is missing' "$firefox_log"
printf 'verification=ok route=%s scene=Dining_Room assets=10 browser=firefox_webgl fallback=false time=%s\n' "$PUBLIC/" "$(date -Is)"
