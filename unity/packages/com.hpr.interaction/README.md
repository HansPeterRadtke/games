# HPR Interaction

Reusable interaction contracts and simple runtime components for Unity projects.

## What it provides
- generic `IInteractionActor` and `IInteractable` contracts
- `InteractionSensor` for prompt probing and interaction execution
- `InventoryPickupInteractable` for inventory-backed pickups
- `KeyDoorInteractable` for keyed open/close interactions
- standalone demo scene and builder

## Dependencies
- `com.hpr.foundation`
- `com.hpr.core`
- `com.hpr.eventbus`
- `com.hpr.inventory`

## Setup
1. Add the package to a Unity project.
2. For inventory-backed actors, put `InventoryComponent` on the actor root.
3. Add `SimpleInteractionActor` or your own `IInteractionActor` implementation.
4. Add `InteractionSensor` and bind a camera.
5. Add `IInteractable` components to world objects.

## API overview
- `IInteractionActor`: exposes the actor transform and inventory service.
- `IInteractable`: prompt + interaction contract.
- `InteractionSensor`: probes forward from a camera and caches the active prompt/target.
- `InventoryPickupInteractable`: adds `ItemData` into inventory and publishes `ItemPickedEvent`.
- `KeyDoorInteractable`: toggles a door leaf and optionally requires an inventory key item.

## Demo
- build/open `Packages/com.hpr.interaction/Demo/InteractionDemo.unity`
- or use `HPR/Interaction/Build Demo Scene`

The demo uses simple primitives only and is safe to distribute.
