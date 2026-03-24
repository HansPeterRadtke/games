#!/usr/bin/env bash
set -euo pipefail
cd /data/src/github/games
exec /data/venv/bin/python /data/src/github/games/unity/tools/assetstore/queue_native_downloads.py \
  --skip-existing \
  --continue-on-error \
  --poll-interval 20 \
  --timeout 3600 \
  --package-ids 330002,151980,258782,71426,124055,107224,326131,181470,157920,288783,52977,138810,279940,48529,213197,267961
