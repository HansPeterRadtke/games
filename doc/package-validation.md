# Package Validation

## Single release entrypoint
Use:
- `unity/tools/release/validate_release_candidate.sh`

This is the authoritative validator for the current first-release package set. It runs:
1. release audit
2. dependency audit
3. headless composition/eventbus validation
4. clean-project import for every selected package
5. package demo execution for every selected package
6. clean-project import for the selected package combinations
7. full game build
8. full game smoke validation

## Current first-release package set
- `com.hpr.eventbus`
- `com.hpr.composition`
- `com.hpr.save`
- `com.hpr.stats`
- `com.hpr.inventory`
- `com.hpr.interaction`
- `com.hpr.abilities`
- `com.hpr.weapons`
- `com.hpr.ai`
- `com.hpr.world`

## Supporting validators
- `unity/tools/packages/validate_local_packages.sh <package-name> [more packages...]`
- `unity/tools/architecture/run_phase1_headless_validation.sh`
- `unity/tools/architecture/dependency_audit.py`
- `unity/tools/release/release_audit.py`

`validate_local_packages.sh` creates a clean temporary Unity project, resolves declared local package dependencies, copies only the requested packages into that project, and runs Unity batch validation there. It does not symlink package folders, so package demo execution cannot mutate the source package folders.

## What a release pass proves
For every package in the first-release set:
- package metadata is present and consistent
- the README is external-user-facing and includes install/demo/validation guidance
- the package imports into a clean Unity project with only its declared dependencies
- the package demo validator executes successfully in that clean project
- the package has no forbidden references to `GameManager`, `SceneBootstrap`, `com.hpr.fpsdemo`, parent-service discovery, or local machine paths
- the package contents are limited to authored code, metadata, and demo assets that are safe to redistribute

For the repository as a whole:
- the selected release packages validate together as a combined import set
- the game still builds and the canonical smoke path still completes

## Canonical commands
### Full release candidate
- `unity/tools/release/validate_release_candidate.sh`

### Individual package validation
- `EXECUTE_METHOD=EventBusPackageValidator.ValidateInBatch unity/tools/packages/validate_local_packages.sh com.hpr.eventbus`
- `EXECUTE_METHOD=CompositionPackageValidator.ValidateInBatch unity/tools/packages/validate_local_packages.sh com.hpr.composition`
- `EXECUTE_METHOD=SavePackageValidator.ValidateInBatch unity/tools/packages/validate_local_packages.sh com.hpr.save`
- `EXECUTE_METHOD=StatsPackageValidator.ValidateInBatch unity/tools/packages/validate_local_packages.sh com.hpr.stats`
- `EXECUTE_METHOD=InventoryPackageValidator.ValidateInBatch unity/tools/packages/validate_local_packages.sh com.hpr.inventory`
- `EXECUTE_METHOD=InteractionPackageValidator.ValidateInBatch unity/tools/packages/validate_local_packages.sh com.hpr.interaction`
- `EXECUTE_METHOD=AbilitiesPackageValidator.ValidateInBatch unity/tools/packages/validate_local_packages.sh com.hpr.abilities`
- `EXECUTE_METHOD=WeaponsPackageValidator.ValidateInBatch unity/tools/packages/validate_local_packages.sh com.hpr.weapons`
- `EXECUTE_METHOD=AiPackageValidator.ValidateInBatch unity/tools/packages/validate_local_packages.sh com.hpr.ai`
- `EXECUTE_METHOD=WorldPackageValidator.ValidateInBatch unity/tools/packages/validate_local_packages.sh com.hpr.world`

### Package-set combinations
- `unity/tools/packages/validate_local_packages.sh com.hpr.composition com.hpr.eventbus`
- `unity/tools/packages/validate_local_packages.sh com.hpr.eventbus com.hpr.stats`
- `unity/tools/packages/validate_local_packages.sh com.hpr.inventory com.hpr.interaction`
- `unity/tools/packages/validate_local_packages.sh com.hpr.eventbus com.hpr.stats com.hpr.abilities`
- `unity/tools/packages/validate_local_packages.sh com.hpr.weapons com.hpr.ai com.hpr.world`
- `unity/tools/packages/validate_local_packages.sh com.hpr.eventbus com.hpr.composition com.hpr.save com.hpr.stats com.hpr.inventory com.hpr.interaction com.hpr.abilities com.hpr.weapons com.hpr.ai com.hpr.world`

## Latest successful proof artifacts
### Audits
- `doc/release-audit.md`
- `doc/dependency-audit-phase1.md`

### Package validation logs
- `doc/logs/package_validation/20260328_125318_com_hpr_eventbus_.log`
- `doc/logs/package_validation/20260328_125327_com_hpr_eventbus__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_125347_com_hpr_composition_.log`
- `doc/logs/package_validation/20260328_125356_com_hpr_composition__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_125416_com_hpr_save_.log`
- `doc/logs/package_validation/20260328_125425_com_hpr_save__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_125446_com_hpr_stats_.log`
- `doc/logs/package_validation/20260328_125455_com_hpr_stats__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_125516_com_hpr_inventory_.log`
- `doc/logs/package_validation/20260328_125524_com_hpr_inventory__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_125545_com_hpr_interaction_.log`
- `doc/logs/package_validation/20260328_125554_com_hpr_interaction__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_125615_com_hpr_abilities_.log`
- `doc/logs/package_validation/20260328_125624_com_hpr_abilities__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_125646_com_hpr_weapons_.log`
- `doc/logs/package_validation/20260328_125654_com_hpr_weapons__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_125715_com_hpr_ai_.log`
- `doc/logs/package_validation/20260328_125723_com_hpr_ai__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_125744_com_hpr_world_.log`
- `doc/logs/package_validation/20260328_125753_com_hpr_world__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_125814_com_hpr_composition_com_hpr_eventbus_.log`
- `doc/logs/package_validation/20260328_125835_com_hpr_eventbus_com_hpr_stats_.log`
- `doc/logs/package_validation/20260328_125856_com_hpr_inventory_com_hpr_interaction_.log`
- `doc/logs/package_validation/20260328_125918_com_hpr_eventbus_com_hpr_stats_com_hpr_abilities_.log`
- `doc/logs/package_validation/20260328_125940_com_hpr_weapons_com_hpr_ai_com_hpr_world_.log`
- `doc/logs/package_validation/20260328_130003_com_hpr_eventbus_com_hpr_composition_com_hpr_save_com_hpr_stats_com_hpr_inventory_com_hpr_interaction_com_hpr_abilities_com_hpr_weapons_com_hpr_ai_com_hpr_world_.log`

### Full game validation
- `doc/logs/20260328_130012_BuildLinux.log`
- `/home/hans/.config/unity3d/DefaultCompany/fps_demo/Player.log`
