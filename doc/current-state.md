# Current State

## Repository purpose
`games` contains a Unity workspace under `unity/` with:
- a playable composition project: `unity/projects/fps_demo`
- a package workspace: `unity/packages/com.hpr.*`
- reproducible validation/build tooling: `unity/tools/`
- architecture and handoff docs: `doc/`

## Sale-ready package set in this checkpoint
These packages are currently designated as ready for external sale/upload:
- `unity/packages/com.hpr.eventbus`
- `unity/packages/com.hpr.composition`
- `unity/packages/com.hpr.save`
- `unity/packages/com.hpr.stats`
- `unity/packages/com.hpr.inventory`
- `unity/packages/com.hpr.interaction`
- `unity/packages/com.hpr.abilities`

Why this set qualifies:
- each package has verified standalone clean-project import
- each package has verified standalone demo execution
- the combined release set imports cleanly together
- the release audit and dependency audit pass for the selected set
- the main game still builds and passes smoke with the selected set composed back in

## Internal package set still under extraction
Not yet sale-ready:
- `unity/packages/com.hpr.foundation`
- `unity/packages/com.hpr.core`
- `unity/packages/com.hpr.input`
- `unity/packages/com.hpr.weapons`
- `unity/packages/com.hpr.ai`
- `unity/packages/com.hpr.world`
- `unity/packages/com.hpr.ui`
- `unity/packages/com.hpr.bootstrap`
- `unity/packages/com.hpr.fpsdemo`

## Current architecture summary
### Sale-ready packages
- `com.hpr.eventbus`
  - generic typed publish/subscribe transport and Unity adapter
- `com.hpr.composition`
  - generic explicit service registration and lifecycle orchestration
- `com.hpr.save`
  - generic save data wrappers and `ISaveableEntity`
- `com.hpr.stats`
  - reusable health/stamina and damage-event runtime
- `com.hpr.inventory`
  - reusable item definitions and inventory storage/runtime
- `com.hpr.interaction`
  - reusable interaction contracts, pickup flow, and keyed-door runtime
- `com.hpr.abilities`
  - reusable data-driven active abilities over eventbus/stats

### Internal game composition
- `com.hpr.fpsdemo` still owns game-specific flow, authored world composition, bootstrap/build adapters, and smoke validation flow
- `com.hpr.core` and the remaining internal packages still carry internal-only gameplay contracts or composition ownership that is not yet productized

## What is committed
Committed content is limited to:
- package/runtime/editor code we authored
- package manifests and package docs
- validation/build/audit scripts
- project metadata and authored data assets we own
- documentation

## What is intentionally not committed
The following stay local-only:
- downloaded `.unitypackage` files
- imported Asset Store folders under `unity/projects/fps_demo/Assets/...`
- generated asset metadata registries for imported local art
- Unity `Library/`, `Temp/`, `Logs/`, and build artifacts

The local-only imported asset inventory is documented in `doc/local-assets.md`.

## Verified validation state
### Release-candidate entrypoint
- `unity/tools/release/validate_release_candidate.sh`

### What it proves today
- every selected sale-ready package imports into a fresh empty Unity project
- every selected sale-ready package compiles there
- every selected sale-ready package runs its own package demo there
- the selected package-set combination imports cleanly together
- release and dependency audits pass for the selected set
- the main game still builds and passes smoke validation after the package split work

### Latest proof artifacts
- `doc/release-audit.md`
- `doc/dependency-audit-phase1.md`
- `doc/logs/package_validation/20260328_113748_com_hpr_eventbus__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_113817_com_hpr_composition__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_113846_com_hpr_save__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_113915_com_hpr_stats__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_113945_com_hpr_inventory__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_114014_com_hpr_interaction__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_114045_com_hpr_abilities__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_114236_com_hpr_eventbus_com_hpr_composition_com_hpr_save_com_hpr_stats_com_hpr_inventory_com_hpr_interaction_com_hpr_abilities_.log`
- `doc/logs/20260328_114247_BuildLinux.log`
- `/home/hans/.config/unity3d/DefaultCompany/fps_demo/Player.log`

## Current modularity reality
- the seven-package release set above is genuinely standalone by current audit/validation proof
- `com.hpr.fpsdemo` remains the primary internal composition layer and the main extraction target
- the remaining internal packages are usable in the game but are not yet productized to the same standard

## Ownership rule
Everything in this repo should be readable and writable by `hans`. Root-owned files are a bug and must be corrected immediately.
