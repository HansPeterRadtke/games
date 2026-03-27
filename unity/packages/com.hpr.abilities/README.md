# HPR Abilities

Data-driven ability activation for Unity projects.

## Included
- `AbilityData` and `AbilityEffectData` ScriptableObjects
- `AbilityRunnerComponent` with cooldowns, costs, unlock gating, and event publication
- `IAbilityResourcePool` and `IAbilityLoadout` interfaces for integration
- standalone demo scene and scene builder

## Dependencies
- `com.hpr.eventbus`
- `com.hpr.stats`

## Setup
1. Add the package to `Packages/manifest.json`.
2. Reference `HPR.Abilities.Runtime` from dependent asmdefs.
3. Create `AbilityEffectData` and `AbilityData` assets.
4. Add `AbilityRunnerComponent` to an actor.
5. Bind an `IAbilityResourcePool` implementation and an `IEventBusSource`.

## API overview
- `ConfigureAbilities(...)` updates the catalog at runtime.
- `SetUnlockedAbilityIds(...)` controls which configured abilities are available.
- `TryActivate(string abilityId)` and `TryActivateBySlot(int slotIndex)` trigger abilities.
- `BuildEntries()` and `BuildHudSummary(...)` expose UI-friendly state.

## Extension points
- Add new effect types in `AbilityEffectType` and handle them in `AbilityRunnerComponent`.
- Subscribe to `AbilityUsedEvent` or `AbilityEffectAppliedEvent` for UI, analytics, or quests.
- Implement `IAbilityResourcePool` on custom actors or bridges.

## Validation
- Clean-project import validation: `unity/tools/packages/validate_local_packages.sh com.hpr.abilities`
- Demo scene: `Packages/com.hpr.abilities/Demo/AbilitiesDemo.unity`
- Rebuild demo scene: `HPR/Abilities/Build Demo Scene`
