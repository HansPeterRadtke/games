# HPR Inventory Asset Store Listing Draft

## Title
HPR Inventory

## Short description
Reusable item definitions and stack-based inventory runtime services for Unity projects.

## Long description
Reusable item definitions and stack-based runtime inventory service for Unity projects.

Use this package when you want:
- data-driven item definitions through `ItemData`
- runtime inventory storage keyed by stable item ids
- a simple inventory component that captures and restores quantities cleanly

Included:
- `ItemData`
- `ItemType`
- `ItemQuantitySaveData`
- `IInventoryService`
- `InventoryComponent`
- `ItemPickedEvent`

Installation summary:
- Add `com.hpr.inventory` to your Unity project.
- Reference `HPR.Inventory.Runtime` from dependent asmdefs.
- Create `ItemData` assets via `Assets > Create > HPR > Inventory > Item`.
- Add `InventoryComponent` or a derived component to the owning GameObject.

Documentation summary:
Reusable item definitions and stack-based inventory runtime services for Unity projects.

Known product limits:
- this package does not include inventory UI widgets
- slot-based equipment and crafting are intentionally out of scope

## Technical details
- Package name: `com.hpr.inventory`
- Version: `0.1.0`
- Unity version: `6000.4`
- Dependencies: none
- Sample import path: `Samples~/Demo`
- Screenshot: `screenshots/com.hpr.inventory.png`
- Artifact info: `com.hpr.inventory_info.txt`

## Human-only fields to fill before upload
- Price
- Category/subcategory
- Support email or support URL
- Marketing screenshots selection and ordering
- Package icon / cover art if you want a bespoke visual instead of the captured demo screenshot

## Suggested keywords
- inventory
- items
- pickup
- loot
