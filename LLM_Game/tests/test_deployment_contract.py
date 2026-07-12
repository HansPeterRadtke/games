#!/usr/bin/env python3
import json
from pathlib import Path
APP=Path(__file__).resolve().parents[1]
INFRA=Path('/data/infra')
ports=json.loads((INFRA/'etc/ports.json').read_text())['services']
assert ports['llm_game']['base']==15301, ports.get('llm_game')
assert (INFRA/'etc/systemd/system/llm-game-stt.service').is_file()
assert (INFRA/'hosts/nitro/etc/apache2/conf-available/llm-game.conf.in').is_file()
assert (INFRA/'hosts/nitro/bin-impl/install_llm_game.sh').is_file()
unit=(INFRA/'etc/systemd/system/llm-game-stt.service').read_text()
assert 'HF_HOME=/data/var/llm_game/cache/huggingface' in unit
assert 'XDG_CACHE_HOME=/data/var/llm_game/cache' in unit
source=(APP/'web/app.js').read_text()
assert 'wss://nitro.jonnyontherun.org/llm_game_stt' not in source
assert 'location.host' in source
assert 'wh-ch710n' not in source.lower()
assert 'bluetooth' not in source.lower()
assert 'browserSttLanguage' in source
assert 'stt_processing' in source
print('deployment_contract ok')
