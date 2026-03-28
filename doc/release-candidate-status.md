# Release-Candidate Package Status

## Sellable package set
This checkpoint designates these packages as the first external release set:
- `com.hpr.eventbus`
- `com.hpr.composition`
- `com.hpr.save`
- `com.hpr.stats`
- `com.hpr.inventory`
- `com.hpr.interaction`
- `com.hpr.abilities`

## Why these packages qualify
### `com.hpr.eventbus`
- standalone runtime API
- standalone package demo scene
- standalone package validator
- clean-project import proof exists
- no forbidden architecture references in release audit
- no third-party distributable art/content included

### `com.hpr.composition`
- standalone runtime API
- standalone package demo scene
- standalone package validator
- clean-project import proof exists
- no forbidden architecture references in release audit
- no third-party distributable art/content included

### `com.hpr.save`
- standalone save-data/runtime contracts
- standalone package demo scene
- standalone package validator
- clean-project import proof exists
- no forbidden architecture references in release audit
- no third-party distributable art/content included

### `com.hpr.stats`
- standalone health/stamina runtime
- standalone package demo scene
- standalone package validator
- clean-project import proof exists
- no forbidden architecture references in release audit
- no third-party distributable art/content included

### `com.hpr.inventory`
- standalone item/inventory runtime
- standalone package demo scene and authored demo item assets
- standalone package validator
- clean-project import proof exists
- no forbidden architecture references in release audit
- no third-party distributable art/content included

### `com.hpr.interaction`
- standalone interaction runtime over explicit interfaces
- standalone package demo scene
- standalone package validator
- clean-project import proof exists
- no forbidden architecture references in release audit
- no third-party distributable art/content included

### `com.hpr.abilities`
- standalone ability runtime over explicit eventbus/stats dependencies
- standalone package demo scene and authored demo data assets
- standalone package validator
- clean-project import proof exists
- no forbidden architecture references in release audit
- no third-party distributable art/content included

## Legal cleanliness statement for this release candidate
Included in the designated sellable packages:
- original authored C# code
- Unity-authored scene metadata generated for package demo scenes
- package-owned demo ScriptableObject assets we authored
- package metadata and documentation we authored

Explicitly not included in sellable packages:
- imported Asset Store art
- third-party models, textures, animations, sounds, fonts, or icons
- local machine paths as functional dependencies

See also:
- `doc/release-audit.md`
- `unity/packages/com.hpr.eventbus/ThirdPartyNotices.md`
- `unity/packages/com.hpr.composition/ThirdPartyNotices.md`
- `unity/packages/com.hpr.save/ThirdPartyNotices.md`
- `unity/packages/com.hpr.stats/ThirdPartyNotices.md`
- `unity/packages/com.hpr.inventory/ThirdPartyNotices.md`
- `unity/packages/com.hpr.interaction/ThirdPartyNotices.md`
- `unity/packages/com.hpr.abilities/ThirdPartyNotices.md`

## Validation entrypoint
- `unity/tools/release/validate_release_candidate.sh`

## Latest successful proof artifacts
- `doc/release-audit.md`
- `doc/dependency-audit-phase1.md`
- `doc/logs/package_validation/20260328_113748_com_hpr_eventbus__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_113817_com_hpr_composition__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_113846_com_hpr_save__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_113915_com_hpr_stats__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_113945_com_hpr_inventory__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_114014_com_hpr_interaction__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_114045_com_hpr_abilities__ValidateInBatch.log`
- `doc/logs/package_validation/20260328_114236_com_hpr_eventbus_com_hpr_composition_com_hpr_save_com_hpr_stats_com_hpr_inventory_com_hpr_interaction_com_hpr_abilities_.log`
- `doc/logs/20260328_114247_BuildLinux.log`
- `/home/hans/.config/unity3d/DefaultCompany/fps_demo/Player.log`

## Still excluded from this release candidate
Everything else in `unity/packages/com.hpr.*` remains internal until it reaches the same proof standard.
