# HPR World Asset Registry Listing Draft

## Release recommendation
- Status: `bundle_only`
- Reason: Useful supporting code, but too thin to lead as a standalone paid Asset Store listing today; best packaged inside a broader world-authoring or gameplay-data bundle.

## Title
HPR World Asset Registry

## Short description
Asset metadata and registry contracts for world props, materials, and scale defaults in data-driven Unity pipelines.

## Positioning
A lightweight metadata and registry layer that should support a broader world-building offer rather than ship alone.

## Long description
HPR World Asset Registry packages lightweight metadata and registry assets for prop ids, types, materials, and default scale values. It is clean, reusable, and technically ready, but it does not carry enough standalone buyer value to justify a first-wave paid listing on its own.
The strongest commercial use is as a bundle component or companion layer inside a larger world-authoring or import/placement product.

## Feature bullets
- AssetMetadata and AssetRegistry data assets.
- Prop id, display name, type, material, and scale fields.
- Sample entries and isolated validation included.
- Works cleanly in isolated projects and editor tooling.
- Best used as support infrastructure instead of a headlining SKU.

## Use cases
- Keep prop metadata in a reusable registry asset.
- Feed registry data into placement or import tooling.
- Ship as part of a broader environment-authoring bundle.

## Installation summary
- Import the .unitypackage only if you want the registry layer in your own tools or runtime.
- Create AssetMetadata assets and add them to an AssetRegistry asset.
- Consume registry lookups from your own editor tooling or runtime systems.
- Demo/sample path after import: `Assets/com.hpr.world/Samples~/Demo`

## Technical details
- Package id: `com.hpr.world`
- Version: `0.1.0`
- Unity version: `6000.4`
- Category recommendation: `Tools / Utilities`
- Price recommendation: `bundle_only`
- Explicit dependencies: `none`
- Registry and metadata layer only.
- Cleanly isolated and validated, but commercially thin on its own.
- Best held for bundles or a later broader product.
- Artifact info file: `com.hpr.world_info.txt`

## Known limits / non-goals
- No placement system or scene-authoring UI.
- No world streaming or procedural generation.
- No import normalization or batch tooling included here.

## Screenshot order recommendation
- `screenshots/01_overview.png` — Overview of world metadata and registry assets.
- `screenshots/02_workflow.png` — Metadata-to-registry-to-consumer workflow.
- `screenshots/03_details.png` — Bundle-only commercial recommendation and current non-goals.

## Cover art recommendation
Do not allocate standalone cover art; keep this package as a bundle/supporting component.

## Keywords
- world
- registry
- metadata
- props
- asset catalog

## Cross-sell / bundle recommendation
- com.hpr.ai
- com.hpr.weapons

## Naming recommendation
Use 'HPR World Asset Registry' if it is ever surfaced directly.

## Pricing strategy note
Bundle-only; do not prioritize a standalone paid upload in wave one.

## Support field
Set one publisher support email address or support URL in the Asset Store portal before upload. Keep it consistent across every listing.
