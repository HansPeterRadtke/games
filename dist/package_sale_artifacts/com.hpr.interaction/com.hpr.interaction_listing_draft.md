# HPR Interaction Asset Store Listing Draft

## Title
HPR Interaction

## Short description
Reusable interaction flow for pickups, keyed doors, and custom world objects.

## Long description
Reusable first-person interaction flow for pickups, keyed doors, and custom world objects.

Use this package when you want:
- a generic `IInteractionActor` / `IInteractable` contract pair
- a camera-based `InteractionSensor` for probing and executing interactions
- ready-made inventory pickup and keyed-door interactables

Included:
- `IInteractionActor`
- `IInteractable`
- `InteractionSensor`
- `InteractionTargetProxy`
- `InventoryPickupInteractable`
- `KeyDoorInteractable`
- `SimpleInteractionActor`

Installation summary:
- Add `com.hpr.interaction`, `com.hpr.inventory`, and `com.hpr.eventbus` to your project.
- Reference `HPR.Interaction.Runtime` from dependent asmdefs.
- Implement `IInteractionActor` or use `SimpleInteractionActor` for basic setups.
- Add `InteractionSensor` and bind a camera explicitly.
- Add `IInteractable` components to world objects.
- If a collider lives on a child object, add `InteractionTargetProxy` to that collider and bind the actual interactable explicitly.

Documentation summary:
Reusable interaction flow for pickups, keyed doors, and custom world objects.

Known product limits:
- this package does not provide a full HUD prompt renderer
- input polling is demo-only; production projects should trigger `TryInteract(...)` from their own input layer

## Technical details
- Package name: `com.hpr.interaction`
- Version: `0.1.0`
- Unity version: `6000.4`
- Dependencies: com.hpr.eventbus, com.hpr.inventory
- Sample import path: `Samples~/Demo`
- Screenshot: `screenshots/com.hpr.interaction.png`
- Artifact info: `com.hpr.interaction_info.txt`

## Human-only fields to fill before upload
- Price
- Category/subcategory
- Support email or support URL
- Marketing screenshots selection and ordering
- Package icon / cover art if you want a bespoke visual instead of the captured demo screenshot

## Suggested keywords
- interaction
- pickup
- doors
- world
