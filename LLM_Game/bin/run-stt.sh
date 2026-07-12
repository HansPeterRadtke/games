#!/usr/bin/env bash
set -euo pipefail
DATA_ROOT="${INFRA_DATA_ROOT:-/data}"
PYTHON="${LLM_GAME_PYTHON:-$DATA_ROOT/venv/bin/python3}"
CONFIG_VALUE="$DATA_ROOT/infra/libexec/config_value.py"
APP_ROOT="${LLM_GAME_ROOT:-$DATA_ROOT/src/github/games/LLM_Game}"
[[ -x "$PYTHON" ]] || { echo "missing Python: $PYTHON" >&2; exit 1; }
WS_PORT="$($PYTHON "$CONFIG_VALUE" port "$DATA_ROOT" llm_game 0)"
HTTP_PORT="$($PYTHON "$CONFIG_VALUE" port "$DATA_ROOT" llm_game 1)"
mkdir -p "${LLM_GAME_STT_OUT_DIR:-$DATA_ROOT/var/llm_game/stt}" "${LLM_GAME_GIF_DIR:-$DATA_ROOT/var/llm_game/topic_gifs}"
cd "$APP_ROOT"
args=(--host 127.0.0.1 --port "$WS_PORT" --http-port "$HTTP_PORT")
[[ "${LLM_GAME_WARMUP:-1}" == 1 ]] && args+=(--warmup)
exec "$PYTHON" -u server/stt_ws_server.py "${args[@]}"
