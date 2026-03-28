# Current State

## Frozen first-release package set
- `unity/packages/com.hpr.eventbus`
- `unity/packages/com.hpr.composition`
- `unity/packages/com.hpr.save`
- `unity/packages/com.hpr.stats`
- `unity/packages/com.hpr.inventory`
- `unity/packages/com.hpr.interaction`
- `unity/packages/com.hpr.abilities`
- `unity/packages/com.hpr.weapons`
- `unity/packages/com.hpr.ai`
- `unity/packages/com.hpr.world`

## Excluded packages
- `unity/packages/com.hpr.foundation`: internal support package; missing full external release assets and clean-project proof
- `unity/packages/com.hpr.core`: internal shared-contract package; not productized to the frozen first-release standard
- `unity/packages/com.hpr.input`: internal-only package; missing full external release assets and proof
- `unity/packages/com.hpr.ui`: internal UI support; not productized or isolated for external sale
- `unity/packages/com.hpr.bootstrap`: thin internal bootstrap helper; missing release metadata/docs and not marketed as a standalone product
- `unity/packages/com.hpr.fpsdemo`: game-specific composition/content package; not reusable product code

## Fresh validation proof
### Audits
- `doc/release-audit.md`
- `doc/dependency-audit-phase1.md`
- `doc/logs/20260328_151627_release_audit.log`
- `doc/logs/20260328_151627_dependency_audit.log`
- `doc/logs/20260328_151627_headless_phase1_validation.log`

### Package validation
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
- `doc/logs/package_validation/20260328_152148_com_hpr_composition_com_hpr_eventbus_.log`
- `doc/logs/package_validation/20260328_152209_com_hpr_eventbus_com_hpr_stats_.log`
- `doc/logs/package_validation/20260328_152231_com_hpr_inventory_com_hpr_interaction_.log`
- `doc/logs/package_validation/20260328_152253_com_hpr_eventbus_com_hpr_stats_com_hpr_abilities_.log`
- `doc/logs/package_validation/20260328_152315_com_hpr_weapons_com_hpr_ai_com_hpr_world_.log`
- `doc/logs/package_validation/20260328_152337_com_hpr_eventbus_com_hpr_composition_com_hpr_save_com_hpr_stats_com_hpr_inventory_com_hpr_interaction_com_hpr_abilities_com_hpr_weapons_com_hpr_ai_com_hpr_world_.log`

### Game validation
- `doc/logs/20260328_151627_game_build.log`
- `doc/logs/20260328_152347_BuildLinux.log`
- `doc/logs/20260328_151627_game_smoke.log`
- `doc/logs/20260328_152431_smoke_test.log`

## Runtime bug fixes applied in this run
- `unity/packages/com.hpr.stats/Runtime/ActorStatsComponent.cs`: fixed runtime max-health and max-stamina handling so clamping/regeneration uses effective values, not base values
- `unity/packages/com.hpr.stats/Runtime/DamageableTargetProxy.cs`: added explicit collider-to-damageable binding without parent lookup
- `unity/packages/com.hpr.abilities/Runtime/AbilityRunnerComponent.cs`: removed parent lookup damage resolution; uses direct target or `DamageableTargetProxy`
- `unity/packages/com.hpr.interaction/Runtime/InteractionSensor.cs`: removed hierarchy lookup and implicit camera-child discovery; uses explicit camera binding and optional `InteractionTargetProxy`
- `unity/packages/com.hpr.interaction/Runtime/InteractionTargetProxy.cs`: added explicit collider-to-interactable binding without parent lookup
- `unity/tools/fps_demo/smoke_test.sh`: now copies smoke proof into `doc/logs/`
- `unity/tools/release/validate_release_candidate.sh`: now writes top-level proof logs into `doc/logs/`

## Ownership rule
Everything under `/data/src/github/games` must be owned by `hans`.
