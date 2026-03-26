# Modularization Status

## Checkpoint
The repo is in an intermediate package-split checkpoint. The main game still composes through `com.hpr.fpsdemo`, but shared event/input/core contracts have started moving into dedicated packages.

## Package layout now present
- `unity/packages/com.hpr.foundation` - existing utility package
- `unity/packages/com.hpr.fpsdemo` - current composition-heavy gameplay package
- `unity/packages/com.hpr.core` - shared service contracts and future neutral runtime types
- `unity/packages/com.hpr.eventbus` - extracted event manager and gameplay event payloads
- `unity/packages/com.hpr.input` - extracted options/binding/input abstractions
- `unity/packages/com.hpr.stats` - scaffold package
- `unity/packages/com.hpr.inventory` - scaffold package
- `unity/packages/com.hpr.weapons` - scaffold package
- `unity/packages/com.hpr.ai` - scaffold package
- `unity/packages/com.hpr.interaction` - scaffold package
- `unity/packages/com.hpr.ui` - scaffold package
- `unity/packages/com.hpr.world` - scaffold package
- `unity/packages/com.hpr.bootstrap` - scaffold package

## What was extracted in this checkpoint
- `EventManager` moved from `com.hpr.fpsdemo` to `com.hpr.eventbus`
- `GameEvents` moved from `com.hpr.fpsdemo` to `com.hpr.eventbus`
- `GameAction`, `GameOptionsData`, `GameOptionsStore` moved from `com.hpr.fpsdemo` to `com.hpr.input`
- shared service interfaces moved into `com.hpr.core/Runtime/Services/GameplayServiceContracts.cs`
- `IEventBusSource` added in `com.hpr.eventbus`
- `IInputSource`, `IInputBindingsSource`, `IOptionsController` live in `com.hpr.input`

## Runtime decoupling completed in this checkpoint
These systems no longer depend on `GameManager.Instance` and are bound through interfaces from the composition layer:
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

## Composition layer still left to split further
These are still composition-heavy and should be the next extraction targets:
- `GameManager`
- `SceneBootstrap`
- `GameStateValidator`
- most editor/import integration code in `com.hpr.fpsdemo/Editor`
- save data types in `com.hpr.fpsdemo/Runtime/Core/SaveData.cs`
- gameplay interfaces in `com.hpr.fpsdemo/Runtime/Core/GameplayInterfaces.cs`

## Validation result at this checkpoint
Verified as `hans`:
- `unity/tools/fps_demo/run_unity_batch.sh SceneBootstrap.BuildLinux` succeeds
- `unity/tools/fps_demo/smoke_test.sh` succeeds
- project stays writable by `hans`

## Known intermediate-state limitations
- package scaffold demos are placeholders, not real standalone demo scenes yet
- `com.hpr.fpsdemo` is still too large to be considered a thin composition-only package
- scaffold packages still contain marker classes only until systems are moved into them
- `SceneBootstrap` still knows about the current game scene and hierarchy
- imported Asset Store content remains local-only and untracked by design

## Practical next steps
1. move save contracts and generic runtime interfaces into `com.hpr.core`
2. split inventory/weapons/stats/world/AI runtime classes out of `com.hpr.fpsdemo`
3. create per-package standalone demo scenes and smoke entry points
4. shrink `com.hpr.fpsdemo` to composition/bootstrap glue only
5. update docs again after each stable buildable checkpoint
