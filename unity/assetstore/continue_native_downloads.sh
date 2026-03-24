#!/usr/bin/env bash
set -euo pipefail
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export XDG_RUNTIME_DIR=/run/user/1000
RUNNER=/data/src/github/games/unity/tools/assetstore/unity_native_asset.py
PY=/data/venv/bin/python
LOG=/data/src/github/games/unity/assetstore/logs/continue_native_downloads.log
PACKAGES=(151980 258782 71426 124055 107224 326131 181470 157920 288783 52977 138810 279940 48529 213197 267961)
wait_for_final() {
  local path="$1"
  while true; do
    if [[ -f "$path" ]]; then
      local magic
      magic=$(python3 - <<PY
from pathlib import Path
p = Path(r'''$path''')
print(p.read_bytes()[:2].hex() if p.exists() and p.stat().st_size >= 2 else '')
PY
)
      if [[ "$magic" == '1f8b' ]]; then
        return 0
      fi
    fi
    sleep 20
  done
}
run_download() {
  local package_id="$1"
  while true; do
    echo "START $(date -Iseconds) ${package_id}" | tee -a "$LOG"
    if sudo -u hans -H env DBUS_SESSION_BUS_ADDRESS="$DBUS_SESSION_BUS_ADDRESS" XDG_RUNTIME_DIR="$XDG_RUNTIME_DIR" "$PY" "$RUNNER" download "$package_id" --timeout 3600 >>"$LOG" 2>&1; then
      echo "DONE  $(date -Iseconds) ${package_id}" | tee -a "$LOG"
      return 0
    fi
    echo "RETRY $(date -Iseconds) ${package_id}" | tee -a "$LOG"
    sleep 60
  done
}
wait_for_final '/home/hans/.local/share/unity3d/Asset Store-5.x/dlgames/3D ModelsPropsFurniture/Furniture Mega Pack - Free.unitypackage'
for package_id in "${PACKAGES[@]}"; do
  run_download "$package_id"
done
