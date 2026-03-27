# Package Validation

## Validation helpers
Use:
- `unity/tools/packages/validate_local_packages.sh <package-name>`
- `unity/tools/architecture/run_phase1_headless_validation.sh`

The Unity package validator creates a clean temporary Unity project, resolves declared local package dependencies, symlinks only those packages into the temp project, and batch-runs Unity to confirm compile/import health.
Each invocation uses its own temp project path by default, so multiple validations can run concurrently without Unity project-lock collisions.

The headless phase-one validator is separate. It proves that `com.hpr.composition` and `com.hpr.eventbus` work outside Unity scene bootstrapping.

## Latest verified validations
Verified through 2026-03-27:
- headless:
  - `unity/tools/architecture/run_phase1_headless_validation.sh`
- clean-project package validation:
  - `com.hpr.eventbus`
  - `com.hpr.composition`
- full project:
  - `unity/tools/fps_demo/run_unity_batch.sh SceneBootstrap.BuildLinux`
  - `NO_NOTICE=1 unity/tools/fps_demo/smoke_test.sh`

## Log locations
- package validation logs: `doc/logs/package_validation/`
- Unity batch logs: `doc/logs/`

Relevant current logs:
- `doc/logs/package_validation/20260327_165749_com_hpr_eventbus_.log`
- `doc/logs/package_validation/20260327_165859_com_hpr_composition_.log`
- `doc/logs/20260327_170846_BuildLinux.log`

## Current meaning of a pass
### Headless phase-one validator proves
- `CompositionRoot` initializes and disposes services without scene wiring
- `EventBus` supports typed publish/subscribe
- base-type subscription delivery works
- disposed subscriptions stop receiving events

### Clean-project package validation proves
- the package and its declared local package dependencies import into an empty Unity project
- Unity script compilation succeeds
- there are no package-resolution or missing-reference compile failures

### Full project build + smoke proves
- the composition project still builds after the modularization changes
- the runtime smoke path still completes after the composition/eventbus split

## What this still does not prove
- Asset Store submission readiness of every package
- complete elimination of `fpsdemo` dependency violations
- standalone demo quality for every package
