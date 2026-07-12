#!/usr/bin/env bash
set -euo pipefail
DATA=/data
APP=$DATA/src/github/games/LLM_Game
PY=$DATA/venv/bin/python3
CFG=$DATA/infra/libexec/config_value.py
WS_PORT=$($PY "$CFG" port "$DATA" llm_game 0)
HTTP_PORT=$($PY "$CFG" port "$DATA" llm_game 1)
[[ $(hostname -s) == nitro ]]
systemctl is-active --quiet llm-game-stt.service
apache2ctl configtest >/dev/null
curl -fsS --max-time 5 "http://127.0.0.1:$HTTP_PORT/http/health" >/dev/null
curl -fsS --max-time 5 http://127.0.0.1/llm_game_stt/http/health >/dev/null
curl -fsS --max-time 15 https://nitro.jonnyontherun.org/llm_game/ | grep -q '20260712-voice-recovery-v1'
"$PY" "$APP/tests/stt_ws_smoke.py" --url ws://127.0.0.1/llm_game_stt/ws/ --timeout 10
"$PY" "$APP/tests/stt_ws_smoke.py" --url wss://nitro.jonnyontherun.org/llm_game_stt/ws/ --timeout 15
printf 'verification=ok machine=%s ws_port=%s http_port=%s time=%s\n' "$(hostname)" "$WS_PORT" "$HTTP_PORT" "$(date -Is)"
