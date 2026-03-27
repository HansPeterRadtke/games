# HPR Composition Demo

Standalone scene for `com.hpr.composition`.

## Scene
- `Packages/com.hpr.composition/Demo/CompositionDemo.unity`

## What it shows
- explicit service registration
- initialization through `CompositionRoot.Initialize()`
- update ticks through `CompositionRoot.Tick(...)`
- disposal through `CompositionRoot.Dispose()`

## Rebuild / validate
- builder: `CompositionDemoSceneBuilder.BuildDemoScene`
- validator: `CompositionPackageValidator.ValidateInBatch`
