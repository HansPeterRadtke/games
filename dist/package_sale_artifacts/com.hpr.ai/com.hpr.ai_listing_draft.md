# HPR Enemy Runtime Listing Draft

## Release recommendation
- Status: `second_wave_ready`
- Reason: Now includes package-owned health/death state, attack cooldown, deterministic patrol/chase/hold/attack decisions, combat results, demo validation, and five EditMode tests. Strong enough for a standalone second-wave submission without coupling to NavMesh or project-specific AI controllers.

## Title
HPR Enemy Runtime

## Short description
Enemy archetypes with health/death state, attack cooldowns, patrol/chase/hold/attack decisions, and deterministic combat results.

## Positioning
A compact data-driven enemy runtime that owns health, death, attack cooldown, and high-level distance decisions while leaving navigation, perception, animation, and combat presentation to the consuming project.

## Long description
HPR Enemy Runtime combines authored EnemyData archetypes with reusable per-instance state for health, death, attack cooldowns, and the high-level decisions most combat enemies need: patrol, chase, hold, attack, and dead.
The runtime is deliberately navigation-agnostic. Feed it target distance, then map its decisions to your own NavMesh, steering, animation, perception, projectile, melee, audio, and VFX systems. Successful attacks return a clean EnemyAttackResult containing the authored combat values.

## Feature bullets
- EnemyData assets for melee/ranged archetypes and authored combat/range tuning.
- EnemyRuntimeState with health, damage, healing, death, and attack cooldown behavior.
- Deterministic Patrol, Hold, Chase, Attack, and Dead decisions from target distance and AI type.
- EnemyAttackResult handoff for melee/ranged combat execution.
- Raider and sentry samples plus clean-project validator and five EditMode tests.

## Use cases
- Put a deterministic behavior/combat-state layer beneath NavMesh or custom movement controllers.
- Share the same enemy decisions in scene gameplay, headless tests, and simulation code.
- Keep authored enemy balance data separate from perception, animation, and presentation systems.

## Installation summary
- Import the .unitypackage and open the included enemy demo.
- Create EnemyData assets and instantiate EnemyRuntimeState for each live enemy.
- Feed target distance into Decide/TryAttack and connect the results to your own navigation/combat layers.
- Demo/sample path after import: `Assets/com.hpr.ai/Samples~/Demo`

## Technical details
- Package id: `com.hpr.ai`
- Version: `0.2.0`
- Unity version: `6000.4`
- Category recommendation: `Templates / Systems`
- Price recommendation: `$14.99`
- Explicit dependencies: `none`
- Package-owned behavior/combat state rather than data assets only.
- No dependency on NavMesh, fpsdemo, physics queries, animation controllers, or project managers.
- Validated in clean Unity 6000.4 projects with package validator and five EditMode tests.
- Artifact info file: `com.hpr.ai_info.txt`

## Known limits / non-goals
- No pathfinding, steering, perception, or target-selection implementation.
- No behavior tree, spawner, animation, audio, or VFX layer.
- High-level decisions are distance/archetype based; richer tactical logic remains external.

## Screenshot order recommendation
- `screenshots/01_overview.png` — Overview of EnemyData plus package-owned health, cooldown, and behavior decision state.
- `screenshots/02_workflow.png` — Target distance to Patrol/Chase/Hold/Attack decision and EnemyAttackResult workflow.
- `screenshots/03_details.png` — Integration boundaries between deterministic package state and consuming navigation/perception/presentation systems.

## Cover art recommendation
Use screenshots/01_overview.png as the store cover image.

## Keywords
- enemy ai
- enemy runtime
- combat ai
- ai behavior
- enemy system

## Cross-sell / bundle recommendation
- com.hpr.weapons
- com.hpr.stats
- com.hpr.world

## Naming recommendation
Use 'HPR Enemy Runtime' as the storefront title.

## Pricing strategy note
Paid second-wave standalone package; recommended launch price $14.99.

## Support field
Set one publisher support email address or support URL in the Asset Store portal before upload. Keep it consistent across every listing.
