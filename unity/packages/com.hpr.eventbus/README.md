# HPR Event Bus

Strongly typed publish/subscribe infrastructure for Unity projects that need an event
transport without taking a dependency on project-specific managers or scene hierarchies.

## Audience
Use this package when you want:
- a reusable event transport shared by multiple runtime systems
- a pure C# event bus that also works outside Unity scenes
- an optional Unity `MonoBehaviour` adapter for scene composition

## Included
- `IEventBus`
- `EventBus`
- `EventManager`
- `IEventBusSource`
- `EventBusSourceAdapter`

## Unity version
- tested with Unity `6000.4` (`6000.4.0f1`)
- intended minimum Unity editor version: `6000.4`

## Dependencies
- no local package dependencies
- Unity `UnityEngine` only for the adapter classes and demo scene

## Installation
1. Add `com.hpr.eventbus` to your Unity project.
2. Reference `HPR.Eventbus.Runtime` from any dependent asmdef.
3. Register `IEventBus` explicitly in your composition root, or place `EventManager`
   on a bootstrap GameObject when you want scene-based composition.

## Quick start
```csharp
var bus = new EventBus();
IDisposable subscription = bus.Subscribe<PlayerDiedEvent>(evt =>
{
    UnityEngine.Debug.Log($"Player died: {evt.PlayerId}");
});

bus.Publish(new PlayerDiedEvent { PlayerId = "hero" });
subscription.Dispose();
```

## Unity scene usage
1. Add `EventManager` to a scene object.
2. Add `EventBusSourceAdapter` only if other components want a serialized
   `IEventBusSource` provider.
3. Keep domain event payload classes in your own package or project code.

## API overview
- `Subscribe<TEvent>(Action<TEvent>)` returns a disposable subscription token
- `Unsubscribe<TEvent>(Action<TEvent>)` explicitly removes a handler
- `Publish<TEvent>(TEvent)` dispatches to exact-type and base-type subscribers
- `Clear()` removes all subscriptions

## Demo
- Scene: `Packages/com.hpr.eventbus/Demo/EventBusDemo.unity`
- Builder: `HPR.EventBusDemoSceneBuilder.BuildDemoScene`
- Batch validator: `HPR.EventBusPackageValidator.ValidateInBatch`

## Validation
- Unity batch mode:
  - `Unity -batchmode -projectPath <your-project> -executeMethod HPR.EventBusPackageValidator.ValidateInBatch -quit`
- repository helper (used inside this repo):
  - `EXECUTE_METHOD=HPR.EventBusPackageValidator.ValidateInBatch unity/tools/packages/validate_local_packages.sh com.hpr.eventbus`

## Extension points
- define domain event payloads in your own package
- wrap `IEventBus` in your own service abstractions if you need filtering or logging
- compose the bus with any DI or service-registration layer

## Limitations
- this package does not define domain events for you
- subscription ordering is registration-order based and intentionally simple
- no replay, persistence, or buffering is included

## Samples
- Import the package sample from Package Manager > Samples > Event Bus Demo.
- The imported sample contains the demo scene and helper scripts from `Samples~/Demo`.

## Documentation
- `Documentation~/Overview.md` provides package-specific installation and integration notes.
- `Documentation~/Support.md` lists the support and issue-reporting path.

## Support
- issue tracker: https://github.com/HansPeterRadtke/games/issues
- when reporting a package issue, include the package name, Unity version, and the validator log if available.
