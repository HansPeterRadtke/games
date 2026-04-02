# HPR Stats & Damage Listing Draft

## Release recommendation
- Status: `launch_now`
- Reason: Clear gameplay-system value, real runtime behavior, validated bugs already fixed, and an easy buyer story around health, stamina, damage, and healing.

## Title
HPR Stats & Damage

## Short description
Health, stamina, damage, healing, and runtime max-value bonuses in a small reusable Unity gameplay package.

## Positioning
A compact gameplay runtime for health, stamina, damage, healing, and runtime max-value modifiers without a full RPG framework.

## Long description
HPR Stats & Damage gives Unity projects a focused runtime for the stat loops buyers usually need first: take damage, heal, spend stamina, regenerate stamina, and clamp values against effective maximums. The package ships with demo content, event integration, and clean-project validation instead of just data shells.
It is intentionally narrow. You get working health and stamina logic with damageable targets and event-driven integration, not a giant character framework or full RPG progression system.

## Feature bullets
- Actor stats runtime with health and stamina values.
- Damage, healing, spending, and regeneration flows included.
- Runtime max-value modifiers with correct clamping behavior.
- Damageable target proxy and event bus integration hooks.
- Package-owned demo scene, validator, and tests.

## Use cases
- Add health and stamina loops to a prototype without writing them from scratch.
- Drive combat or ability systems through explicit damage events.
- Use a reusable stat core beneath your own UI and VFX layers.

## Installation summary
- Import the .unitypackage and open the included stats demo.
- Attach the runtime components to your own actors or target dummies.
- Hook UI, combat, or ability systems into the exposed methods and events.
- Demo/sample path after import: `Assets/com.hpr.stats/Samples~/Demo`

## Technical details
- Package id: `com.hpr.stats`
- Version: `0.1.0`
- Unity version: `6000.4`
- Category recommendation: `Templates / Systems`
- Price recommendation: `$14.99`
- Explicit dependencies: `com.hpr.eventbus`
- Runtime behavior, not just ScriptableObject definitions.
- Clean integration path with eventbus and abilities packages.
- Validated in clean projects, EditMode tests, and official Asset Store Tools runs.
- Artifact info file: `com.hpr.stats_info.txt`

## Known limits / non-goals
- No buff/debuff stacking system.
- No RPG progression or talent tree.
- No built-in UI skin.

## Screenshot order recommendation
- `screenshots/01_overview.png` — Overview of the packaged health, stamina, damage, and healing runtime.
- `screenshots/02_workflow.png` — Damage, heal, spend, and regenerate workflow in one view.
- `screenshots/03_details.png` — Runtime hooks, boundaries, and integration details.

## Cover art recommendation
Use screenshots/01_overview.png as the initial store cover image.

## Keywords
- stats
- damage
- health
- stamina
- combat systems

## Cross-sell / bundle recommendation
- com.hpr.abilities
- com.hpr.eventbus
- com.hpr.save
- com.hpr.interaction

## Naming recommendation
Use 'HPR Stats & Damage' as the storefront title.

## Pricing strategy note
Paid first-wave package.

## Support field
Set one publisher support email address or support URL in the Asset Store portal before upload. Keep it consistent across every listing.
