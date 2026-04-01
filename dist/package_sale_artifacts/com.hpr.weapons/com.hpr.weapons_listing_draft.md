# HPR Weapons Asset Store Listing Draft

## Title
HPR Weapons

## Short description
Reusable weapon data definitions and fire-mode metadata for combat packages.

## Long description
Reusable weapon-definition assets for Unity projects that want authored weapon catalogs without baking weapon metadata into scene objects or gameplay scripts.

Use this package when you want:
- weapon definitions authored as `ScriptableObject` assets
- a stable schema for slots, ammo, view-model placement, and fire mode metadata
- a package-safe weapon catalog that can drive your own combat runtime

Included:
- `WeaponData`
- `FireModeType`
- `EquipmentKind`
- `WeaponUtilityAction`

Installation summary:
- Add `com.hpr.weapons` to your Unity project.
- Reference `HPR.Weapons.Runtime` from dependent asmdefs.
- Create weapon assets via `Assets > Create > HPR > Weapons > Weapon`.
- Feed those assets into your own runtime systems or authoring tools.

Documentation summary:
Reusable weapon data definitions and fire-mode metadata for combat packages.

Known product limits:
- this package defines weapon data only; it does not include a complete shooting runtime
- projectile prefabs and combat execution remain the responsibility of the consuming project

## Technical details
- Package name: `com.hpr.weapons`
- Version: `0.1.0`
- Unity version: `6000.4`
- Dependencies: none
- Sample import path: `Samples~/Demo`
- Screenshot: `screenshots/com.hpr.weapons.png`
- Artifact info: `com.hpr.weapons_info.txt`

## Human-only fields to fill before upload
- Price
- Category/subcategory
- Support email or support URL
- Marketing screenshots selection and ordering
- Package icon / cover art if you want a bespoke visual instead of the captured demo screenshot

## Suggested keywords
- weapons
- combat
- firemodes
- data
