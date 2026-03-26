# HPR Stats

Reusable health and stamina runtime contracts for Unity gameplay packages.

## Included
- `IDamageable`
- `ICharacterStats`
- `ActorStatsComponent`

## Dependencies
- `com.hpr.eventbus`

## Setup
1. Add the package to your Unity project.
2. Reference `HPR.Stats.Runtime` from dependent asmdefs.
3. Add `ActorStatsComponent` or a derived component to a GameObject.
4. If you use the event bus, provide an `IEventBusSource` in the parent hierarchy or bind one at runtime.

## Validation
- Clean-project import validation should run through `unity/tools/packages/validate_local_packages.sh com.hpr.stats` after each extraction pass.

## Demo
- Runtime demo scene target: `Packages/com.hpr.stats/Demo/StatsDemo.unity`
- Generate or refresh it with `HPR/Stats/Build Demo Scene` or `StatsDemoSceneBuilder.BuildDemoScene` in batch mode.
