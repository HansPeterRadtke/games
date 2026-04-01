# HPR World Asset Store Listing Draft

## Title
HPR World

## Short description
Reusable asset metadata and registry types for world and placement workflows.

## Long description
Reusable asset-classification and registry assets for Unity projects that want explicit world metadata without hardcoding prefab categories or normalization values into tools.

Use this package when you want:
- stable metadata for environment, prop, enemy, weapon, or decoration prefabs
- a registry asset that resolves metadata by asset id
- authored default scale and material classification for import or placement tooling

Included:
- `AssetMetadata`
- `AssetRegistry`
- `AssetType`
- `MaterialType`

Installation summary:
- Add `com.hpr.world` to your Unity project.
- Reference `HPR.World.Runtime` from dependent asmdefs.
- Create metadata assets via `Assets > Create > HPR > World > ...`.
- Register those assets inside an `AssetRegistry` and feed it into your own world/build tooling.

Documentation summary:
Reusable asset metadata and registry types for world and placement workflows.

Known product limits:
- this package defines metadata and lookup only; it does not ship a full importer or procedural placement runtime
- prefab placement policy remains the responsibility of the consuming project

## Technical details
- Package name: `com.hpr.world`
- Version: `0.1.0`
- Unity version: `6000.4`
- Dependencies: none
- Sample import path: `Samples~/Demo`
- Screenshot: `screenshots/com.hpr.world.png`
- Artifact info: `com.hpr.world_info.txt`

## Human-only fields to fill before upload
- Price
- Category/subcategory
- Support email or support URL
- Marketing screenshots selection and ordering
- Package icon / cover art if you want a bespoke visual instead of the captured demo screenshot

## Suggested keywords
- world
- registry
- metadata
- placement
