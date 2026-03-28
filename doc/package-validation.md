# Package Validation

## Single release-candidate entrypoint
Use:
- `unity/tools/release/validate_release_candidate.sh`

This is the authoritative validation entrypoint for the current sale-ready package set.
It runs:
1. release audit
2. dependency audit
3. headless validation
4. clean-project import + demo execution for each sale-ready package
5. clean-project import for the sale-ready package combinations
6. full game build
7. full game smoke test

## Current sale-ready package set
- `com.hpr.eventbus`
- `com.hpr.composition`
- `com.hpr.save`
- `com.hpr.stats`
- `com.hpr.inventory`
- `com.hpr.interaction`
- `com.hpr.abilities`

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
- package content is legally safe to redistribute

## Latest verified commands
Verified through the latest release-candidate pass on 2026-03-28:
- `unity/tools/release/validate_release_candidate.sh`
- `unity/tools/architecture/run_phase1_headless_validation.sh`
- `unity/tools/packages/validate_local_packages.sh com.hpr.eventbus`
- `EXECUTE_METHOD=EventBusPackageValidator.ValidateInBatch unity/tools/packages/validate_local_packages.sh com.hpr.eventbus`
- `unity/tools/packages/validate_local_packages.sh com.hpr.composition`
- `EXECUTE_METHOD=CompositionPackageValidator.ValidateInBatch unity/tools/packages/validate_local_packages.sh com.hpr.composition`
- `unity/tools/packages/validate_local_packages.sh com.hpr.save`
- `EXECUTE_METHOD=SavePackageValidator.ValidateInBatch unity/tools/packages/validate_local_packages.sh com.hpr.save`
- `unity/tools/packages/validate_local_packages.sh com.hpr.stats`
- `EXECUTE_METHOD=StatsPackageValidator.ValidateInBatch unity/tools/packages/validate_local_packages.sh com.hpr.stats`
- `unity/tools/packages/validate_local_packages.sh com.hpr.inventory`
- `EXECUTE_METHOD=InventoryPackageValidator.ValidateInBatch unity/tools/packages/validate_local_packages.sh com.hpr.inventory`
- `unity/tools/packages/validate_local_packages.sh com.hpr.interaction`
- `EXECUTE_METHOD=InteractionPackageValidator.ValidateInBatch unity/tools/packages/validate_local_packages.sh com.hpr.interaction`
- `unity/tools/packages/validate_local_packages.sh com.hpr.abilities`
- `EXECUTE_METHOD=AbilitiesPackageValidator.ValidateInBatch unity/tools/packages/validate_local_packages.sh com.hpr.abilities`
- `unity/tools/packages/validate_local_packages.sh com.hpr.composition com.hpr.eventbus`
- `unity/tools/packages/validate_local_packages.sh com.hpr.eventbus com.hpr.stats`
- `unity/tools/packages/validate_local_packages.sh com.hpr.inventory com.hpr.interaction`
- `unity/tools/packages/validate_local_packages.sh com.hpr.eventbus com.hpr.stats com.hpr.abilities`
- `unity/tools/packages/validate_local_packages.sh com.hpr.eventbus com.hpr.composition com.hpr.save com.hpr.stats com.hpr.inventory com.hpr.interaction com.hpr.abilities`
- `unity/tools/fps_demo/run_unity_batch.sh SceneBootstrap.BuildLinux`
- `NO_NOTICE=1 unity/tools/fps_demo/smoke_test.sh`

## Latest proof logs
### Release audits
- `doc/release-audit.md`
- `doc/dependency-audit-phase1.md`

### Package validation logs
- `doc/logs/package_validation/20260328_113740_com_hpr_eventbus_.log`
- `doc/logs/package_validation/20260328_113748_com_hpr_eventbus__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_113809_com_hpr_composition_.log`
- `doc/logs/package_validation/20260328_113817_com_hpr_composition__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_113838_com_hpr_save_.log`
- `doc/logs/package_validation/20260328_113846_com_hpr_save__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_113907_com_hpr_stats_.log`
- `doc/logs/package_validation/20260328_113915_com_hpr_stats__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_113937_com_hpr_inventory_.log`
- `doc/logs/package_validation/20260328_113945_com_hpr_inventory__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_114006_com_hpr_interaction_.log`
- `doc/logs/package_validation/20260328_114014_com_hpr_interaction__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_114036_com_hpr_abilities_.log`
- `doc/logs/package_validation/20260328_114045_com_hpr_abilities__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_114107_com_hpr_composition_com_hpr_eventbus_.log`
- `doc/logs/package_validation/20260328_114129_com_hpr_eventbus_com_hpr_stats_.log`
- `doc/logs/package_validation/20260328_114152_com_hpr_inventory_com_hpr_interaction_.log`
- `doc/logs/package_validation/20260328_114214_com_hpr_eventbus_com_hpr_stats_com_hpr_abilities_.log`
- `doc/logs/package_validation/20260328_114236_com_hpr_eventbus_com_hpr_composition_com_hpr_save_com_hpr_stats_com_hpr_inventory_com_hpr_interaction_com_hpr_abilities_.log`

### Full game validation logs
- `doc/logs/20260328_114247_BuildLinux.log`
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
