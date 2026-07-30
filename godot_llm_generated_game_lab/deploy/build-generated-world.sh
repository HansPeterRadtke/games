#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# The legacy SDXL-frame compiler is intentionally not a deployment path.
# All generated-world builds must pass the StableAnimator pose, recurrent RVM alpha,
# executable-action, scene-recognizability and public-browser gates.
exec bash deploy/build-temporal-world.sh "$@"
