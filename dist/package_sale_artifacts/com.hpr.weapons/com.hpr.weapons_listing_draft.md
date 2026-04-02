# HPR Weapon Data Kit Listing Draft

## Release recommendation
- Status: `second_wave`
- Reason: Technically clean, but the current value proposition is data-definition heavy and weaker than the first-wave systems unless paired with a stronger runtime controller or bundle story.

## Title
HPR Weapon Data Kit

## Short description
Reusable weapon definition assets for hitscan, scatter, ammo, and preview geometry in Unity shooter prototypes.

## Positioning
A data-definition layer for hitscan and scatter weapons that is better pitched as a follow-on product or bundle companion than a first-wave standalone SKU.

## Long description
HPR Weapon Data Kit packages WeaponData assets for common shooter fields such as damage, range, ammo, fire mode, scatter count, and preview geometry. It is useful when a team already owns the runtime shooting controller and wants to move weapon tuning into clean reusable assets.
The package is technically sellable, but it is not the strongest first-wave storefront product because it does not yet lead with a full runtime weapon controller.

## Feature bullets
- WeaponData assets for hitscan and scatter weapons.
- Damage, range, ammo, pellet, and preview fields.
- Rifle and scattergun sample content included.
- Clean package boundary and isolated validation.
- Good companion product to stats and AI content.

## Use cases
- Move weapon tuning into assets in a shooter prototype.
- Share weapon definitions across multiple runtime controllers.
- Use as a data layer inside a broader combat bundle.

## Installation summary
- Import the .unitypackage and review the included weapon data samples.
- Create WeaponData assets for each weapon profile you need.
- Consume the assets from your own firing, reload, and presentation code.
- Demo/sample path after import: `Assets/com.hpr.weapons/Samples~/Demo`

## Technical details
- Package id: `com.hpr.weapons`
- Version: `0.1.0`
- Unity version: `6000.4`
- Category recommendation: `Templates / Systems`
- Price recommendation: `$9.99`
- Explicit dependencies: `none`
- Focused on data assets rather than a full runtime controller.
- Cleanly isolated from fpsdemo-specific code.
- Validated in clean projects and tests.
- Artifact info file: `com.hpr.weapons_info.txt`

## Known limits / non-goals
- No recoil system or input/controller layer.
- No muzzle flash or combat VFX pipeline.
- No equip flow or reload animation system.

## Screenshot order recommendation
- `screenshots/01_overview.png` — Overview of authored weapon data, fire modes, and scope.
- `screenshots/02_workflow.png` — Weapon data authored once and consumed by runtime systems.
- `screenshots/03_details.png` — Commercial recommendation and non-goals for the package.

## Cover art recommendation
Use screenshots/01_overview.png as the initial cover only if you launch it later as a standalone SKU.

## Keywords
- weapons
- shooter
- data assets
- hitscan
- scattergun

## Cross-sell / bundle recommendation
- com.hpr.stats
- com.hpr.ai
- com.hpr.world

## Naming recommendation
Use 'HPR Weapon Data Kit' as the storefront title.

## Pricing strategy note
Paid second-wave package or bundle component.

## Support field
Set one publisher support email address or support URL in the Asset Store portal before upload. Keep it consistent across every listing.
