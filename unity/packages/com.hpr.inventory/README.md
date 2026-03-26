# HPR Inventory

Reusable item definitions and runtime inventory services for Unity projects.

## Included
- `ItemData` ScriptableObject for item definitions
- `ItemType` classification enum
- `IInventoryService` runtime contract
- `InventoryComponent` MonoBehaviour for item stack storage and save-friendly state capture

## Dependencies
- `com.hpr.save`

## Setup
1. Add the package to `Packages/manifest.json` or embed it locally.
2. Reference `HPR.Inventory.Runtime` from any dependent asmdef.
3. Create `ItemData` assets via `Assets > Create > HPR > Inventory > Item`.
4. Add `InventoryComponent` or a derived component to a GameObject and assign known items.

## API overview
- `InventoryComponent.ConfigureKnownItems(...)` updates the catalog at runtime.
- `AddItem`, `RemoveItem`, `HasItem`, and `GetQuantity` operate purely by item id and quantity.
- `CaptureItemQuantities()` and `RestoreItemQuantities(...)` use `ItemQuantitySaveData` from `com.hpr.save`.

## Extension points
- Derive from `InventoryComponent` for project-specific HUD or tab rendering helpers.
- Subscribe to `ItemAdded` and `ItemRemoved` to drive UI or quest logic.

## Validation
- Clean-project import validation is automated through `unity/tools/packages/validate_local_packages.sh com.hpr.inventory`.

## Demo
- Demo scene: `Packages/com.hpr.inventory/Demo/InventoryDemo.unity`
- Generate or refresh it with `HPR/Inventory/Build Demo Scene` or `InventoryDemoSceneBuilder.BuildDemoScene` in batch mode.
