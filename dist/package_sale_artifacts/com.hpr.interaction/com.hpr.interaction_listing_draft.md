# HPR Interaction Toolkit Listing Draft

## Release recommendation
- Status: `launch_now`
- Reason: Buyer-facing value is easy to understand from demos and screenshots: sensors, pickups, keys, and doors with explicit bindings and package-safe runtime boundaries.

## Title
HPR Interaction Toolkit

## Short description
Sensor-driven pickups and key-door interactions for Unity projects that want explicit bindings instead of hierarchy hacks.

## Positioning
A focused interaction layer for pickups, key-door logic, and actor sensors that avoids hidden hierarchy lookup and project-specific glue.

## Long description
HPR Interaction Toolkit packages a reusable interaction layer around three concrete patterns: actor sensors, inventory pickups, and key-gated doors. The runtime stays explicit about its dependencies, so buyers can integrate it without parent-lookup service locators or scene-specific glue code.
It is a practical first-wave product because the included sample content demonstrates real behavior immediately: see an interactable, use it, pick it up, and unlock a door.

## Feature bullets
- InteractionSensor with explicit source camera binding.
- Pickup interactables for inventory item collection.
- Key-door interaction flow with proxy bindings already validated.
- Designed to integrate with inventory and event-driven systems.
- Package demo, validator, and EditMode tests included.

## Use cases
- Add pickups and locked doors to a first-person prototype.
- Reuse explicit sensor logic across multiple scenes.
- Wire an inventory-based interaction flow without custom scene lookup code.

## Installation summary
- Import the .unitypackage and open the included interaction demo.
- Bind InteractionSensor to a source camera explicitly.
- Assign pickup or door interactables and connect them to your inventory/runtime flow.
- Demo/sample path after import: `Assets/com.hpr.interaction/Samples~/Demo`

## Technical details
- Package id: `com.hpr.interaction`
- Version: `0.1.0`
- Unity version: `6000.4`
- Category recommendation: `Templates / Systems`
- Price recommendation: `$14.99`
- Explicit dependencies: `com.hpr.eventbus, com.hpr.inventory`
- No parent-hierarchy service discovery.
- Works cleanly alongside inventory, stats, and eventbus packages.
- Validated in clean projects and official Asset Store Tools runs.
- Artifact info file: `com.hpr.interaction_info.txt`

## Known limits / non-goals
- No dialogue system or cinematic interaction layer.
- No animation graph integration.
- No quest scripting or controller-specific input wrappers.

## Screenshot order recommendation
- `screenshots/01_overview.png` — Overview of sensors, pickups, and key-door runtime components.
- `screenshots/02_workflow.png` — Actor sensor to interactable to result workflow.
- `screenshots/03_details.png` — Included runtime pieces, package boundaries, and non-goals.

## Cover art recommendation
Use screenshots/01_overview.png as the initial store cover image.

## Keywords
- interaction
- pickup
- door
- key system
- unity gameplay

## Cross-sell / bundle recommendation
- com.hpr.inventory
- com.hpr.stats
- com.hpr.abilities
- com.hpr.eventbus

## Naming recommendation
Use 'HPR Interaction Toolkit' as the storefront title.

## Pricing strategy note
Paid first-wave package.

## Support field
Set one publisher support email address or support URL in the Asset Store portal before upload. Keep it consistent across every listing.
