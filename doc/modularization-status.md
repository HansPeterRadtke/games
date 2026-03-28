# Modularization Status

## Checkpoint
The repo is in a verified release-candidate checkpoint for this first external package set:
- `com.hpr.eventbus`
- `com.hpr.composition`
- `com.hpr.save`
- `com.hpr.stats`
- `com.hpr.inventory`
- `com.hpr.interaction`
- `com.hpr.abilities`

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

### `com.hpr.save`
- standalone save primitives and contracts
- package-owned demo scene
- package-owned batch validator
- clean-project import validated
- no forbidden references in release audit

### `com.hpr.stats`
- standalone actor stats runtime and event payloads
- package-owned demo scene
- package-owned batch validator
- clean-project import validated
- no forbidden references in release audit

### `com.hpr.inventory`
- standalone item and inventory runtime
- package-owned demo scene and authored demo items
- package-owned batch validator
- clean-project import validated
- no forbidden references in release audit

### `com.hpr.interaction`
- standalone interaction contracts and runtime components
- package-owned demo scene
- package-owned batch validator
- clean-project import validated
- no forbidden references in release audit

### `com.hpr.abilities`
- standalone ability runtime and authored demo data
- package-owned demo scene
- package-owned batch validator
- clean-project import validated
- no forbidden references in release audit

## What remains internal
The remaining package workspace is still internal because it still contains one or more of:
- game-specific composition or bootstrap ownership
- incomplete product docs/demo/validator coverage
- runtime responsibilities that are still too entangled with the main game

Primary internal blockers are concentrated in:
- `com.hpr.fpsdemo`
- `com.hpr.core`
- `com.hpr.weapons`
- `com.hpr.ai`
- `com.hpr.world`
- `com.hpr.input`
- `com.hpr.ui`
- `com.hpr.bootstrap`

## Current dependency truth
### Clean for external sale in this checkpoint
- `com.hpr.eventbus`
- `com.hpr.composition`
- `com.hpr.save`
- `com.hpr.stats`
- `com.hpr.inventory`
- `com.hpr.interaction`
- `com.hpr.abilities`

### Not yet clean for sale
See:
- `doc/dependency-audit-phase1.md`

Current known violation groups outside the sellable set:
- `GameManager` ownership and references in `com.hpr.fpsdemo`
- `SceneBootstrap` ownership in `com.hpr.fpsdemo`
- parent `MonoBehaviour` service lookup fallbacks inside `com.hpr.fpsdemo`

## Verified validations
Executed successfully as `hans` on 2026-03-28:
- `unity/tools/release/validate_release_candidate.sh`
- `unity/tools/architecture/run_phase1_headless_validation.sh`
- `unity/tools/packages/validate_local_packages.sh com.hpr.eventbus`
- `unity/tools/packages/validate_local_packages.sh com.hpr.composition`
- `unity/tools/packages/validate_local_packages.sh com.hpr.save`
- `unity/tools/packages/validate_local_packages.sh com.hpr.stats`
- `unity/tools/packages/validate_local_packages.sh com.hpr.inventory`
- `unity/tools/packages/validate_local_packages.sh com.hpr.interaction`
- `unity/tools/packages/validate_local_packages.sh com.hpr.abilities`
- `unity/tools/packages/validate_local_packages.sh com.hpr.composition com.hpr.eventbus`
- `unity/tools/packages/validate_local_packages.sh com.hpr.eventbus com.hpr.stats`
- `unity/tools/packages/validate_local_packages.sh com.hpr.inventory com.hpr.interaction`
- `unity/tools/packages/validate_local_packages.sh com.hpr.eventbus com.hpr.stats com.hpr.abilities`
- `unity/tools/packages/validate_local_packages.sh com.hpr.eventbus com.hpr.composition com.hpr.save com.hpr.stats com.hpr.inventory com.hpr.interaction com.hpr.abilities`
- `unity/tools/fps_demo/run_unity_batch.sh SceneBootstrap.BuildLinux`
- `NO_NOTICE=1 unity/tools/fps_demo/smoke_test.sh`

## Next extraction targets
1. shrink `com.hpr.fpsdemo` further until it is only game-specific composition/content
2. split generic runtime out of `com.hpr.core`, `com.hpr.weapons`, `com.hpr.ai`, and `com.hpr.world` where product boundaries justify it
3. productize the next package only after it has the same demo, validator, audit, and clean-project proof level as the current release set
