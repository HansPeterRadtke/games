# Current State

## Repository purpose
`games` contains a Unity workspace under `unity/` with:
- a playable composition project: `unity/projects/fps_demo`
- a package workspace: `unity/packages/com.hpr.*`
- reproducible validation/build tooling: `unity/tools/`
- architecture and handoff docs: `doc/`

## Sale-ready package set in this checkpoint
These are the only packages currently designated as ready for external sale/upload:
- `unity/packages/com.hpr.eventbus`
- `unity/packages/com.hpr.composition`

Why only these two:
- they are the only packages that currently have verified standalone clean-project import, standalone demo execution, no forbidden architectural references, and release documentation/tooling in place
- the rest of the package tree is still useful and partly modularized, but not yet product-clean enough for external sale

## Internal package set still under extraction
Not yet sale-ready:
- `unity/packages/com.hpr.foundation`
- `unity/packages/com.hpr.core`
- `unity/packages/com.hpr.input`
- `unity/packages/com.hpr.save`
- `unity/packages/com.hpr.inventory`
- `unity/packages/com.hpr.weapons`
- `unity/packages/com.hpr.ai`
- `unity/packages/com.hpr.stats`
- `unity/packages/com.hpr.world`
- `unity/packages/com.hpr.abilities`
- `unity/packages/com.hpr.interaction`
- `unity/packages/com.hpr.ui`
- `unity/packages/com.hpr.bootstrap`
- `unity/packages/com.hpr.fpsdemo`

## Current architecture summary
### Sale-ready packages
- `com.hpr.eventbus`
  - owns only generic event transport and Unity adapter code
- `com.hpr.composition`
  - owns only explicit service registration, lifecycle, and tick/disposal primitives

### Internal game composition
- `com.hpr.fpsdemo` still owns project-specific game flow, build/bootstrap adapters, smoke validation flow, and other composition-heavy game runtime
- `com.hpr.core` still carries current gameplay-domain event payloads and shared game/runtime contracts

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
- the sellable package set imports into fresh empty Unity projects
- those packages compile there
- those packages run their own package demos there
- the sellable package set combination imports cleanly together
- release and dependency audits pass for the sellable set
- the main game still builds and passes smoke validation after the package split work

### Latest proof artifacts
- `doc/release-audit.md`
- `doc/dependency-audit-phase1.md`
- `doc/logs/package_validation/20260327_194854_com_hpr_eventbus__ValidateInBatch.log`
- `doc/logs/package_validation/20260327_195023_com_hpr_composition__ValidateInBatch.log`
- `doc/logs/package_validation/20260327_195113_com_hpr_composition_com_hpr_eventbus_.log`
- `doc/logs/20260327_195141_BuildLinux.log`
- `/home/hans/.config/unity3d/DefaultCompany/fps_demo/Player.log`

## Current modularity reality
- `com.hpr.eventbus` is genuinely standalone
- `com.hpr.composition` is genuinely standalone
- the rest of the repo is not yet fully productized for sale
- `com.hpr.fpsdemo` remains the primary internal composition layer and the main extraction target

## Ownership rule
Everything in this repo should be readable and writable by `hans`. Root-owned files are a bug and must be corrected immediately.
