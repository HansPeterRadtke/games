# HPR Interaction

Reusable first-person interaction flow for pickups, keyed doors, and custom world objects.

## Audience
Use this package when you want:
- a generic `IInteractionActor` / `IInteractable` contract pair
- a camera-based `InteractionSensor` for probing and executing interactions
- ready-made inventory pickup and keyed-door interactables

## Included
- `IInteractionActor`
- `IInteractable`
- `InteractionSensor`
- `InteractionTargetProxy`
- `InventoryPickupInteractable`
- `KeyDoorInteractable`
- `SimpleInteractionActor`

## Unity version
- tested with Unity `6000.4` (`6000.4.0f1`)
- intended minimum Unity editor version: `6000.4`

## Dependencies
- `com.hpr.eventbus`
- `com.hpr.inventory`

## Installation
1. Add `com.hpr.interaction`, `com.hpr.inventory`, and `com.hpr.eventbus` to your project.
2. Reference `HPR.Interaction.Runtime` from dependent asmdefs.
3. Implement `IInteractionActor` or use `SimpleInteractionActor` for basic setups.
4. Add `InteractionSensor` and bind a camera explicitly.
5. Add `IInteractable` components to world objects.
6. If a collider lives on a child object, add `InteractionTargetProxy` to that collider and bind the actual interactable explicitly.

## Quick start
```csharp
var actor = playerRoot.AddComponent<SimpleInteractionActor>();
var sensor = playerRoot.AddComponent<InteractionSensor>();
sensor.BindCamera(playerCamera);

if (sensor.TryInteract(actor))
{
    UnityEngine.Debug.Log(sensor.CurrentPrompt);
}
```

## API overview
- `InteractionSensor.Probe(...)` caches the current prompt and interactable target
- `InteractionSensor.TryInteract(...)` executes the active target if one is available
- `InteractionTargetProxy` lets child colliders resolve an explicit `IInteractable` target without parent lookups
- `InventoryPickupInteractable` adds `ItemData` into an `IInventoryService` and can publish `ItemPickedEvent`
- `KeyDoorInteractable` toggles a door leaf and optionally requires a key item id

## Demo
- Scene: `Packages/com.hpr.interaction/Demo/InteractionDemo.unity`
- Builder: `InteractionDemoSceneBuilder.BuildDemoScene`
- Batch validator: `InteractionPackageValidator.ValidateInBatch`

## Validation
- Unity batch mode:
  - `Unity -batchmode -projectPath <your-project> -executeMethod InteractionPackageValidator.ValidateInBatch -quit`
- repository helper (used inside this repo):
  - `EXECUTE_METHOD=InteractionPackageValidator.ValidateInBatch unity/tools/packages/validate_local_packages.sh com.hpr.interaction`

## Extension points
- implement your own `IInteractable` behaviors for terminals, switches, dialogue, or loot containers
- implement your own `IInteractionActor` if your project uses a custom inventory service bridge
- bind `InventoryPickupInteractable` to any explicit `IEventBusSource` without hierarchy-based service lookup

## Limitations
- this package does not provide a full HUD prompt renderer
- input polling is demo-only; production projects should trigger `TryInteract(...)` from their own input layer
