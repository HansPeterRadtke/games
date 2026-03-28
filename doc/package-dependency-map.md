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

### `com.hpr.save`
- local package dependencies: none
- runtime role: serializable save wrappers and `ISaveableEntity`
- Unity-specific role: demo scene and editor validator only

### `com.hpr.stats`
- local package dependencies: `com.hpr.eventbus`
- runtime role: reusable health/stamina and damage-event handling
- Unity-specific role: demo scene and editor validator only

### `com.hpr.inventory`
- local package dependencies: none
- runtime role: item definitions and stack-based inventory runtime
- Unity-specific role: demo scene and editor validator only

### `com.hpr.interaction`
- local package dependencies: `com.hpr.eventbus`, `com.hpr.inventory`
- runtime role: interaction contracts, interaction sensing, pickups, keyed doors
- Unity-specific role: demo scene and editor validator only

### `com.hpr.abilities`
- local package dependencies: `com.hpr.eventbus`, `com.hpr.stats`
- runtime role: ability data, runtime activation, and event publication
- Unity-specific role: demo scene and editor validator only

These seven packages are the packages currently designated for external sale.

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
- `com.hpr.save`
  - `SerializableVector3`
  - `SerializableQuaternion`
  - `SaveEntityData`
  - `ISaveableEntity`
- `com.hpr.stats`
  - `IDamageable`
  - `ICharacterStats`
  - `DamageEvent`
  - `ActorStatsComponent`
- `com.hpr.inventory`
  - `ItemData`
  - `ItemType`
  - `IInventoryService`
  - `ItemPickedEvent`
  - `InventoryComponent`
- `com.hpr.interaction`
  - `IInteractionActor`
  - `IInteractable`
  - `InteractionSensor`
  - `InventoryPickupInteractable`
  - `KeyDoorInteractable`
- `com.hpr.abilities`
  - `AbilityData`
  - `AbilityEffectData`
  - `IAbilityLoadout`
  - `IAbilityResourcePool`
  - `AbilityRunnerComponent`
  - ability events

### Internal ownership still not ready for external productization
- `com.hpr.core`
  - internal shared game/runtime contracts still being thinned
- `com.hpr.fpsdemo`
  - game-specific runtime composition
  - game-specific bootstrap/build flow
  - smoke validation flow
  - scene/content-specific wiring
- `com.hpr.weapons`, `com.hpr.ai`, `com.hpr.world`, `com.hpr.input`, `com.hpr.ui`, `com.hpr.bootstrap`
  - still internal until they meet the same standalone proof bar

## Dependency audit truth
Generated audit:
- `doc/dependency-audit-phase1.md`

### Sellable packages
- no forbidden references remain in the seven-package release set

### Internal packages still carrying violations
- `com.hpr.fpsdemo`
  - `GameManager` references
  - `SceneBootstrap` references
  - parent `MonoBehaviour` service lookup fallbacks

## Verified validation points
- `unity/tools/release/validate_release_candidate.sh`
- `unity/tools/architecture/run_phase1_headless_validation.sh`
- `unity/tools/packages/validate_local_packages.sh com.hpr.eventbus`
- `unity/tools/packages/validate_local_packages.sh com.hpr.composition`
- `unity/tools/packages/validate_local_packages.sh com.hpr.save`
- `unity/tools/packages/validate_local_packages.sh com.hpr.stats`
- `unity/tools/packages/validate_local_packages.sh com.hpr.inventory`
- `unity/tools/packages/validate_local_packages.sh com.hpr.interaction`
- `unity/tools/packages/validate_local_packages.sh com.hpr.abilities`
- `unity/tools/packages/validate_local_packages.sh com.hpr.composition com.hpr.eventbus`
- `unity/tools/packages/validate_local_packages.sh com.hpr.eventbus com.hpr.stats`
- `unity/tools/packages/validate_local_packages.sh com.hpr.inventory com.hpr.interaction`
- `unity/tools/packages/validate_local_packages.sh com.hpr.eventbus com.hpr.stats com.hpr.abilities`
- `unity/tools/packages/validate_local_packages.sh com.hpr.eventbus com.hpr.composition com.hpr.save com.hpr.stats com.hpr.inventory com.hpr.interaction com.hpr.abilities`
- `unity/tools/fps_demo/run_unity_batch.sh SceneBootstrap.BuildLinux`
- `NO_NOTICE=1 unity/tools/fps_demo/smoke_test.sh`
