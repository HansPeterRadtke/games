# HPR Weapon Runtime

Reusable weapon definitions plus a small headless-friendly runtime for magazine ammo, reserve ammo, firing cooldowns, firing results, ammo pickups, and reloads.

## Audience
Use this package when you want:
- weapon definitions authored as `ScriptableObject` assets
- a stable schema for slots, ammo, view-model placement, and fire-mode metadata
- package-owned runtime state for common weapon loops without adopting an input, animation, VFX, or physics framework
- runtime code that can be validated in EditMode/headless tests

## Included
- `WeaponData`
- `WeaponRuntimeState`
- `WeaponFireResult`
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
4. Create one `WeaponRuntimeState` per equipped/runtime weapon instance.
5. Feed successful `TryFire(...)` results into your own hitscan, projectile, animation, audio, and VFX layers.

## Quick start
```csharp
[SerializeField] private WeaponData rifle;
private WeaponRuntimeState state;

private void Start()
{
    state = new WeaponRuntimeState(rifle);
}

private void Update()
{
    state.Tick(Time.deltaTime);

    if (Input.GetButton("Fire1") && state.TryFire(out WeaponFireResult shot))
    {
        Debug.Log($"Fire {shot.Pellets} pellet(s), {shot.Damage} damage each");
        // Apply your own raycast/projectile/VFX implementation here.
    }

    if (Input.GetKeyDown(KeyCode.R))
    {
        state.Reload();
    }
}
```

## Runtime behavior
- `WeaponRuntimeState` initializes magazine and reserve ammo from `WeaponData`.
- `TryFire(...)` enforces cooldown and available magazine ammo, consumes one round, and returns authored damage/range/pellet/spread data.
- `Tick(deltaTime)` advances the fire cooldown without requiring a `MonoBehaviour`.
- `Reload()` transfers only the ammo required to fill the magazine.
- `AddReserveAmmo(amount)` supports pickup flows and respects `MaxAmmo` when it is configured.
- ammo-less weapons can fire without magazine/reserve state.

## API overview
- `WeaponData` stores ids, display names, fire mode, combat values, ammo settings, projectile metadata, and presentation offsets.
- `WeaponRuntimeState` owns transient per-instance ammo/cooldown state.
- `WeaponFireResult` is the clean handoff from package runtime state to the consuming combat/presentation layer.
- `FireModeType` expresses the intended runtime fire behavior category.
- `EquipmentKind` groups weapons by high-level usage.
- `WeaponUtilityAction` marks non-damage tool behavior for consuming projects.

## Demo
- Scene: `Packages/com.hpr.weapons/Demo/WeaponsDemo.unity`
- Builder: `HPR.WeaponsDemoSceneBuilder.BuildDemoScene`
- Batch validator: `HPR.WeaponsPackageValidator.ValidateInBatch`
- the validator instantiates runtime state for both included weapons and verifies that authored fire data can execute successfully.

## Validation
- Unity batch mode:
  - `Unity -batchmode -projectPath <your-project> -executeMethod HPR.WeaponsPackageValidator.ValidateInBatch -quit`
- repository helper:
  - `EXECUTE_METHOD=HPR.WeaponsPackageValidator.ValidateInBatch RUN_TESTS=1 unity/tools/packages/validate_local_packages.sh com.hpr.weapons`
- current EditMode coverage includes firing/cooldown, reload transfers, ammo-pickup clamping, and stable data defaults.

## Extension points
- perform hitscan, projectile spawning, melee traces, or utility actions from `WeaponFireResult` plus `WeaponData.FireModeType`.
- connect input, animation, audio, recoil, camera, and VFX without changing package runtime state.
- save/restore `MagazineAmmo` and `ReserveAmmo` in a consuming save layer.
- add higher-level equip/loadout controllers while retaining `WeaponData.Id` as the stable lookup key.

## Limitations
- no input binding, recoil, camera shake, animation, muzzle flash, impact VFX, or audio layer
- no built-in raycast/projectile execution; the runtime deliberately stops at a deterministic fire result
- no equip/loadout UI or reload animation timing

## Samples
- Import the package sample from Package Manager > Samples > Weapons Demo.
- The imported sample contains the demo scene and helper scripts from `Samples~/Demo`.

## Documentation
- `Documentation~/Overview.md` provides package-specific installation and integration notes.
- `Documentation~/Support.md` lists the support and issue-reporting path.

## Support
- issue tracker: https://github.com/HansPeterRadtke/games/issues
- when reporting a package issue, include the package name, Unity version, and the validator log if available.
