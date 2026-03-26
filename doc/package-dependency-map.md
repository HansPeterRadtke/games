# Package Dependency Map

## Main game package graph
Current verified graph for `unity/projects/fps_demo`:
- `com.hpr.foundation`
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

Scaffold-only packages still present but not yet populated with real runtime code:
- `com.hpr.stats`
- `com.hpr.interaction`
- `com.hpr.ui`
- `com.hpr.world`
- `com.hpr.bootstrap`

## Extracted responsibilities

### com.hpr.core
Generic composition/service contracts only.
Current contents:
- gameplay state contracts
- menu/flow command contracts
- status/prompt/HUD sink contracts
- player death contract

### com.hpr.eventbus
Event dispatch infrastructure and current gameplay-domain payloads.
Current contents:
- `IGameEventBus`
- `EventManager`
- gameplay event payloads from the FPS prototype
- `IEventBusSource`

### com.hpr.input
Input abstraction and settings/binding storage.
Current contents:
- `GameAction`
- `GameOptionsData`
- `GameOptionsStore`
- `IInputSource`
- `IInputBindingsSource`
- `IOptionsController`
- `UnityInputSource`

### com.hpr.save
Generic save payload types and save contracts.
Current contents:
- serializable vector/quaternion wrappers
- player/entity save payloads
- inventory and weapon save payloads
- `ISaveableEntity`

### com.hpr.inventory
Real standalone data/runtime package now in use by the game.
Current contents:
- `ItemData`
- `ItemType`
- `IInventoryService`
- `InventoryComponent`

### com.hpr.weapons
Real standalone data package now in use by the game.
Current contents:
- `WeaponData`
- `FireModeType`
- `EquipmentKind`
- `WeaponUtilityAction`

### com.hpr.ai
Real standalone data package now in use by the game.
Current contents:
- `EnemyData`
- `EnemyAIType`
- `EnemyAttackStyle`

### com.hpr.fpsdemo
Still owns composition-heavy gameplay runtime and editor tooling.
Current contents still include:
- `GameManager`
- `SceneBootstrap`
- `GameStateValidator`
- player, weapon, enemy, pickup, and door runtime code
- asset metadata/registry support
- project-specific editor/bootstrap/integration logic

## Runtime decoupling already completed
These systems no longer use `GameManager.Instance` and bind through interfaces or the event bus:
- `PlayerController`
- `PlayerGameplayController`
- `PlayerStats`
- `WeaponSystem`
- `WeaponFireModes`
- `PhysicsProjectile`
- `PickupItem`
- `DoorController`
- `EnemyAgent`
- `GameUiController`

## Clean-project validations already passing
Validated in an empty Unity project through `unity/tools/packages/validate_local_packages.sh`:
- `com.hpr.core`
- `com.hpr.eventbus`
- `com.hpr.input`
- `com.hpr.save`
- `com.hpr.inventory`
- `com.hpr.weapons`
- `com.hpr.ai`
- `com.hpr.stats`
- `com.hpr.world`
- `com.hpr.fpsdemo` (with declared dependencies)

Logs are in `doc/logs/package_validation/`.

## Remaining high-value extraction targets

### Move from fpsdemo to stats
Candidates:
- generic health/stamina contracts currently in `GameplayInterfaces.cs`
- `PlayerStats` or a generic replacement component

### Move from fpsdemo to weapons
Candidates:
- `WeaponSystem`
- `WeaponFireModes`
- `PhysicsProjectile`
- weapon runtime state and loadout contracts

### Move from fpsdemo to ai
Candidates:
- `EnemyAgent`
- `EnemyBehaviors`
- generic targeting/agent behavior contracts

### Move from fpsdemo to interaction
Candidates:
- `IInteractable` once the actor contract is generalized
- generalized `DoorController` and `PickupItem` logic stripped of project assumptions

### Keep in fpsdemo or move to bootstrap later
Likely composition-specific:
- `GameManager`
- `SceneBootstrap`
- current world composition/editor scene wiring
- game-specific smoke validation flow
- third-party asset placement workflow

## Known dependency cleanliness gaps
- `SceneBootstrap` still hardcodes the current project scene and hierarchy
- event payloads in `com.hpr.eventbus` are still FPS-domain payloads, not purely generic bus infrastructure
- several packages still lack real demo scenes and module-specific tests
- `com.hpr.fpsdemo` remains the composition-heavy package and is not store-ready
