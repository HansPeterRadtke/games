# Modularization Status

## Checkpoint
The repo is in a buildable intermediate package-productization checkpoint. The main game still composes through `com.hpr.fpsdemo`, but several real standalone packages now compile and validate independently in clean projects.

## Real packages in use
- `unity/packages/com.hpr.foundation` - shared low-level utilities
- `unity/packages/com.hpr.core` - generic service contracts
- `unity/packages/com.hpr.eventbus` - event bus infrastructure and current gameplay payloads
- `unity/packages/com.hpr.input` - input abstraction and settings storage
- `unity/packages/com.hpr.save` - save payload types and save contracts
- `unity/packages/com.hpr.inventory` - item definitions and generic inventory runtime
- `unity/packages/com.hpr.weapons` - weapon definitions and fire-mode metadata
- `unity/packages/com.hpr.ai` - enemy definitions and AI metadata
- `unity/packages/com.hpr.stats` - reusable actor stats runtime and demo scene
- `unity/packages/com.hpr.world` - generic asset metadata and registry types
- `unity/packages/com.hpr.interaction` - reusable interaction contracts, sensors, pickups, keyed doors, and standalone demo
- `unity/packages/com.hpr.fpsdemo` - current composition-heavy gameplay package

## Scaffold packages still to populate
- `unity/packages/com.hpr.ui`
- `unity/packages/com.hpr.bootstrap`

## What was extracted in this checkpoint series
- `EventManager` moved from `com.hpr.fpsdemo` to `com.hpr.eventbus`
- `GameEvents` moved from `com.hpr.fpsdemo` to `com.hpr.eventbus`
- `GameAction`, `GameOptionsData`, `GameOptionsStore` moved from `com.hpr.fpsdemo` to `com.hpr.input`
- generic save payloads moved from `com.hpr.fpsdemo` to `com.hpr.save`
- `ItemData`, `ItemType`, `IInventoryService`, and `InventoryComponent` moved into `com.hpr.inventory`
- `WeaponData`, `FireModeType`, `EquipmentKind`, and `WeaponUtilityAction` moved into `com.hpr.weapons`
- `EnemyData`, `EnemyAIType`, and `EnemyAttackStyle` moved into `com.hpr.ai`

## Runtime decoupling completed
These systems no longer depend on `GameManager.Instance` and bind through interfaces/services instead:
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

## Validation result at this checkpoint
Verified as `hans`:
- `unity/tools/fps_demo/run_unity_batch.sh SceneBootstrap.BuildLinux` succeeds
- `unity/tools/fps_demo/smoke_test.sh` succeeds
- clean-project validation succeeds for:
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

## Demo progress
- `com.hpr.stats` now has a committed standalone demo scene: `unity/packages/com.hpr.stats/Demo/StatsDemo.unity`
- `com.hpr.eventbus` now includes `EventBusSourceAdapter` to make standalone package demos easier to compose
- `com.hpr.eventbus` now has a committed standalone demo scene: `unity/packages/com.hpr.eventbus/Demo/EventBusDemo.unity`
- `com.hpr.inventory` now has a committed standalone demo scene: `unity/packages/com.hpr.inventory/Demo/InventoryDemo.unity`
- `com.hpr.interaction` now has a committed standalone demo scene: `unity/packages/com.hpr.interaction/Demo/InteractionDemo.unity`

## Remaining work before store-ready modularity
- move generic stats contracts/runtime out of `com.hpr.fpsdemo`
- move weapon runtime execution out of `com.hpr.fpsdemo` into `com.hpr.weapons`
- move AI runtime behavior out of `com.hpr.fpsdemo` into `com.hpr.ai`
- reduce `com.hpr.eventbus` to generic bus + cleaner domain event separation
- create real demo scenes and tests per package
- shrink `com.hpr.fpsdemo` to project composition/bootstrap only

## Known intermediate-state limitations
- only `com.hpr.stats`, `com.hpr.eventbus`, and `com.hpr.inventory` currently have real standalone demo scenes
- `SceneBootstrap` still knows about the current game scene and hierarchy
- `com.hpr.fpsdemo` is still too large to be considered thin composition-only glue
- imported Asset Store content remains local-only and untracked by design


## Game-content checkpoint on top of the package split
- `com.hpr.fpsdemo` now owns authored quest/dialogue/journal composition without leaking those project-specific systems into reusable packages.
- `QuestManager` subscribes to package events (`ItemPickedEvent`, `EnemyKilledEvent`, `DialogueCompletedEvent`) and persists quest state through `com.hpr.save`.
- Dialogue-aware NPC interactions are now composed through `com.hpr.interaction` and `IDialogueFlowCommands`, keeping the reusable interaction package generic.
- The smoke path now validates quest acceptance, quest completion, journal visibility, skill-point rewards, and save/load after progression.
