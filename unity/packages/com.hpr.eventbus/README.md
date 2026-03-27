# HPR Event Bus

Standalone strongly typed event bus infrastructure for modular Unity packages.

## Included
- `IEventBus`
- `EventBus`
- `EventManager`
- `IEventBusSource`
- `EventBusSourceAdapter`

## Setup
1. Add the package to your Unity project.
2. Reference `HPR.Eventbus.Runtime` from any dependent asmdef.
3. For headless or plain C# composition, instantiate `EventBus` directly.
4. For Unity scene composition, add `EventManager` to a bootstrap GameObject.
5. Add `EventBusSourceAdapter` only when a scene needs a ready-made `IEventBusSource`.

## Typical usage
- register `IEventBus` in a composition root
- publish plain C# event objects
- subscribe through strongly typed handlers
- keep domain event types outside this package

## Demo
- Demo scene: `Packages/com.hpr.eventbus/Demo/EventBusDemo.unity`
- Generate or refresh it with `HPR/EventBus/Build Demo Scene` or `EventBusDemoSceneBuilder.BuildDemoScene` in batch mode.

## Headless validation
- `unity/tools/architecture/run_phase1_headless_validation.sh`
