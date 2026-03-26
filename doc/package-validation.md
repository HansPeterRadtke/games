# Package Validation

## Validation helper
Use:
- `unity/tools/packages/validate_local_packages.sh <package-name>`

The helper creates a clean temporary Unity project, resolves declared local package dependencies, symlinks only those packages into the temp project, and batch-runs Unity to confirm compile/import health.
Each invocation now uses its own temp project path by default, so multiple package validations can run concurrently without tripping Unity project-lock errors.

## Latest validated packages
Validated on 2026-03-26:
- `com.hpr.core`
- `com.hpr.eventbus`
- `com.hpr.input`
- `com.hpr.save`
- `com.hpr.inventory`
- `com.hpr.weapons`
- `com.hpr.ai`
- `com.hpr.stats`
- `com.hpr.world`
- `com.hpr.fpsdemo`

## Log locations
Validation logs are written to:
- `doc/logs/package_validation/`

Relevant recent logs:
- `20260326_100057_com_hpr_core_.log`
- `20260326_100137_com_hpr_eventbus_.log`
- `20260326_100205_com_hpr_input_.log`
- `20260326_100236_com_hpr_save_.log`
- `20260326_102012_com_hpr_inventory_.log`
- `20260326_102427_com_hpr_weapons_.log`
- `20260326_102755_com_hpr_ai_.log`
- `20260326_104044_com_hpr_stats_.log`
- `20260326_120926_com_hpr_stats_.log`
- `20260326_142342_com_hpr_eventbus_.log`
- `20260326_142424_com_hpr_inventory_.log`
- `20260326_115137_com_hpr_world_.log`
- `20260326_115201_com_hpr_fpsdemo_.log`

## Current meaning of a pass
A passing validation currently proves:
- the package and its declared local package dependencies import into an empty Unity project
- Unity script compilation succeeds
- no missing-reference compile failures occur during batch import

It does not yet prove:
- standalone demo scene quality
- package-specific runtime behavior correctness
- Asset Store submission readiness

## Demo-specific validation
- Stats demo scene generation was validated via `unity/tools/fps_demo/run_unity_batch.sh StatsDemoSceneBuilder.BuildDemoScene`.
- Event bus demo scene generation was validated via `unity/tools/fps_demo/run_unity_batch.sh EventBusDemoSceneBuilder.BuildDemoScene`.
- Inventory demo scene generation was validated via `unity/tools/fps_demo/run_unity_batch.sh InventoryDemoSceneBuilder.BuildDemoScene`.
