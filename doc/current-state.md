# Current State

## Repository purpose
`games` contains a Unity workspace under `unity/` with one current playable prototype:
- `unity/projects/fps_demo` - the Unity project
- `unity/packages/com.hpr.fpsdemo` - shared FPS gameplay/editor package
- `unity/packages/com.hpr.foundation` - shared base utilities
- `unity/tools/` - reproducible helpers used to build, test, import, and diagnose the project

## What is committed
Committed content is limited to:
- gameplay/runtime code
- editor tooling
- setup/build/test scripts
- local-asset import automation
- documentation
- Unity project metadata that does not require local-only imported art assets

## What is intentionally not committed
The following stay local-only:
- downloaded `.unitypackage` files
- imported Asset Store folders under `unity/projects/fps_demo/Assets/...`
- generated asset metadata registries for imported local art
- Unity `Library/`, `Temp/`, `Logs/`, and build artifacts
- queue logs and download metadata under `unity/assetstore/`

The `.gitignore` already covers the local-only asset roots and pipeline state.

## Architecture summary
The current gameplay architecture is package-based and data-driven.

### Core gameplay package
`unity/packages/com.hpr.fpsdemo`
- runtime systems
- editor/import tooling
- data ScriptableObjects
- event bus and validation

### Runtime boundaries
- `PlayerController` / player runtime components: movement and player-facing runtime state
- `WeaponSystem`: weapon loadout, ammo runtime state, combat dispatch
- `PlayerInventory`: inventory data keyed by item IDs
- `EnemyAgent`: enemy runtime behavior delegated from data
- `GameManager`: scene/session orchestration, save/load, smoke path
- `EventManager`: central event bus used by gameplay systems

### Data-driven pieces already present
- `WeaponData`
- `ItemData`
- `EnemyData`
- asset metadata/registry support for imported art

### Editor/tooling already present
- scene/bootstrap/build helpers
- data seeding helpers
- imported asset metadata synchronizer
- third-party asset integrator
- third-party scene reporter
- prefab/material reporters

## Current reality about art integration
The project supports local-only third-party art integration, but those integrations are not a committed source of truth.
The committed source of truth is:
- the gameplay code
- the integration scripts
- the documented workflow

If a new machine needs the same art, the expected path is:
1. download/import the local asset packs again
2. run the documented integration helpers as `hans`
3. keep imported content local-only

## Ownership rule
Everything in this repo should be writable/readable by user `hans`.
The repo should not rely on root-owned files.
