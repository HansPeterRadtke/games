# Package Dependency Map

## Main game package graph
Current verified graph for `unity/projects/fps_demo`:
- `com.hpr.foundation`
- `com.hpr.core`
- `com.hpr.composition`
- `com.hpr.eventbus`
- `com.hpr.input`
- `com.hpr.save`
- `com.hpr.inventory`
- `com.hpr.weapons`
- `com.hpr.ai`
- `com.hpr.stats`
- `com.hpr.world`
- `com.hpr.abilities`
- `com.hpr.interaction`
- `com.hpr.fpsdemo`

Scaffold-only packages still present but not yet populated with real runtime code:
- `com.hpr.ui`
- `com.hpr.bootstrap`

## Extracted responsibilities

### `com.hpr.core`
Generic service contracts plus current gameplay-domain event payloads.
Current contents include:
- gameplay/menu/flow service contracts
- status/prompt/HUD sink contracts
- player-death and runtime service contracts
- `GameplayEvents.cs`

### `com.hpr.composition`
Explicit composition only.
Current contents:
- `IService`
- `IServiceResolver`
- `IServiceRegistry`
- `IInitializable`
- `IUpdatableService`
- `ServiceRegistry`
- `CompositionRoot`

### `com.hpr.eventbus`
Generic event transport only.
Current contents:
- `IEventBus`
- `EventBus`
- `EventManager`
- `IEventBusSource`
- `EventBusSourceAdapter`

### `com.hpr.input`
Input abstraction and settings/binding storage.

### `com.hpr.save`
Generic save payload types and save contracts.

### `com.hpr.inventory`
Generic item definitions and inventory runtime.

### `com.hpr.weapons`
Weapon definitions and weapon metadata.

### `com.hpr.ai`
Enemy definitions and AI metadata.

### `com.hpr.stats`
Reusable actor stats runtime.

### `com.hpr.abilities`
Reusable ability/effect runtime.

### `com.hpr.interaction`
Reusable interaction contracts and interaction runtime.

### `com.hpr.fpsdemo`
Still owns project-specific composition-heavy runtime and editor tooling.
Current contents still include:
- `GameManager`
- `SceneBootstrap`
- `GameStateValidator`
- player/world/combat runtime wiring
- project-specific smoke flow

## Phase-one dependency violations
Generated audit:
- `doc/dependency-audit-phase1.md`

Primary remaining violations:
- `com.hpr.fpsdemo`
  - `GameManager` references
  - `SceneBootstrap` references
  - parent `MonoBehaviour` service lookup fallbacks
- `com.hpr.interaction`
  - demo/runtime lookup fallbacks
- `com.hpr.inventory`
  - demo scene search fallback
- `com.hpr.stats`
  - parent lookup fallback

## Verified validation points
- `unity/tools/architecture/run_phase1_headless_validation.sh`
- `unity/tools/packages/validate_local_packages.sh com.hpr.eventbus`
- `unity/tools/packages/validate_local_packages.sh com.hpr.composition`
- `unity/tools/fps_demo/run_unity_batch.sh SceneBootstrap.BuildLinux`
- `NO_NOTICE=1 unity/tools/fps_demo/smoke_test.sh`

## Next extraction targets
1. remove runtime parent-service discovery from `fpsdemo`
2. move more shared runtime from `fpsdemo` into package-owned modules
3. reduce `com.hpr.core` gameplay-event ownership where domain packages can own their own event payloads cleanly
4. keep `fpsdemo` as composition-only glue
