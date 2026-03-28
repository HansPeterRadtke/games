# Handoff

## Current release target
The current first-release package set is:
- `com.hpr.eventbus`
- `com.hpr.composition`
- `com.hpr.save`
- `com.hpr.stats`
- `com.hpr.inventory`
- `com.hpr.interaction`
- `com.hpr.abilities`
- `com.hpr.weapons`
- `com.hpr.ai`
- `com.hpr.world`

## Internal packages still excluded
- `com.hpr.foundation`
- `com.hpr.core`
- `com.hpr.input`
- `com.hpr.ui`
- `com.hpr.bootstrap`
- `com.hpr.fpsdemo`

## Current proof entrypoint
- `unity/tools/release/validate_release_candidate.sh`

## Next extraction targets
1. continue reducing `com.hpr.fpsdemo` to pure game composition/content
2. decide whether `com.hpr.input` can be brought to the same standalone sale bar
3. isolate any reusable UI widgets from game-specific menu flow
4. keep all third-party/imported art local-only and outside sellable packages

## Local-only art rule
Never add imported Asset Store data to the sellable packages or to git-tracked package content.
