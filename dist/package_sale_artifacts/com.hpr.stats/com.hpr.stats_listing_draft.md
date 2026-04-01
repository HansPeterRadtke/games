# HPR Stats Asset Store Listing Draft

## Title
HPR Stats

## Short description
Reusable health, stamina, and damage-event runtime for Unity gameplay actors.

## Long description
Reusable health, stamina, and damage-event runtime for Unity gameplay actors.

Use this package when you want:
- a lightweight actor stats component with health and stamina handling
- event-driven damage application through a standalone event bus
- a reusable `IDamageable` / `ICharacterStats` contract for gameplay actors

Included:
- `IDamageable`
- `ICharacterStats`
- `ActorStatsComponent`
- `DamageableTargetProxy`
- `DamageEvent`

Installation summary:
- Add `com.hpr.stats` and `com.hpr.eventbus` to your Unity project.
- Reference `HPR.Stats.Runtime` from dependent asmdefs.
- Add `ActorStatsComponent` or a derived component to an actor GameObject.
- Bind an `IEventBusSource` explicitly if you want damage to arrive through events.

Documentation summary:
Reusable health, stamina, and damage-event runtime for Unity gameplay actors.

Known product limits:
- this package does not include armor, resistances, or status-effect stacks
- stamina regeneration policy is left to the consuming project

## Technical details
- Package name: `com.hpr.stats`
- Version: `0.1.0`
- Unity version: `6000.4`
- Dependencies: com.hpr.eventbus
- Sample import path: `Samples~/Demo`
- Screenshot: `screenshots/com.hpr.stats.png`
- Artifact info: `com.hpr.stats_info.txt`

## Human-only fields to fill before upload
- Price
- Category/subcategory
- Support email or support URL
- Marketing screenshots selection and ordering
- Package icon / cover art if you want a bespoke visual instead of the captured demo screenshot

## Suggested keywords
- stats
- health
- stamina
- damage
