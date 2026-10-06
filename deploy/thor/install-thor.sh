#!/usr/bin/env bash
set -euo pipefail
[[ $(id -u) -eq 0 ]] || { echo 'install-thor.sh must run as root' >&2; exit 1; }
[[ $(hostname -s) == thor ]] || { echo 'install-thor.sh is Thor-only' >&2; exit 1; }
ROOT=${GAMES_ROOT:-/data/src/github/games}
for unit in llm-game-image.service llm-game-world-small.service; do
    install -m 0644 "$ROOT/deploy/thor/$unit" "/etc/systemd/system/$unit"
done
systemctl daemon-reload
systemd-analyze verify /etc/systemd/system/llm-game-image.service /etc/systemd/system/llm-game-world-small.service
echo 'Installed Thor game services. Runtime enable/active state was intentionally left unchanged.'
