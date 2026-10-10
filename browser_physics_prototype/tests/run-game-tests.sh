#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."
for file in \
  test-physics.mjs \
  tests/active-regression.mjs \
  tests/local-obstacle-regression.mjs \
  tests/prse-transition.mjs \
  tests/semantic-input-regression.mjs \
  tests/hidden-and-character.mjs \
  tests/world-proposals.mjs \
  tests/scene-translation.mjs \
  tests/affordance-boundary.mjs \
  tests/causal-world.mjs \
  tests/npc-knowledge.mjs \
  tests/narrative-roundtrip.mjs \
  tests/semantic-command-study.mjs \
  tests/save-migration.mjs \
  tests/event-journal.mjs \
  tests/modality-contract.mjs \
  tests/gameplay-journey.mjs \
  tests/injury-response-study.mjs \
  tests/llm-region-adapter.mjs \
  tests/llm-consistency-regression.mjs \
  tests/llm-branch-world.mjs \
  tests/llm-region-physical-integration.mjs \
  tests/performance.mjs; do
  echo "== ${file} =="
  node "$file"
done
