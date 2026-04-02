# HPR Ability Runtime Listing Draft

## Release recommendation
- Status: `launch_now`
- Reason: The package already reads like a real product: ability assets, effect assets, cooldowns, unlock tracking, and visible runtime behavior backed by clean validations.

## Title
HPR Ability Runtime

## Short description
Author reusable Unity abilities through data assets, effect assets, cooldowns, and a runtime component instead of one-off scripts.

## Positioning
A reusable ability layer for self and area abilities with authorable data assets, effect assets, cooldowns, and unlock tracking.

## Long description
HPR Ability Runtime gives Unity projects a compact ability stack built around authorable AbilityData and AbilityEffectData assets. Buyers get self-target and area-target examples, cooldown handling, unlock tracking, runtime execution, and a clean integration story with stats and event-driven systems.
The package is intentionally not a whole combat game. It ships the reusable ability layer that teams can plug into their own input, VFX, animation, and UI stack.

## Feature bullets
- AbilityData assets with cooldown, cost, target type, and presentation fields.
- AbilityRunnerComponent for configured abilities and unlock state.
- Heal and area-damage effect asset examples included.
- Explicit resource-pool and stats integration points.
- Demo scene, validator, and tests included.

## Use cases
- Prototype ability-driven combat without building an ability runtime from zero.
- Author ability content as assets instead of scattered scripts.
- Integrate cooldown and unlock logic into an existing combat stack.

## Installation summary
- Import the .unitypackage and open the included ability demo.
- Create or reuse AbilityData and AbilityEffectData assets.
- Configure AbilityRunnerComponent on your actor and connect it to your own input and presentation code.
- Demo/sample path after import: `Assets/com.hpr.abilities/Samples~/Demo`

## Technical details
- Package id: `com.hpr.abilities`
- Version: `0.1.0`
- Unity version: `6000.4`
- Category recommendation: `Templates / Systems`
- Price recommendation: `$19.99`
- Explicit dependencies: `com.hpr.eventbus, com.hpr.stats`
- No runtime parent lookup remains in the package.
- Integrates cleanly with stats, save, and eventbus packages.
- Validated in clean projects, tests, and official Asset Store Tools runs.
- Artifact info file: `com.hpr.abilities_info.txt`

## Known limits / non-goals
- No animation system or cast-bar UI.
- No multiplayer authority layer.
- No full combo or talent-tree system.

## Screenshot order recommendation
- `screenshots/01_overview.png` — Overview of the ability assets, runner, and effect assets.
- `screenshots/02_workflow.png` — Ability asset to effect asset to runtime result workflow.
- `screenshots/03_details.png` — Sample content, extension points, and package boundaries.

## Cover art recommendation
Use screenshots/01_overview.png as the initial store cover image.

## Keywords
- abilities
- cooldowns
- effects
- combat
- scriptable objects

## Cross-sell / bundle recommendation
- com.hpr.stats
- com.hpr.eventbus
- com.hpr.save
- com.hpr.interaction

## Naming recommendation
Use 'HPR Ability Runtime' as the storefront title.

## Pricing strategy note
Paid first-wave package.

## Support field
Set one publisher support email address or support URL in the Asset Store portal before upload. Keep it consistent across every listing.
