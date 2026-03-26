# HPR Event Bus

Runtime event bus infrastructure and gameplay event payloads used to decouple HPR modules.

## Included
- `IGameEventBus`
- `EventManager`
- gameplay event payloads for damage, weapon fire, pickup, kills, impact, and HUD-related notifications
- `IEventBusSource`
- `EventBusSourceAdapter`

## Setup
1. Add the package to your Unity project.
2. Reference `HPR.Eventbus.Runtime` from any dependent asmdef.
3. Add `EventManager` to a composition root GameObject.
4. Add `EventBusSourceAdapter` when a scene needs a ready-made `IEventBusSource`.

## Typical usage
- add `EventManager` to a composition root object
- add `EventBusSourceAdapter` when you need a ready-made `IEventBusSource` component
- expose the bus through `IEventBusSource`
- publish and subscribe to events instead of calling other systems directly

## Demo
- Demo scene: `Packages/com.hpr.eventbus/Demo/EventBusDemo.unity`
- Generate or refresh it with `HPR/EventBus/Build Demo Scene` or `EventBusDemoSceneBuilder.BuildDemoScene` in batch mode.

## Current limitation
- the payload set still includes FPS-domain events and may later split into generic bus infrastructure plus separate domain-event packages
