# HPR Weapon Runtime Listing Draft

## Release recommendation
- Status: `second_wave_ready`
- Reason: Now includes real package-owned firing state: magazine/reserve ammo, cooldown, deterministic fire results, ammo pickups, reload behavior, demo validation, and EditMode tests. Strong enough for a standalone second-wave submission without depending on project-specific FPS code.

## Title
HPR Weapon Runtime

## Short description
Data-driven weapon definitions with magazine ammo, reserve ammo, fire cooldowns, deterministic firing results, pickups, and reloads.

## Positioning
A compact data-driven weapon runtime that owns ammo, cooldown, firing state, pickups, and reloads while leaving input, physics, animation, audio, and VFX to the consuming project.

## Long description
HPR Weapon Runtime combines authored WeaponData assets with reusable per-instance runtime state for the loops most weapon systems need immediately: magazine ammo, reserve ammo, fire cooldowns, firing, ammo pickups, and reloads.
The runtime stays deliberately presentation-agnostic. A successful fire returns a clean WeaponFireResult containing damage, range, pellet count, and spread so your own hitscan, projectile, input, animation, audio, recoil, and VFX layers can remain project-specific.

## Feature bullets
- WeaponData assets for hitscan, shotgun, projectile, melee, and utility metadata.
- WeaponRuntimeState with magazine ammo, reserve ammo, cooldown, firing, pickup, and reload behavior.
- WeaponFireResult handoff for deterministic damage/range/pellet/spread execution.
- Rifle and scattergun sample content with runtime validation.
- Clean-project validator plus EditMode tests for firing, cooldown, reload, and ammo limits.

## Use cases
- Add a reusable ammo/reload/fire state layer beneath a custom shooter controller.
- Drive both hitscan and scatter weapon execution from authored data and deterministic fire results.
- Run weapon-state tests or simulations without scene objects or an input stack.

## Installation summary
- Import the .unitypackage and open the included weapon demo.
- Create WeaponData assets and instantiate WeaponRuntimeState for each equipped/runtime weapon instance.
- Call Tick, TryFire, Reload, and AddReserveAmmo from your own controller and presentation layers.
- Demo/sample path after import: `Assets/com.hpr.weapons/Samples~/Demo`

## Technical details
- Package id: `com.hpr.weapons`
- Version: `0.2.0`
- Unity version: `6000.4`
- Category recommendation: `Templates / Systems`
- Price recommendation: `$14.99`
- Explicit dependencies: `none`
- Package-owned runtime state rather than data assets only.
- No dependency on fpsdemo, input systems, animation controllers, or project-specific managers.
- Validated in clean Unity 6000.4 projects with package validator and EditMode tests.
- Artifact info file: `com.hpr.weapons_info.txt`

## Known limits / non-goals
- No built-in raycast/projectile execution, recoil, camera, animation, audio, or VFX layer.
- No equip/loadout UI.
- Reload is state transfer only; animation timing remains external.

## Screenshot order recommendation
- `screenshots/01_overview.png` — Overview of WeaponData plus package-owned ammo, cooldown, firing, and reload runtime state.
- `screenshots/02_workflow.png` — WeaponData to WeaponRuntimeState to WeaponFireResult workflow.
- `screenshots/03_details.png` — Integration boundaries: package state versus consuming physics, animation, audio, and VFX.

## Cover art recommendation
Use screenshots/01_overview.png as the store cover image.

## Keywords
- weapons
- ammo
- reload
- shooter runtime
- weapon system

## Cross-sell / bundle recommendation
- com.hpr.stats
- com.hpr.ai
- com.hpr.world

## Naming recommendation
Use 'HPR Weapon Runtime' as the storefront title.

## Pricing strategy note
Paid second-wave standalone package; recommended launch price $14.99.

## Support field
Set one publisher support email address or support URL in the Asset Store portal before upload. Keep it consistent across every listing.
