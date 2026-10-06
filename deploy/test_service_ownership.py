#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
assert (ROOT/'LLM_Game/deploy/llm-game-stt.service').is_file()
assert (ROOT/'godot_llm_generated_game_lab/deploy/llm-game-objects.service').is_file()
assert (ROOT/'deploy/thor/llm-game-image.service').is_file()
assert (ROOT/'deploy/thor/llm-game-world-small.service').is_file()
installer=(ROOT/'deploy/thor/install-thor.sh').read_text()
assert '/data/infra' not in installer
assert 'llm-game-image.service' in installer
assert 'llm-game-world-small.service' in installer
print('game_service_ownership ok')
