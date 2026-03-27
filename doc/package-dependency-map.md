# Package Dependency Map

## Sale-ready package set
### `com.hpr.eventbus`
- local package dependencies: none
- runtime role: typed publish/subscribe transport
- Unity-specific role: `EventManager` adapter and demo scene only

### `com.hpr.composition`
- local package dependencies: none
- runtime role: explicit service registration and lifecycle orchestration
- Unity-specific role: demo scene and editor validator only

These two packages are the only packages currently designated for external sale.

## Internal package graph still used by the game
Current main game composition still consumes:
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

Scaffold-only/internal packages still present:
- `com.hpr.ui`
- `com.hpr.bootstrap`

## Ownership summary
### Sale-ready ownership
- `com.hpr.eventbus`
  - `IEventBus`
  - `EventBus`
  - `EventManager`
  - `IEventBusSource`
  - `EventBusSourceAdapter`
- `com.hpr.composition`
  - `IService`
  - `IServiceResolver`
  - `IServiceRegistry`
  - `IInitializable`
  - `IUpdatableService`
  - `ServiceRegistry`
  - `CompositionRoot`

### Internal ownership still not ready for external productization
- `com.hpr.core`
  - shared game/runtime contracts
  - current gameplay-domain event payloads
- `com.hpr.fpsdemo`
  - game-specific runtime composition
  - game-specific bootstrap/build flow
  - smoke validation flow
  - scene/content-specific wiring

## Dependency audit truth
Generated audit:
- `doc/dependency-audit-phase1.md`

### Sellable packages
- no forbidden references remain in `com.hpr.eventbus`
- no forbidden references remain in `com.hpr.composition`

### Internal packages still carrying violations
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
- `unity/tools/release/validate_release_candidate.sh`
- `unity/tools/architecture/run_phase1_headless_validation.sh`
- `unity/tools/packages/validate_local_packages.sh com.hpr.eventbus`
- `unity/tools/packages/validate_local_packages.sh com.hpr.composition`
- `unity/tools/packages/validate_local_packages.sh com.hpr.composition com.hpr.eventbus`
- `unity/tools/fps_demo/run_unity_batch.sh SceneBootstrap.BuildLinux`
- `NO_NOTICE=1 unity/tools/fps_demo/smoke_test.sh`
