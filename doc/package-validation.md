# Package Validation

## Single release-candidate entrypoint
Use:
- `unity/tools/release/validate_release_candidate.sh`

This is the current authoritative validation entrypoint for the sale-ready package set.
It runs:
1. release audit
2. dependency audit
3. headless validation
4. clean-project import + demo execution for each sale-ready package
5. clean-project import for the sale-ready package combination
6. full game build
7. full game smoke test

## Lower-level helpers
- `unity/tools/packages/validate_local_packages.sh <package-name> [more packages...]`
- `unity/tools/architecture/run_phase1_headless_validation.sh`
- `unity/tools/architecture/dependency_audit.py`
- `unity/tools/release/release_audit.py`

The Unity package validator creates a clean temporary Unity project, resolves declared local package dependencies, symlinks only those packages into the temp project, and batch-runs Unity.
Each invocation uses its own temp project path by default, so multiple validations can run concurrently without Unity project-lock collisions.

## What currently counts as sale-ready proof
For a designated sale-ready package, the repo now requires all of the following:
- package metadata exists and passes release audit
- README contains installation/quick-start/API/demo/validation sections
- clean-project import succeeds
- package demo execute method succeeds in that clean project
- no forbidden architectural references are present in the package

## Latest verified commands
Verified through the latest release-candidate pass on 2026-03-27:
- `unity/tools/release/validate_release_candidate.sh`
- `unity/tools/architecture/run_phase1_headless_validation.sh`
- `unity/tools/packages/validate_local_packages.sh com.hpr.eventbus`
- `unity/tools/packages/validate_local_packages.sh com.hpr.composition`
- `unity/tools/packages/validate_local_packages.sh com.hpr.composition com.hpr.eventbus`
- `unity/tools/fps_demo/run_unity_batch.sh SceneBootstrap.BuildLinux`
- `NO_NOTICE=1 unity/tools/fps_demo/smoke_test.sh`

## Latest proof logs
### Release audits
- `doc/release-audit.md`
- `doc/dependency-audit-phase1.md`

### Package validation logs
- `doc/logs/package_validation/20260327_194816_com_hpr_eventbus_.log`
- `doc/logs/package_validation/20260327_194854_com_hpr_eventbus__ValidateInBatch.log`
- `doc/logs/package_validation/20260327_194953_com_hpr_composition_.log`
- `doc/logs/package_validation/20260327_195023_com_hpr_composition__ValidateInBatch.log`
- `doc/logs/package_validation/20260327_195113_com_hpr_composition_com_hpr_eventbus_.log`

### Full game validation logs
- `doc/logs/20260327_195141_BuildLinux.log`
- `/home/hans/.config/unity3d/DefaultCompany/fps_demo/Player.log`

## Current meaning of a pass
### Headless validation proves
- `CompositionRoot` initializes and disposes services without scene wiring
- `EventBus` supports typed publish/subscribe
- base-type subscription delivery works
- disposed subscriptions stop receiving events

### Clean-project package validation proves
- the selected packages import into an empty Unity project
- declared local package dependencies resolve correctly
- Unity script compilation succeeds there
- the package-owned demo execute method succeeds there

### Full project build + smoke proves
- the main game still builds after the modularization work
- the release-candidate packages still compose back into the game cleanly
- the smoke path still reaches completion

## What this does not prove
- the internal package set is ready for sale
- every package in the repo is standalone yet
- future package candidates are productized automatically
