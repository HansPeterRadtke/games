# Release-Candidate Package Status

## Frozen first-release package set
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

## Excluded packages
- `com.hpr.foundation`: internal support package; missing full external release assets and clean-project proof
- `com.hpr.core`: internal shared-contract package; not productized to the frozen first-release standard
- `com.hpr.input`: internal-only package; missing full external release assets and proof
- `com.hpr.ui`: internal UI support; not productized or isolated for external sale
- `com.hpr.bootstrap`: thin internal bootstrap helper; missing release metadata/docs and not marketed as a standalone product
- `com.hpr.fpsdemo`: game-specific composition/content package; not reusable product code


## Latest 2026-04-01 proof
- release audit: `doc/logs/20260401_095205_release_audit.log`
- dependency audit: `doc/logs/20260401_095205_dependency_audit.log`
- headless validation: `doc/logs/20260401_095205_headless_phase1_validation.log`
- official Asset Store Tools validation root: `doc/logs/asset_store_tools_validation/20260401_110033_*`
- sale-prep report: `doc/package-sale-prep.md`
- tracked sale artifacts: `dist/package_sale_artifacts`

## Historical proof snapshots
### Audit logs
- `doc/logs/20260328_151627_release_audit.log`
- `doc/logs/20260328_151627_dependency_audit.log`
- `doc/logs/20260328_151627_headless_phase1_validation.log`

### Package validation logs
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

### Combination validation logs
- `doc/logs/package_validation/20260328_152148_com_hpr_composition_com_hpr_eventbus_.log`
- `doc/logs/package_validation/20260328_152209_com_hpr_eventbus_com_hpr_stats_.log`
- `doc/logs/package_validation/20260328_152231_com_hpr_inventory_com_hpr_interaction_.log`
- `doc/logs/package_validation/20260328_152253_com_hpr_eventbus_com_hpr_stats_com_hpr_abilities_.log`
- `doc/logs/package_validation/20260328_152315_com_hpr_weapons_com_hpr_ai_com_hpr_world_.log`
- `doc/logs/package_validation/20260328_152337_com_hpr_eventbus_com_hpr_composition_com_hpr_save_com_hpr_stats_com_hpr_inventory_com_hpr_interaction_com_hpr_abilities_com_hpr_weapons_com_hpr_ai_com_hpr_world_.log`

### Game proof
- `doc/logs/20260328_151627_game_build.log`
- `doc/logs/20260328_152347_BuildLinux.log`
- `doc/logs/20260328_151627_game_smoke.log`
- `doc/logs/20260328_152431_smoke_test.log`
