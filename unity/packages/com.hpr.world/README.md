# HPR World

Reusable asset-classification and registry assets for Unity projects that want explicit
world metadata without hardcoding prefab categories or normalization values into tools.

## Audience
Use this package when you want:
- stable metadata for environment, prop, enemy, weapon, or decoration prefabs
- a registry asset that resolves metadata by asset id
- authored default scale and material classification for import or placement tooling

## Included
- `AssetMetadata`
- `AssetRegistry`
- `AssetType`
- `MaterialType`

## Unity version
- tested with Unity `6000.4` (`6000.4.0f1`)
- intended minimum Unity editor version: `6000.4`

## Dependencies
- no local package dependencies
- Unity `UnityEngine` only

## Installation
1. Add `com.hpr.world` to your Unity project.
2. Reference `HPR.World.Runtime` from dependent asmdefs.
3. Create metadata assets via `Assets > Create > HPR > World > ...`.
4. Register those assets inside an `AssetRegistry` and feed it into your own world/build tooling.

## Quick start
```csharp
[SerializeField] private AssetRegistry registry;

private void Start()
{
    AssetMetadata crate = registry.Get("prop_demo_crate");
    UnityEngine.Debug.Log(crate.DisplayName);
}
```

## API overview
- `AssetMetadata` stores a stable asset id, display name, scale, material category, and optional prefab path
- `AssetRegistry` stores a metadata list and resolves entries by `AssetId`
- `AssetType` and `MaterialType` provide standardized classification categories for consuming tools

## Demo
- Scene: `Packages/com.hpr.world/Demo/WorldDemo.unity`
- Builder: `HPR.WorldDemoSceneBuilder.BuildDemoScene`
- Batch validator: `HPR.WorldPackageValidator.ValidateInBatch`

## Validation
- Unity batch mode:
  - `Unity -batchmode -projectPath <your-project> -executeMethod HPR.WorldPackageValidator.ValidateInBatch -quit`
- repository helper (used inside this repo):
  - `EXECUTE_METHOD=HPR.WorldPackageValidator.ValidateInBatch unity/tools/packages/validate_local_packages.sh com.hpr.world`

## Extension points
- extend placement/import tools by reading `AssetRegistry`
- build your own prefab normalization pipeline over `DefaultScale` and `MaterialType`
- define your own content-generation rules keyed by `AssetId`

## Limitations
- this package defines metadata and lookup only; it does not ship a full importer or procedural placement runtime
- prefab placement policy remains the responsibility of the consuming project

## Samples
- Import the package sample from Package Manager > Samples > World Demo.
- The imported sample contains the demo scene and helper scripts from `Samples~/Demo`.

## Documentation
- `Documentation~/Overview.md` provides package-specific installation and integration notes.
- `Documentation~/Support.md` lists the support and issue-reporting path.

## Support
- issue tracker: https://github.com/HansPeterRadtke/games/issues
- when reporting a package issue, include the package name, Unity version, and the validator log if available.
