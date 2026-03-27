# Modularization Status

## Checkpoint
The repo is past the original phase-one split and is now in a verified release-candidate checkpoint for the first external package set.

Release-candidate packages:
- `com.hpr.eventbus`
- `com.hpr.composition`

## What is complete
### `com.hpr.eventbus`
- standalone runtime transport
- Unity adapter only where needed
- package-owned demo scene
- package-owned batch validator
- clean-project import validated
- no forbidden references in release audit

### `com.hpr.composition`
- standalone service registry and composition root
- headless validation path
- package-owned demo scene
- package-owned batch validator
- clean-project import validated
- no forbidden references in release audit

## What remains internal
The package workspace is larger than the current sellable set.
Remaining packages are still internal because they still contain one or more of:
- game-domain ownership that is not yet productized
- project-specific composition or bootstrap assumptions
- remaining forbidden lookup patterns
- insufficient external-user documentation/demo coverage

Primary internal blockers are still concentrated in:
- `com.hpr.fpsdemo`
- `com.hpr.interaction`
- `com.hpr.inventory` demo layer
- `com.hpr.stats`
- `com.hpr.core`

## Current dependency truth
### Clean for external sale in this checkpoint
- `com.hpr.eventbus`
- `com.hpr.composition`

### Not yet clean for sale
See:
- `doc/dependency-audit-phase1.md`

Current known violation groups outside the sellable set:
- parent `MonoBehaviour` service lookup fallbacks
- direct scene search in some demo/runtime code
- remaining game-specific ownership in `com.hpr.fpsdemo`

## Verified validations
Executed successfully as `hans`:
- `unity/tools/release/validate_release_candidate.sh`
- `unity/tools/architecture/run_phase1_headless_validation.sh`
- `unity/tools/packages/validate_local_packages.sh com.hpr.eventbus`
- `unity/tools/packages/validate_local_packages.sh com.hpr.composition`
- `unity/tools/packages/validate_local_packages.sh com.hpr.composition com.hpr.eventbus`
- `unity/tools/fps_demo/run_unity_batch.sh SceneBootstrap.BuildLinux`
- `NO_NOTICE=1 unity/tools/fps_demo/smoke_test.sh`

## Next extraction targets
1. remove remaining parent-service discovery from internal packages
2. shrink `com.hpr.fpsdemo` further until it is only game-specific composition/content
3. split gameplay-domain events out of `com.hpr.core` where product boundaries require it
4. productize the next candidate package only after it has standalone demo, docs, and clean-project proof
