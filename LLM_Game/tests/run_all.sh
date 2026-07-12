#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
PY=${LLM_GAME_PYTHON:-/data/venv/bin/python3}
cd "$ROOT"
"$PY" -m py_compile server/stt_ws_server.py tests/*.py
node --check web/app.js
"$PY" tests/web_static_check.py
"$PY" tests/test_raw_stt_flow.py
"$PY" tests/test_backend_selection.py
"$PY" tests/test_deployment_contract.py
bash -n bin/run-stt.sh deploy/nitro-verify.sh
git -C "$ROOT/.." diff --check -- LLM_Game
