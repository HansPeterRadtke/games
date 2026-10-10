#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
for f in test-physics.mjs tests/active-regression.mjs tests/local-obstacle-regression.mjs tests/prse-transition.mjs tests/semantic-input-regression.mjs tests/hidden-and-character.mjs tests/world-proposals.mjs tests/modality-contract.mjs tests/gameplay-journey.mjs tests/injury-response-study.mjs tests/performance.mjs; do
  echo "== $f =="
  node "$f"
done
