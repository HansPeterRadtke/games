# HPR Weapons

Reusable weapon data definitions and fire-mode metadata for Unity combat systems.

## Included
- `WeaponData` ScriptableObject
- `FireModeType`, `EquipmentKind`, and `WeaponUtilityAction` enums

## Current scope
This package currently provides the data layer for weapon-driven gameplay. Runtime weapon execution remains in the game composition package while the split continues.

## Setup
1. Add the package to your Unity project.
2. Reference `HPR.Weapons.Runtime` from dependent asmdefs.
3. Create weapon assets via `Assets > Create > HPR > Weapons > Weapon`.

## Validation
- Clean-project import validation is automated through `unity/tools/packages/validate_local_packages.sh com.hpr.weapons`.
