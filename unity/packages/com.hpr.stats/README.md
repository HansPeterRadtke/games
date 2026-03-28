# HPR Stats

Reusable health, stamina, and damage-event runtime for Unity gameplay actors.

## Audience
Use this package when you want:
- a lightweight actor stats component with health and stamina handling
- event-driven damage application through a standalone event bus
- a reusable `IDamageable` / `ICharacterStats` contract for gameplay actors

## Included
- `IDamageable`
- `ICharacterStats`
- `ActorStatsComponent`
- `DamageableTargetProxy`
- `DamageEvent`

## Unity version
- tested with Unity `6000.4` (`6000.4.0f1`)
- intended minimum Unity editor version: `6000.4`

## Dependencies
- `com.hpr.eventbus`

## Installation
1. Add `com.hpr.stats` and `com.hpr.eventbus` to your Unity project.
2. Reference `HPR.Stats.Runtime` from dependent asmdefs.
3. Add `ActorStatsComponent` or a derived component to an actor GameObject.
4. Bind an `IEventBusSource` explicitly if you want damage to arrive through events.

## Quick start
```csharp
var stats = actor.AddComponent<ActorStatsComponent>();
stats.BindRuntimeEventBusSource(eventBusSourceAdapter);

eventBus.Publish(new DamageEvent
{
    TargetRoot = actor,
    Amount = 15f,
    HitPoint = actor.transform.position,
    HitDirection = UnityEngine.Vector3.forward
});
```

## API overview
- `ApplyDamage(...)` reduces health and triggers death handling hooks
- `Heal(...)`, `ConsumeStamina(...)`, and `RegenerateStamina(...)` mutate vitals directly
- `SetRuntimeBonuses(...)` applies runtime max-health and max-stamina bonuses
- `BindRuntimeEventBusSource(...)` wires an explicit `IEventBusSource` without hierarchy lookups
- `DamageableTargetProxy` lets child colliders forward damage to an explicit `IDamageable` target without parent lookups

## Demo
- Scene: `Packages/com.hpr.stats/Demo/StatsDemo.unity`
- Builder: `StatsDemoSceneBuilder.BuildDemoScene`
- Batch validator: `StatsPackageValidator.ValidateInBatch`

## Validation
- Unity batch mode:
  - `Unity -batchmode -projectPath <your-project> -executeMethod StatsPackageValidator.ValidateInBatch -quit`
- repository helper (used inside this repo):
  - `EXECUTE_METHOD=StatsPackageValidator.ValidateInBatch unity/tools/packages/validate_local_packages.sh com.hpr.stats`

## Extension points
- derive from `ActorStatsComponent` to customize damage reactions or death behavior
- publish `DamageEvent` from your own weapons, traps, or abilities
- consume `ICharacterStats` from UI, AI, or other gameplay systems
- place `DamageableTargetProxy` on child colliders when the `IDamageable` target lives on another object

## Limitations
- this package does not include armor, resistances, or status-effect stacks
- stamina regeneration policy is left to the consuming project
