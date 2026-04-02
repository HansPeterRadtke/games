# HPR Enemy Archetype Data Listing Draft

## Release recommendation
- Status: `second_wave`
- Reason: The package is technically solid, but buyer-facing value is narrower because it defines AI archetype data without a stronger runtime behavior/controller story.

## Title
HPR Enemy Archetype Data

## Short description
Reusable enemy archetype data for melee, ranged, chase, and stationary attack behaviors in Unity combat projects.

## Positioning
Enemy archetype data assets for teams that already have or plan to add their own AI controller layer.

## Long description
HPR Enemy Archetype Data packages enemy tuning into reusable ScriptableObject assets. Buyers get clean fields for health, speed, chase range, attack range, damage, and high-level behavior categories that a separate AI runtime can consume.
That makes it technically clean and reusable, but commercially it is better positioned as a follow-on release or a bundle companion until the runtime story is stronger.

## Feature bullets
- EnemyData assets for melee and ranged archetypes.
- Aggressive chase and stationary attack behavior categories.
- Sample raider and sentry content included.
- Designed for teams that want data-driven enemy tuning.
- Isolated validation, docs, samples, and tests included.

## Use cases
- Move enemy balance out of scripts and into authored assets.
- Share AI archetype data across multiple scenes or modes.
- Pair with your own navigation and behavior execution layer.

## Installation summary
- Import the .unitypackage and open the included AI demo/sample content.
- Create EnemyData assets for each archetype you want to expose.
- Consume those assets from your own behavior controller or combat runtime.
- Demo/sample path after import: `Assets/com.hpr.ai/Samples~/Demo`

## Technical details
- Package id: `com.hpr.ai`
- Version: `0.1.0`
- Unity version: `6000.4`
- Category recommendation: `Templates / Systems`
- Price recommendation: `$9.99`
- Explicit dependencies: `none`
- Enemy data layer only; no navigation or behavior-tree runtime included.
- Package boundaries are clean and independently validated.
- Best paired with combat or controller packages.
- Artifact info file: `com.hpr.ai_info.txt`

## Known limits / non-goals
- No pathfinding or navigation controller.
- No perception/senses runtime.
- No spawner system or animation layer.

## Screenshot order recommendation
- `screenshots/01_overview.png` — Overview of enemy archetype assets and included behavior categories.
- `screenshots/02_workflow.png` — How the data flows into a consuming runtime controller.
- `screenshots/03_details.png` — Why the package is better as a later-wave or bundled product.

## Cover art recommendation
Use screenshots/01_overview.png only if launching it later as a standalone SKU.

## Keywords
- ai
- enemy
- archetype
- scriptable object
- combat data

## Cross-sell / bundle recommendation
- com.hpr.weapons
- com.hpr.stats
- com.hpr.world

## Naming recommendation
Use 'HPR Enemy Archetype Data' as the storefront title.

## Pricing strategy note
Paid second-wave package or bundle component.

## Support field
Set one publisher support email address or support URL in the Asset Store portal before upload. Keep it consistent across every listing.
