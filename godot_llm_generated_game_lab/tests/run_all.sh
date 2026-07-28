#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
/data/venv/bin/python3 -m py_compile tests/test_rpg_assets.py tests/test_rpg_contracts.py tests/test_deployment_contract.py tests/test_web_shell.py tests/test_world_generation_contracts.py server/generated_object_service.py server/rpg_content.py server/world_generation.py
/data/venv/bin/python3 tests/test_rpg_assets.py
/data/venv/bin/python3 tests/test_rpg_contracts.py
/data/venv/bin/python3 tests/test_deployment_contract.py
/data/venv/bin/python3 tests/test_web_shell.py
/data/venv/bin/python3 tests/test_world_generation_contracts.py
LLM_GAME_DISABLE_LIVE_GENERATION=1 godot --headless --path "$ROOT" --editor --quit
LLM_GAME_DISABLE_LIVE_GENERATION=1 godot --headless --path "$ROOT" --script tests/test_project.gd
LLM_GAME_DISABLE_LIVE_GENERATION=1 godot --headless --path "$ROOT" --script tests/test_physics.gd
LLM_GAME_DISABLE_LIVE_GENERATION=1 godot --headless --path "$ROOT" --script tests/test_open_world.gd
LLM_GAME_DISABLE_LIVE_GENERATION=1 godot --headless --path "$ROOT" --script tests/test_web_bridge.gd
LLM_GAME_DISABLE_LIVE_GENERATION=1 godot --headless --path "$ROOT" --script tests/test_player_walk_animation.gd
LLM_GAME_DISABLE_LIVE_GENERATION=1 godot --headless --path "$ROOT" --quit-after 3
/data/venv/bin/python3 tests/test_world_asset_pipeline.py
/data/venv/bin/python3 tests/test_generated_world_contract.py
