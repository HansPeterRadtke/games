# HPR Inventory Core Listing Draft

## Release recommendation
- Status: `launch_now`
- Reason: Clear reusable runtime value with actual quantity tracking, sample items, and straightforward integration into pickups, save systems, and gameplay logic.

## Title
HPR Inventory Core

## Short description
Reusable item definitions and runtime quantity tracking for keys, consumables, and ammo in Unity projects.

## Positioning
A lean inventory runtime for item definitions, keys, consumables, and ammo counts without dragging in UI skins or economy systems.

## Long description
HPR Inventory Core gives you the part of inventory work that should stay generic: item definitions, known-item registration, runtime quantity tracking, ammo counts, and simple queries. It is designed for teams that want a dependable core before they add their own UI, save flow, or economy logic.
The package includes sample items and a clean standalone demo. It keeps scope disciplined by avoiding grid UIs, drag-and-drop skins, crafting trees, and vendor systems.

## Feature bullets
- ItemData assets for consumables, keys, ammo, and similar item types.
- InventoryComponent runtime with explicit known-item setup.
- Correct per-item quantity and ammo state tracking.
- Simple runtime queries for counts and item presence.
- Clean-project sample scene, validator, and tests.

## Use cases
- Track keys and consumables in a first-person or survival prototype.
- Store ammo counts without writing inventory logic from scratch.
- Pair a lightweight inventory runtime with your own UI and save system.

## Installation summary
- Import the .unitypackage and open the included inventory demo.
- Create or reuse ItemData assets inside the package structure.
- Configure your known items on InventoryComponent and call its runtime methods from pickups, UI, or save code.
- Demo/sample path after import: `Assets/com.hpr.inventory/Samples~/Demo`

## Technical details
- Package id: `com.hpr.inventory`
- Version: `0.1.0`
- Unity version: `6000.4`
- Category recommendation: `Templates / Systems`
- Price recommendation: `$14.99`
- Explicit dependencies: `none`
- Deliberately avoids UI and economy coupling.
- Integrates cleanly with interaction and save packages.
- Validated in isolated clean projects and tests.
- Artifact info file: `com.hpr.inventory_info.txt`

## Known limits / non-goals
- No built-in inventory UI.
- No drag-and-drop equipment grid.
- No crafting or vendor subsystem.

## Screenshot order recommendation
- `screenshots/01_overview.png` — Overview of item definitions, runtime storage, and package scope.
- `screenshots/02_workflow.png` — Pickup to stored-quantity workflow for keys, potions, and ammo.
- `screenshots/03_details.png` — Detailed runtime features, sample items, and non-goals.

## Cover art recommendation
Use screenshots/01_overview.png as the initial store cover image.

## Keywords
- inventory
- items
- ammo
- keys
- consumables

## Cross-sell / bundle recommendation
- com.hpr.interaction
- com.hpr.save
- com.hpr.abilities

## Naming recommendation
Use 'HPR Inventory Core' as the storefront title.

## Pricing strategy note
Paid first-wave package.

## Support field
Set one publisher support email address or support URL in the Asset Store portal before upload. Keep it consistent across every listing.
