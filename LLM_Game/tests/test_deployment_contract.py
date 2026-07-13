#!/usr/bin/env python3
from pathlib import Path
APP=Path(__file__).resolve().parents[1]
assert (APP/'deploy/llm-game-stt.service').is_file()
assert (APP/'deploy/apache.conf.in').is_file()
assert (APP/'deploy/install-nitro.sh').is_file()
unit=(APP/'deploy/llm-game-stt.service').read_text()
assert 'HF_HOME=/data/var/llm_game/cache/huggingface' in unit
assert 'XDG_CACHE_HOME=/data/var/llm_game/cache' in unit
installer=(APP/'deploy/install-nitro.sh').read_text()
assert 'LLM_GAME_WS_PORT:-15301' in installer
assert 'LLM_GAME_HTTP_PORT:-15302' in installer
assert '/data/infra' not in installer
source=(APP/'web/app.js').read_text()
assert 'wss://nitro.jonnyontherun.org/llm_game_stt' not in source
assert 'location.host' in source
assert 'wh-ch710n' not in source.lower()
assert 'bluetooth' not in source.lower()
assert 'browserSttLanguage' in source
assert 'stt_processing' in source
print('deployment_contract ok')
