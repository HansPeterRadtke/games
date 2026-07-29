#!/usr/bin/env bash
set -euo pipefail
[[ $(id -u) -eq 0 ]] || { echo 'install-nitro.sh must run as root' >&2; exit 1; }
[[ $(hostname -s) == nitro ]] || { echo 'install-nitro.sh is Nitro-only' >&2; exit 1; }
DATA=${INFRA_DATA_ROOT:-/data}
ROOT=$DATA/src/github/games/godot_llm_generated_game_lab
WS_PORT=${LLM_GAME_WS_PORT:-15301}
HTTP_PORT=${LLM_GAME_HTTP_PORT:-15302}
[[ -s "$ROOT/web/index.html" && -s "$ROOT/web/index.wasm" && -s "$ROOT/web/index.pck" ]] || { echo 'run deploy/build-web.sh as hans first' >&2; exit 1; }
systemctl is-active --quiet llm-game-objects.service || { echo 'llm-game-objects.service is not active' >&2; exit 1; }
TS=$(date +%Y%m%dT%H%M%S)
BACKUP=$DATA/var/backups/godot-llm-game-deploy-$TS
REPORT=$DATA/var/llm_game/deploy/godot-install-$TS.txt
TARGET=/etc/apache2/conf-available/llm-game.conf
mkdir -p "$BACKUP" "$(dirname "$REPORT")"
old_config_present=0
if [[ -e "$TARGET" ]]; then
    cp -a "$TARGET" "$BACKUP/llm-game.conf"
    old_config_present=1
fi
rollback() {
    rc=$?
    trap - ERR
    if [[ $old_config_present -eq 1 ]]; then
        cp -a "$BACKUP/llm-game.conf" "$TARGET"
    else
        rm -f "$TARGET"
    fi
    apache2ctl configtest >/dev/null 2>&1 && systemctl reload apache2 >/dev/null 2>&1 || true
    echo "deployment rolled back after error; backup=$BACKUP" >&2
    exit "$rc"
}
trap rollback ERR
rendered=$(mktemp)
trap 'rm -f "$rendered"' RETURN
sed -e "s/@WS_PORT@/$WS_PORT/g" -e "s/@HTTP_PORT@/$HTTP_PORT/g" "$ROOT/deploy/apache.conf.in" > "$rendered"
install -m 0644 "$rendered" "$TARGET"
rm -f "$rendered"
a2enmod alias headers proxy proxy_http proxy_wstunnel >/dev/null
a2enconf llm-game >/dev/null
apache2ctl configtest
systemctl reload apache2
verify_tmp=$(mktemp -d /data/tmp/llm-game-install-verify.XXXXXX)
trap 'rm -rf "$verify_tmp"' RETURN
curl -fsS --max-time 10 http://127.0.0.1/llm_game/ -o "$verify_tmp/index.html"
grep -q 'your-mom-temporal-absolute-paths-v3' "$verify_tmp/index.html"
for token in 'id="hud-panel"' 'id="stage"' 'id="canvas"' 'id="controls-panel"' 'id="touch-controls"' 'id="stick-base"' 'id="action-pad"' 'llmGameGodotMove'; do grep -q "$token" "$verify_tmp/index.html"; done
[[ $(grep -c 'id="canvas"' "$verify_tmp/index.html") -eq 1 ]]
curl -fsSI --max-time 10 http://127.0.0.1/llm_game/index.wasm | grep -qi 'content-type: application/wasm'
curl -fsS --max-time 10 http://127.0.0.1/llm_game_stt/http/health >/dev/null
curl -fsS --max-time 10 http://127.0.0.1/llm_game_object/health -o "$verify_tmp/object-health.json"
grep -q 'generated-game-objects' "$verify_tmp/object-health.json"
PLAYER_SLUG=$(python3 -c 'import json; print(json.load(open("/data/src/github/games/godot_llm_generated_game_lab/data/rpg_content.json"))["player"]["slug"])')
curl -fsSI --max-time 15 "http://127.0.0.1/llm_game_object_asset/$PLAYER_SLUG.sheet.png" | grep -qi 'content-type: image/png'
curl -fsS --max-time 15 http://10.8.0.7:15310/health -o "$verify_tmp/thor-health.json"
grep -q 'sdxl-base-canonical+sdxl-img2img-animation' "$verify_tmp/thor-health.json"
trap - ERR
{
    echo machine=$(hostname)
    echo installed=$(date -Is)
    echo backup=$BACKUP
    echo route=/llm_game/
    echo static_root=$ROOT/web
    echo ws_port=$WS_PORT
    echo http_port=$HTTP_PORT
    echo object_port=15303
    echo player_slug=$PLAYER_SLUG
    echo grounded_asset_engine=sdxl-base-canonical+sdxl-img2img-animation
    echo web_shell=dom-controls-outside-canvas
    echo apache=ok
} | tee "$REPORT"
ln -sfn "$(basename "$REPORT")" "$DATA/var/llm_game/deploy/latest-godot-install.txt"
