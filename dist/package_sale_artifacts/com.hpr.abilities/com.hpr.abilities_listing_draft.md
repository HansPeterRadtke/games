# HPR Abilities Asset Store Listing Draft

## Title
HPR Abilities

## Short description
Reusable data-driven active abilities with costs, cooldowns, unlocks, and event-driven runtime hooks.

## Long description
Data-driven active abilities with cooldowns, costs, unlock gating, and event publication.

Use this package when you want:
- authored `AbilityData` and `AbilityEffectData` assets
- an ability runner that activates abilities by id or unlocked slot order
- event-driven ability usage that integrates with an external HUD or analytics layer

Included:
- `AbilityData`
- `AbilityEffectData`
- `AbilityRunnerComponent`
- `IAbilityResourcePool`
- `IAbilityLoadout`
- `AbilityUsedEvent`
- `AbilityEffectAppliedEvent`
- `AbilityStatusEvent`
- `AbilityStateChangedEvent`

Installation summary:
- Add `com.hpr.abilities`, `com.hpr.eventbus`, and `com.hpr.stats` to your project.
- Reference `HPR.Abilities.Runtime` from dependent asmdefs.
- Create `AbilityEffectData` and `AbilityData` assets.
- Add `AbilityRunnerComponent` to an actor.
- Bind an `IAbilityResourcePool` and an explicit `IEventBusSource`.

Documentation summary:
Reusable data-driven active abilities with costs, cooldowns, unlocks, and event-driven runtime hooks.

Known product limits:
- the included runner supports heal, stamina restore, and area-damage effects only
- ability targeting UI and input bindings belong in the consuming project

## Technical details
- Package name: `com.hpr.abilities`
- Version: `0.1.0`
- Unity version: `6000.4`
- Dependencies: com.hpr.eventbus, com.hpr.stats
- Sample import path: `Samples~/Demo`
- Screenshot: `screenshots/com.hpr.abilities.png`
- Artifact info: `com.hpr.abilities_info.txt`

## Human-only fields to fill before upload
- Price
- Category/subcategory
- Support email or support URL
- Marketing screenshots selection and ordering
- Package icon / cover art if you want a bespoke visual instead of the captured demo screenshot

## Suggested keywords
- abilities
- cooldown
- effects
- gameplay
