# Package Validation

## Validation helper
Use:
- `unity/tools/packages/validate_local_packages.sh <package-name>`

The helper creates a clean temporary Unity project, resolves declared local package dependencies, symlinks only those packages into the temp project, and batch-runs Unity to confirm compile/import health.

## Latest validated packages
Validated on 2026-03-26:
- `com.hpr.core`
- `com.hpr.eventbus`
- `com.hpr.input`
- `com.hpr.save`
- `com.hpr.inventory`
- `com.hpr.weapons`
- `com.hpr.ai`
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
- `20260326_102812_com_hpr_fpsdemo_.log`

## Current meaning of a pass
A passing validation currently proves:
- the package and its declared local package dependencies import into an empty Unity project
- Unity script compilation succeeds
- no missing-reference compile failures occur during batch import

It does not yet prove:
- standalone demo scene quality
- package-specific runtime behavior correctness
- Asset Store submission readiness
