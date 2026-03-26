# Current State

## Repository purpose
`games` contains a Unity workspace under `unity/` with one current playable prototype and an in-progress package productization effort.

Main areas:
- `unity/projects/fps_demo` - playable composition project
- `unity/packages/com.hpr.*` - reusable package split
- `unity/tools/` - reproducible build/test/package-validation helpers
- `doc/` - takeover and workflow documentation

## What is committed
Committed content is limited to:
- gameplay/runtime code
- editor tooling
- package validation helpers
- setup/build/test scripts
- documentation
- Unity project metadata that does not require local-only imported art assets

## What is intentionally not committed
The following stay local-only:
- downloaded `.unitypackage` files
- imported Asset Store folders under `unity/projects/fps_demo/Assets/...`
- generated asset metadata registries for imported local art
- Unity `Library/`, `Temp/`, `Logs/`, and build artifacts
- queue logs and local download metadata under `unity/assetstore/`

The real local-only asset inventory is documented in `doc/local-assets.md`.

## Active package split
Real packages already carrying production code or data:
- `unity/packages/com.hpr.foundation`
- `unity/packages/com.hpr.core`
- `unity/packages/com.hpr.eventbus`
- `unity/packages/com.hpr.input`
- `unity/packages/com.hpr.save`
- `unity/packages/com.hpr.inventory`
- `unity/packages/com.hpr.weapons`
- `unity/packages/com.hpr.ai`
- `unity/packages/com.hpr.fpsdemo`

Still mostly scaffold packages:
- `unity/packages/com.hpr.stats`
- `unity/packages/com.hpr.interaction`
- `unity/packages/com.hpr.ui`
- `unity/packages/com.hpr.world`
- `unity/packages/com.hpr.bootstrap`

## Current architecture summary
- `com.hpr.core` owns generic service contracts
- `com.hpr.eventbus` owns event dispatch and current domain payloads
- `com.hpr.input` owns input abstractions and binding/options storage
- `com.hpr.save` owns generic save payload types and save contracts
- `com.hpr.inventory` owns item definitions plus a generic `InventoryComponent`
- `com.hpr.weapons` owns weapon definitions and fire-mode enums
- `com.hpr.ai` owns enemy definitions and AI enums
- `com.hpr.stats` owns generic damage/health/stamina contracts and the reusable base stats component
- `com.hpr.fpsdemo` still owns composition-heavy runtime, editor bootstrapping, and project-specific gameplay orchestration

## Build and validation status
Verified as `hans`:
- main project build succeeds through `unity/tools/fps_demo/run_unity_batch.sh SceneBootstrap.BuildLinux`
- main project smoke path succeeds through `unity/tools/fps_demo/smoke_test.sh`
- clean-project import validation succeeds for:
  - `com.hpr.core`
  - `com.hpr.eventbus`
  - `com.hpr.input`
  - `com.hpr.save`
  - `com.hpr.inventory`
  - `com.hpr.weapons`
  - `com.hpr.ai`
  - `com.hpr.fpsdemo` with declared dependencies

Validation logs live in `doc/logs/package_validation/`.

## Runtime decoupling checkpoint
These systems no longer depend on `GameManager.Instance`:
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

## Current reality about art integration
The project supports local-only third-party art integration, but those integrations are not a committed source of truth. The committed source of truth is:
- the gameplay code
- the integration scripts
- the documented workflow

If a new machine needs the same art, the expected path is:
1. download/import the local asset packs again
2. run the documented integration helpers as `hans`
3. keep imported content local-only

## Ownership rule
Everything in this repo should be writable/readable by user `hans`. Root-owned files are a bug and should be corrected immediately.
