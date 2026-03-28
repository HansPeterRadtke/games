# HPR Inventory

Reusable item definitions and stack-based runtime inventory service for Unity projects.

## Audience
Use this package when you want:
- data-driven item definitions through `ItemData`
- runtime inventory storage keyed by stable item ids
- a simple inventory component that captures and restores quantities cleanly

## Included
- `ItemData`
- `ItemType`
- `ItemQuantitySaveData`
- `IInventoryService`
- `InventoryComponent`
- `ItemPickedEvent`

## Unity version
- tested with Unity `6000.4` (`6000.4.0f1`)
- intended minimum Unity editor version: `6000.4`

## Dependencies
- no local package dependencies

## Installation
1. Add `com.hpr.inventory` to your Unity project.
2. Reference `HPR.Inventory.Runtime` from dependent asmdefs.
3. Create `ItemData` assets via `Assets > Create > HPR > Inventory > Item`.
4. Add `InventoryComponent` or a derived component to the owning GameObject.

## Quick start
```csharp
var inventory = actor.AddComponent<InventoryComponent>();
inventory.ConfigureKnownItems(new[] { healthPotionItem, keyItem });
inventory.AddItem(healthPotionItem, 1);

bool hasPotion = inventory.HasItem(healthPotionItem.Id);
int quantity = inventory.GetQuantity(healthPotionItem.Id);
```

## API overview
- `ConfigureKnownItems(...)` replaces the known item catalog and resets quantities
- `AddItem`, `RemoveItem`, `HasItem`, and `GetQuantity` work purely by item id
- `CaptureItemQuantities()` and `RestoreItemQuantities(...)` provide save-friendly data
- `ItemAdded` and `ItemRemoved` events support UI, quest, or analytics listeners

## Demo
- Scene: `Packages/com.hpr.inventory/Demo/InventoryDemo.unity`
- Builder: `InventoryDemoSceneBuilder.BuildDemoScene`
- Batch validator: `InventoryPackageValidator.ValidateInBatch`

## Validation
- Unity batch mode:
  - `Unity -batchmode -projectPath <your-project> -executeMethod InventoryPackageValidator.ValidateInBatch -quit`
- repository helper (used inside this repo):
  - `EXECUTE_METHOD=InventoryPackageValidator.ValidateInBatch unity/tools/packages/validate_local_packages.sh com.hpr.inventory`

## Extension points
- derive from `InventoryComponent` for project-specific grouping or presentation helpers
- extend `ItemData` in your own project if you need extra metadata
- publish or consume `ItemPickedEvent` from your own interaction layer

## Limitations
- this package does not include inventory UI widgets
- slot-based equipment and crafting are intentionally out of scope
