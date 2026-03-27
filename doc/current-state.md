# Current State

## Repository purpose
`games` contains a Unity workspace under `unity/` with one current composition project and an ongoing conversion of reusable code into standalone Unity packages.

Main areas:
- `unity/projects/fps_demo` - current composition project and playable prototype
- `unity/packages/com.hpr.*` - reusable or in-progress reusable packages
- `unity/tools/` - reproducible build, audit, and validation helpers
- `doc/` - handoff and architecture status documentation

## What is committed
Committed content is limited to:
- package/runtime/editor code
- package manifests and package docs
- setup/build/test/audit scripts
- project metadata and authored data assets that are ours
- documentation

## What is intentionally not committed
The following stay local-only:
- downloaded `.unitypackage` files
- imported Asset Store folders under `unity/projects/fps_demo/Assets/...`
- generated asset metadata registries for imported local art
- Unity `Library/`, `Temp/`, `Logs/`, and build artifacts

The real local-only asset inventory is documented in `doc/local-assets.md`.

## Active package split
Real packages now carrying production code:
- `unity/packages/com.hpr.foundation`
- `unity/packages/com.hpr.core`
- `unity/packages/com.hpr.composition`
- `unity/packages/com.hpr.eventbus`
- `unity/packages/com.hpr.input`
- `unity/packages/com.hpr.save`
- `unity/packages/com.hpr.inventory`
- `unity/packages/com.hpr.weapons`
- `unity/packages/com.hpr.ai`
- `unity/packages/com.hpr.stats`
- `unity/packages/com.hpr.world`
- `unity/packages/com.hpr.abilities`
- `unity/packages/com.hpr.interaction`
- `unity/packages/com.hpr.fpsdemo`

Still mostly scaffold packages:
- `unity/packages/com.hpr.ui`
- `unity/packages/com.hpr.bootstrap`

## Current architecture summary
- `com.hpr.composition` owns explicit service registration and lifecycle primitives
- `com.hpr.eventbus` owns generic event transport only
- `com.hpr.core` owns shared service contracts and current gameplay-domain event payloads
- `com.hpr.input` owns input abstractions and options/binding storage
- `com.hpr.save` owns save payload types and save contracts
- `com.hpr.inventory` owns item definitions plus generic inventory runtime
- `com.hpr.weapons` owns weapon definitions and weapon metadata
- `com.hpr.ai` owns enemy definitions and AI metadata
- `com.hpr.stats` owns reusable actor stats runtime
- `com.hpr.world` owns generic asset metadata/registry types
- `com.hpr.abilities` owns reusable ability/effect data and runtime activation
- `com.hpr.interaction` owns reusable interaction contracts and generic interaction runtime
- `com.hpr.fpsdemo` still owns project-specific composition-heavy runtime and editor bootstrap logic

## Phase-one modularization checkpoint
This repo now has:
- an explicit runtime composition root: `FpsDemoCompositionRoot`
- an adapter service layer: `FpsDemoServiceAdapter`
- a pure headless validation path for composition + event dispatch
- a generated phase-one dependency audit in `doc/dependency-audit-phase1.md`

What it does not have yet:
- a thin `fpsdemo` package
- full elimination of scene-parent service lookup fallbacks
- package-safe separation of all gameplay-domain events
- standalone sellable demos/tests for every package

## Build and validation status
Verified as `hans`:
- `unity/tools/architecture/run_phase1_headless_validation.sh`
- `unity/tools/architecture/dependency_audit.py`
- `unity/tools/packages/validate_local_packages.sh com.hpr.eventbus`
- `unity/tools/packages/validate_local_packages.sh com.hpr.composition`
- `unity/tools/fps_demo/run_unity_batch.sh SceneBootstrap.BuildLinux`
- `NO_NOTICE=1 unity/tools/fps_demo/smoke_test.sh`

Validation logs live in `doc/logs/` and `doc/logs/package_validation/`.

## Current modularity reality
The event system is now truly standalone.
The composition root exists and works headlessly.
The main game still composes through `com.hpr.fpsdemo`, and that package is still the major remaining extraction target.

## Ownership rule
Everything in this repo should be readable and writable by `hans`. Root-owned files are a bug and must be corrected immediately.
