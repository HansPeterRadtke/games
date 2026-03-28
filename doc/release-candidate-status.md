# Release-Candidate Package Status

## Selected first-release package set
The first external release candidate is:
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

## Why this is the strongest realistic first release from the current repo
This set is stronger than the earlier infrastructure-only release set because these packages now meet the same product bar:
- package metadata is complete
- package-owned demo content exists
- package-owned batch validators exist
- clean-project import validation exists
- release audit covers them
- dependency audit covers them
- no selected package depends on `com.hpr.fpsdemo`, `GameManager`, `SceneBootstrap`, or local-only art content

## Fresh proof for this release candidate
### Audits
- `doc/release-audit.md`
- `doc/dependency-audit-phase1.md`

### Standalone package validation
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

### Combined package-set validation
- `doc/logs/package_validation/20260328_125814_com_hpr_composition_com_hpr_eventbus_.log`
- `doc/logs/package_validation/20260328_125835_com_hpr_eventbus_com_hpr_stats_.log`
- `doc/logs/package_validation/20260328_125856_com_hpr_inventory_com_hpr_interaction_.log`
- `doc/logs/package_validation/20260328_125918_com_hpr_eventbus_com_hpr_stats_com_hpr_abilities_.log`
- `doc/logs/package_validation/20260328_125940_com_hpr_weapons_com_hpr_ai_com_hpr_world_.log`
- `doc/logs/package_validation/20260328_130003_com_hpr_eventbus_com_hpr_composition_com_hpr_save_com_hpr_stats_com_hpr_inventory_com_hpr_interaction_com_hpr_abilities_com_hpr_weapons_com_hpr_ai_com_hpr_world_.log`

### Game proof
- `doc/logs/20260328_130012_BuildLinux.log`
- `/home/hans/.config/unity3d/DefaultCompany/fps_demo/Player.log`

## Excluded packages
Still excluded from the first release:
- `com.hpr.foundation`
- `com.hpr.core`
- `com.hpr.input`
- `com.hpr.ui`
- `com.hpr.bootstrap`
- `com.hpr.fpsdemo`

Reason for exclusion:
- these packages are still internal support or game-specific composition layers
- they are not yet at the same standalone/documented/validated proof standard
