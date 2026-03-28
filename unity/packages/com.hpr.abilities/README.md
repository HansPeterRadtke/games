# HPR Abilities

Data-driven active abilities with cooldowns, costs, unlock gating, and event publication.

## Audience
Use this package when you want:
- authored `AbilityData` and `AbilityEffectData` assets
- an ability runner that activates abilities by id or unlocked slot order
- event-driven ability usage that integrates with an external HUD or analytics layer

## Included
- `AbilityData`
- `AbilityEffectData`
- `AbilityRunnerComponent`
- `IAbilityResourcePool`
- `IAbilityLoadout`
- `AbilityUsedEvent`
- `AbilityEffectAppliedEvent`
- `AbilityStatusEvent`
- `AbilityStateChangedEvent`

## Unity version
- tested with Unity `6000.4` (`6000.4.0f1`)
- intended minimum Unity editor version: `6000.4`

## Dependencies
- `com.hpr.eventbus`
- `com.hpr.stats`

## Installation
1. Add `com.hpr.abilities`, `com.hpr.eventbus`, and `com.hpr.stats` to your project.
2. Reference `HPR.Abilities.Runtime` from dependent asmdefs.
3. Create `AbilityEffectData` and `AbilityData` assets.
4. Add `AbilityRunnerComponent` to an actor.
5. Bind an `IAbilityResourcePool` and an explicit `IEventBusSource`.

## Quick start
```csharp
runner.ConfigureAbilities(new[] { repairPulse, shockPulse });
runner.SetUnlockedAbilityIds(new[] { repairPulse.Id, shockPulse.Id });
runner.BindRuntimeServices(eventBusSourceAdapter, abilityResourcePool);

runner.TryActivate(repairPulse.Id);
```

## API overview
- `ConfigureAbilities(...)` updates the authored ability catalog
- `SetUnlockedAbilityIds(...)` controls which abilities are available at runtime
- `TryActivate(...)` and `TryActivateBySlot(...)` trigger abilities and publish events
- `BuildEntries()` and `BuildHudSummary(...)` expose UI-friendly snapshots of runtime state

## Demo
- Scene: `Packages/com.hpr.abilities/Demo/AbilitiesDemo.unity`
- Builder: `AbilitiesDemoSceneBuilder.BuildDemoScene`
- Batch validator: `AbilitiesPackageValidator.ValidateInBatch`

## Validation
- Unity batch mode:
  - `Unity -batchmode -projectPath <your-project> -executeMethod AbilitiesPackageValidator.ValidateInBatch -quit`
- repository helper (used inside this repo):
  - `EXECUTE_METHOD=AbilitiesPackageValidator.ValidateInBatch unity/tools/packages/validate_local_packages.sh com.hpr.abilities`

## Extension points
- add new effect types through `AbilityEffectType` and `AbilityRunnerComponent`
- subscribe to ability events for UI, telemetry, quests, or combat logs
- implement `IAbilityResourcePool` on custom actors or wrappers around existing stat systems

## Limitations
- the included runner supports heal, stamina restore, and area-damage effects only
- ability targeting UI and input bindings belong in the consuming project
