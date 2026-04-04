#!/usr/bin/env bash
set -euo pipefail

ROOT=/data/src/github/games
RUNNER=$ROOT/unity/tools/assetstore/unity_native_asset.py
QUEUE=$ROOT/unity/tools/assetstore/queue_native_downloads.py
STATE=$ROOT/unity/assetstore/metadata/native_download_state.json
PY=/data/venv/bin/python

mapfile -t PACKAGE_IDS < <(python3 - <<'PY' "$STATE"
import json, sys
from pathlib import Path
state = json.loads(Path(sys.argv[1]).read_text())
for key, value in sorted(state.items(), key=lambda kv: int(kv[0])):
    if value.get('status') == 'error':
        print(key)
PY
)

if [[ ${#PACKAGE_IDS[@]} -eq 0 ]]; then
  echo "No error-state packages to retry."
  exit 0
fi

for package_id in "${PACKAGE_IDS[@]}"; do
  echo "Retrying $package_id"
  sudo -u hans -H env DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus XDG_RUNTIME_DIR=/run/user/1000 \
    "$PY" "$QUEUE" --package-ids "$package_id" --skip-existing --timeout 7200
  echo "Done $package_id"
done
