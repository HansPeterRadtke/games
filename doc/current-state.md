# Current State

## Repository structure
`games` contains:
- the playable Unity project: `unity/projects/fps_demo`
- package products and internal packages: `unity/packages/com.hpr.*`
- build/audit/release tooling: `unity/tools/`
- architecture/release docs: `doc/`

## Chosen first-release package set
The current strongest realistic first external release set is:
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

These packages are the current release target because they now have package-owned demos, package-owned validators, explicit manifests, external-user readmes, clean-project validation workflows, and fresh proof that they validate together.

## Packages explicitly excluded from the first release
These packages remain internal in this checkpoint:
- `unity/packages/com.hpr.foundation`
- `unity/packages/com.hpr.core`
- `unity/packages/com.hpr.input`
- `unity/packages/com.hpr.ui`
- `unity/packages/com.hpr.bootstrap`
- `unity/packages/com.hpr.fpsdemo`

Reason for exclusion:
- they are still internal composition/support layers
- or they still carry game-specific ownership
- or they are not yet productized to the same standalone proof standard as the selected release set

## Architecture reality
### First-release packages
- `com.hpr.eventbus`: typed event transport and Unity adapter
- `com.hpr.composition`: explicit service registration and lifecycle composition
- `com.hpr.save`: generic save contracts and runtime helpers
- `com.hpr.stats`: reusable health/stamina/runtime-state logic
- `com.hpr.inventory`: reusable item definitions and inventory container runtime
- `com.hpr.interaction`: reusable interaction contracts and inventory/door interaction runtime
- `com.hpr.abilities`: reusable ability/effect runtime over explicit dependencies
- `com.hpr.weapons`: reusable weapon-definition data package
- `com.hpr.ai`: reusable enemy/archetype definition data package
- `com.hpr.world`: reusable asset metadata and registry package

### Internal game layer
- `com.hpr.fpsdemo` remains the game-specific composition/content layer
- the game still proves that the reusable packages compose back into a working project

## Local-only content rule
Not committed and not sale-safe:
- imported Asset Store folders
- downloaded `.unitypackage` files
- local art integration outputs
- Unity `Library`, `Temp`, `Logs`, and build output

The local asset inventory is documented in `doc/local-assets.md`.

## Fresh proof from the current release pass
- release audit: `doc/release-audit.md`
- dependency audit: `doc/dependency-audit-phase1.md`
- full-set import validation: `doc/logs/package_validation/20260328_130003_com_hpr_eventbus_com_hpr_composition_com_hpr_save_com_hpr_stats_com_hpr_inventory_com_hpr_interaction_com_hpr_abilities_com_hpr_weapons_com_hpr_ai_com_hpr_world_.log`
- game build: `doc/logs/20260328_130012_BuildLinux.log`
- game smoke: `/home/hans/.config/unity3d/DefaultCompany/fps_demo/Player.log`

## Ownership rule
Everything under this repo must be writable by `hans`. Root-owned files are a defect.
