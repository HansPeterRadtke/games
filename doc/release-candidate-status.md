# Release-Candidate Package Status

## Sellable package set
This checkpoint designates exactly two packages as release-candidate quality:
- `com.hpr.eventbus`
- `com.hpr.composition`

No other package in the repo should currently be treated as upload-ready.

## Why these two qualify
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

## Legal cleanliness statement for this release candidate
Included in the designated sellable packages:
- original authored C# code
- Unity-authored scene metadata generated for package demo scenes
- package metadata and documentation we authored

Explicitly not included in sellable packages:
- imported Asset Store art
- third-party models, textures, animations, sounds, fonts, or icons
- local machine paths as functional dependencies

See also:
- `unity/packages/com.hpr.eventbus/ThirdPartyNotices.md`
- `unity/packages/com.hpr.composition/ThirdPartyNotices.md`
- `doc/release-audit.md`

## Validation entrypoint
- `unity/tools/release/validate_release_candidate.sh`

## Latest successful proof artifacts
- `doc/release-audit.md`
- `doc/dependency-audit-phase1.md`
- `doc/logs/package_validation/20260327_194854_com_hpr_eventbus__ValidateInBatch.log`
- `doc/logs/package_validation/20260327_195023_com_hpr_composition__ValidateInBatch.log`
- `doc/logs/package_validation/20260327_195113_com_hpr_composition_com_hpr_eventbus_.log`
- `doc/logs/20260327_195141_BuildLinux.log`
- `/home/hans/.config/unity3d/DefaultCompany/fps_demo/Player.log`

## Still excluded from this release candidate
Everything else in `unity/packages/com.hpr.*` remains internal until it reaches the same proof standard.
