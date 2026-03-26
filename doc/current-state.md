# Current State

## Repository purpose
`games` contains a Unity workspace under `unity/` with one current playable prototype:
- `unity/projects/fps_demo` - the Unity project
- `unity/packages/com.hpr.fpsdemo` - shared FPS gameplay/editor package
- `unity/packages/com.hpr.foundation` - shared base utilities
- `unity/packages/com.hpr.*` - new modular package split in progress
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
The real local asset inventory is documented in `doc/local-assets.md`.

## Architecture summary
The current gameplay architecture is package-based, data-driven, and mid-transition toward stricter reusable modules.

### Active package split
- `unity/packages/com.hpr.foundation` - low-level shared utilities
- `unity/packages/com.hpr.eventbus` - extracted event manager and gameplay event payloads
- `unity/packages/com.hpr.input` - extracted options, bindings, and input abstractions
- `unity/packages/com.hpr.core` - shared service contracts for composition/runtime binding
- `unity/packages/com.hpr.fpsdemo` - still the main composition-heavy gameplay package
- `unity/packages/com.hpr.stats`, `unity/packages/com.hpr.inventory`, `unity/packages/com.hpr.weapons`, `unity/packages/com.hpr.ai`, `unity/packages/com.hpr.interaction`, `unity/packages/com.hpr.ui`, `unity/packages/com.hpr.world`, `unity/packages/com.hpr.bootstrap` - scaffold packages prepared for the next extraction passes

### Runtime boundaries
- `PlayerController` / player runtime components: movement and player-facing runtime state
- `WeaponSystem`: weapon loadout, ammo runtime state, combat dispatch
- `PlayerInventory`: inventory data keyed by item IDs
- `EnemyAgent`: enemy runtime behavior delegated from data
- `GameManager`: scene/session orchestration, save/load, smoke path
- `EventManager`: central event bus used by gameplay systems, now living in `com.hpr.eventbus`

### Decoupling checkpoint
The following runtime systems no longer use `GameManager.Instance` and are bound through interfaces from the composition layer:
- `PlayerController`
- `PlayerGameplayController`
- `PlayerStats`
- `WeaponSystem`
- `WeaponFireModes`
- `PhysicsProjectile`
- `PickupItem`
- `DoorController`
- `EnemyAgent`
- `GameUiController`

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

Detailed modularization status is tracked in `doc/modularization-status.md`.

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
