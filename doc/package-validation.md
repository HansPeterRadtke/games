# Package Validation

## Frozen first-release package set
The first release is frozen to:
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

## Explicitly excluded packages
- `com.hpr.foundation`: internal support package; missing full external release assets and clean-project proof
- `com.hpr.core`: internal shared-contract package; not productized to the frozen first-release standard
- `com.hpr.input`: internal-only package; missing full external release assets and proof
- `com.hpr.ui`: internal UI support; not productized or isolated for external sale
- `com.hpr.bootstrap`: thin internal bootstrap helper; missing release metadata/docs and not marketed as a standalone product
- `com.hpr.fpsdemo`: game-specific composition/content package; not reusable product code

## Authoritative validator
- `unity/tools/release/validate_release_candidate.sh`

This entrypoint now writes fresh proof logs into `doc/logs/` for:
- release audit
- dependency audit
- headless validation
- package clean-project validation wrappers
- package combination validation wrappers
- game build wrapper
- game smoke wrapper

The package import/demo logs remain under `doc/logs/package_validation/`.

## Fresh proof from the current run
### Top-level validation logs
- `doc/logs/20260328_151627_release_audit.log`
- `doc/logs/20260328_151627_dependency_audit.log`
- `doc/logs/20260328_151627_headless_phase1_validation.log`
- `doc/logs/20260328_151627_game_build.log`
- `doc/logs/20260328_152347_BuildLinux.log`
- `doc/logs/20260328_151627_game_smoke.log`
- `doc/logs/20260328_152431_smoke_test.log`

### Package clean-project import and demo logs
- `doc/logs/package_validation/20260328_151644_com_hpr_eventbus_.log`
- `doc/logs/package_validation/20260328_151652_com_hpr_eventbus__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_151715_com_hpr_composition_.log`
- `doc/logs/package_validation/20260328_151726_com_hpr_composition__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_151747_com_hpr_save_.log`
- `doc/logs/package_validation/20260328_151756_com_hpr_save__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_151817_com_hpr_stats_.log`
- `doc/logs/package_validation/20260328_151826_com_hpr_stats__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_151847_com_hpr_inventory_.log`
- `doc/logs/package_validation/20260328_151856_com_hpr_inventory__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_151917_com_hpr_interaction_.log`
- `doc/logs/package_validation/20260328_151926_com_hpr_interaction__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_151948_com_hpr_abilities_.log`
- `doc/logs/package_validation/20260328_151957_com_hpr_abilities__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_152019_com_hpr_weapons_.log`
- `doc/logs/package_validation/20260328_152028_com_hpr_weapons__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_152049_com_hpr_ai_.log`
- `doc/logs/package_validation/20260328_152057_com_hpr_ai__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_152118_com_hpr_world_.log`
- `doc/logs/package_validation/20260328_152127_com_hpr_world__ValidateInBatch.log`

### Package combination logs
- `doc/logs/package_validation/20260328_152148_com_hpr_composition_com_hpr_eventbus_.log`
- `doc/logs/package_validation/20260328_152209_com_hpr_eventbus_com_hpr_stats_.log`
- `doc/logs/package_validation/20260328_152231_com_hpr_inventory_com_hpr_interaction_.log`
- `doc/logs/package_validation/20260328_152253_com_hpr_eventbus_com_hpr_stats_com_hpr_abilities_.log`
- `doc/logs/package_validation/20260328_152315_com_hpr_weapons_com_hpr_ai_com_hpr_world_.log`
- `doc/logs/package_validation/20260328_152337_com_hpr_eventbus_com_hpr_composition_com_hpr_save_com_hpr_stats_com_hpr_inventory_com_hpr_interaction_com_hpr_abilities_com_hpr_weapons_com_hpr_ai_com_hpr_world_.log`

## Canonical commands
- full release set: `unity/tools/release/validate_release_candidate.sh`
- game build only: `unity/tools/fps_demo/run_unity_batch.sh SceneBootstrap.BuildLinux`
- game smoke only: `NO_NOTICE=1 unity/tools/fps_demo/smoke_test.sh`
