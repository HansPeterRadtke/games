#!/usr/bin/env bash
set -euo pipefail
UNITY_VERSION="${UNITY_VERSION:-6000.4.0f1}"
UNITY_BIN="${UNITY_BIN:-/data/apps/Unity/Hub/Editor/$UNITY_VERSION/Editor/Unity}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-14400}"
START_TS="$(date +%s)"
SELF_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"

echo "Waiting for Unity editor: $UNITY_BIN"
while true; do
  if [[ -x "$UNITY_BIN" ]]; then
    echo "Unity editor found: $UNITY_BIN"
    exec "$SELF_DIR/setup_project.sh"
  fi
  NOW="$(date +%s)"
  if (( NOW - START_TS > TIMEOUT_SECONDS )); then
    echo "Timed out waiting for Unity editor installation" >&2
    exit 1
  fi
  sleep 20
done
