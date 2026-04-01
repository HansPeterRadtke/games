# HPR Weapons

Reusable weapon-definition assets for Unity projects that want authored weapon catalogs
without baking weapon metadata into scene objects or gameplay scripts.

## Audience
Use this package when you want:
- weapon definitions authored as `ScriptableObject` assets
- a stable schema for slots, ammo, view-model placement, and fire mode metadata
- a package-safe weapon catalog that can drive your own combat runtime

## Included
- `WeaponData`
- `FireModeType`
- `EquipmentKind`
- `WeaponUtilityAction`

## Unity version
- tested with Unity `6000.4` (`6000.4.0f1`)
- intended minimum Unity editor version: `6000.4`

## Dependencies
- no local package dependencies
- Unity `UnityEngine` only

## Installation
1. Add `com.hpr.weapons` to your Unity project.
2. Reference `HPR.Weapons.Runtime` from dependent asmdefs.
3. Create weapon assets via `Assets > Create > HPR > Weapons > Weapon`.
4. Feed those assets into your own runtime systems or authoring tools.

## Quick start
```csharp
[SerializeField] private WeaponData rifle;

private void Start()
{
    UnityEngine.Debug.Log($"Loaded weapon {rifle.DisplayName} with damage {rifle.Damage}");
}
```

## API overview
- `WeaponData` stores ids, display names, slot defaults, and ammo settings
- `FireModeType` expresses the intended runtime fire behavior category
- `EquipmentKind` groups weapons by high-level usage
- `WeaponUtilityAction` marks non-damage tool behavior for consuming projects

## Demo
- Scene: `Packages/com.hpr.weapons/Demo/WeaponsDemo.unity`
- Builder: `HPR.WeaponsDemoSceneBuilder.BuildDemoScene`
- Batch validator: `HPR.WeaponsPackageValidator.ValidateInBatch`

## Validation
- Unity batch mode:
  - `Unity -batchmode -projectPath <your-project> -executeMethod HPR.WeaponsPackageValidator.ValidateInBatch -quit`
- repository helper (used inside this repo):
  - `EXECUTE_METHOD=HPR.WeaponsPackageValidator.ValidateInBatch unity/tools/packages/validate_local_packages.sh com.hpr.weapons`

## Extension points
- derive custom editor tooling that reads `WeaponData`
- extend your own combat runtime using `WeaponData.Id` as the stable lookup key
- use the authored view offset fields to drive view-model placement in your own weapon presentation layer

## Limitations
- this package defines weapon data only; it does not include a complete shooting runtime
- projectile prefabs and combat execution remain the responsibility of the consuming project

## Samples
- Import the package sample from Package Manager > Samples > Weapons Demo.
- The imported sample contains the demo scene and helper scripts from `Samples~/Demo`.

## Documentation
- `Documentation~/Overview.md` provides package-specific installation and integration notes.
- `Documentation~/Support.md` lists the support and issue-reporting path.

## Support
- issue tracker: https://github.com/HansPeterRadtke/games/issues
- when reporting a package issue, include the package name, Unity version, and the validator log if available.
