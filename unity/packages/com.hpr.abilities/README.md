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
- Builder: `HPR.AbilitiesDemoSceneBuilder.BuildDemoScene`
- Batch validator: `HPR.AbilitiesPackageValidator.ValidateInBatch`

## Validation
- Unity batch mode:
  - `Unity -batchmode -projectPath <your-project> -executeMethod HPR.AbilitiesPackageValidator.ValidateInBatch -quit`
- repository helper (used inside this repo):
  - `EXECUTE_METHOD=HPR.AbilitiesPackageValidator.ValidateInBatch unity/tools/packages/validate_local_packages.sh com.hpr.abilities`

## Extension points
- add new effect types through `AbilityEffectType` and `AbilityRunnerComponent`
- subscribe to ability events for UI, telemetry, quests, or combat logs
- implement `IAbilityResourcePool` on custom actors or wrappers around existing stat systems
- place `DamageableTargetProxy` on child colliders when area damage needs to resolve an `IDamageable` target on another object

## Limitations
- the included runner supports heal, stamina restore, and area-damage effects only
- ability targeting UI and input bindings belong in the consuming project

## Samples
- Import the package sample from Package Manager > Samples > Abilities Demo.
- The imported sample contains the demo scene and helper scripts from `Samples~/Demo`.

## Documentation
- `Documentation~/Overview.md` provides package-specific installation and integration notes.
- `Documentation~/Support.md` lists the support and issue-reporting path.

## Support
- issue tracker: https://github.com/HansPeterRadtke/games/issues
- when reporting a package issue, include the package name, Unity version, and the validator log if available.


## Definition validation and save-compatible limits

`AbilityData.TryValidateRuntimeSettings(out reason)` validates resource cost,
cooldown and all non-null built-in effects. `AbilityEffectData` exposes the same
validation entry point for effect parameters. Cost and effect amounts must be
finite and nonnegative. Cooldown is finite and between zero and
`AbilityData.MaximumCooldownSeconds` (86400 seconds, one day), matching the existing
snapshot format's limit. Area-damage radius is finite and nonnegative; the existing
minimum effective radius of 0.25 meters is retained. Forward offset may be negative
but must be finite. Unsupported effect types and a null effect list are rejected.

`TryActivate` checks these settings before calling `SpendAbilityCost`, changing
health or starting cooldown. Invalid settings return false with a status reason;
negative values are no longer silently made free/instant activations. This guards
definition errors, not arbitrary failures or mutations inside custom adapter callbacks.

Empty effect lists and optional null slots retain their existing runtime behavior
for event-only integrations. The selected-object Editor installer has its separate
existing requirement for at least one independently owned effect asset. Relative
snapshot cooldowns pause while the game is closed and resume on the new game clock;
they are not wall-clock/offline-expiry timers. Runtime definition validation does
not itself load a customer save or replace a game's own save schema.

This revision's real native candidate checks are recorded in the November 3 night
research report. New six-point-four results are API-only unless a corresponding
native Editor process/log is specifically recorded; rendered buyer usability and
commercial approval remain separate gates.
