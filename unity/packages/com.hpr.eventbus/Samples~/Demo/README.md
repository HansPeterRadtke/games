# HPR Event Bus Demo

Standalone demo scene and assets for `com.hpr.eventbus`.

## Scene
- `Packages/com.hpr.eventbus/Demo/EventBusDemo.unity`

## What it shows
- publishing two plain demo event types
- subscribing to both event types through `EventManager`
- rendering observed activity without any game-project dependencies

## Rebuild / validate
- builder: `HPR.EventBusDemoSceneBuilder.BuildDemoScene`
- validator: `HPR.EventBusPackageValidator.ValidateInBatch`
