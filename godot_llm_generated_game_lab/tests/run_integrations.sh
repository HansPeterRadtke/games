#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
curl -fsS --max-time 5 http://127.0.0.1:14829/health >/dev/null
curl -fsS --max-time 10 http://127.0.0.1:15303/object/health | grep -q 'generated-game-objects'
curl -fsS --max-time 10 http://127.0.0.1:15303/object/rpg/contracts | grep -q 'player'
curl -fsS --max-time 15 http://10.8.0.7:14829/health >/dev/null
curl -fsS --max-time 15 http://10.8.0.7:15310/health | grep -q 'sdxl-base-canonical+sdxl-img2img-animation'
PLAYER_SLUG=$(python3 -c 'import json; print(json.load(open("data/rpg_content.json"))["player"]["slug"])')
curl -fsS --max-time 15 "http://127.0.0.1:15303/object/rpg/status/$PLAYER_SLUG" | grep -q '"status": "ready"'
printf 'integrations=ok player_slug=%s\n' "$PLAYER_SLUG"
