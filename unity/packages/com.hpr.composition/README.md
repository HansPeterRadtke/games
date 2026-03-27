# HPR Composition

Explicit service registration and lifecycle primitives for Unity projects that want
composition without hidden singletons, scene hierarchy assumptions, or reflection magic.

## Audience
Use this package when you want:
- explicit runtime service registration
- deterministic initialization and disposal ordering
- the same composition model in Unity and headless validation tools

## Included
- `IService`
- `IServiceResolver`
- `IServiceRegistry`
- `IInitializable`
- `IUpdatableService`
- `ServiceRegistry`
- `CompositionRoot`

## Dependencies
- no local package dependencies
- Unity only for the package demo scene; the runtime itself is plain C#

## Installation
1. Add `com.hpr.composition` to your Unity project.
2. Reference `HPR.Composition.Runtime` from any dependent asmdef.
3. Register services explicitly in a bootstrap layer.
4. Call `CompositionRoot.Initialize()` after registration.

## Quick start
```csharp
var root = new CompositionRoot();
root.Services.Register(new GameClockService());
root.Services.Register(new EnemySpawnerService());
root.Initialize();
root.Tick(Time.deltaTime);
root.Dispose();
```

## API overview
- `Register<TService>(instance)` stores an explicit service mapping
- `Resolve<TService>()` and `TryResolve<TService>(out service)` expose lookup
- `ResolveAll<TService>()` returns all registered services assignable to the type
- `Initialize()` invokes `IInitializable.Initialize(...)`
- `Tick(deltaTime)` invokes `IUpdatableService.Tick(...)`
- `Dispose()` disposes services in reverse registration order

## Demo
- Scene: `Packages/com.hpr.composition/Demo/CompositionDemo.unity`
- Builder: `CompositionDemoSceneBuilder.BuildDemoScene`
- Batch validator: `CompositionPackageValidator.ValidateInBatch`

## Validation
- headless composition validation:
  - `unity/tools/architecture/run_phase1_headless_validation.sh`
- clean-project import + demo validation:
  - `EXECUTE_METHOD=CompositionPackageValidator.ValidateInBatch unity/tools/packages/validate_local_packages.sh com.hpr.composition`

## Extension points
- implement `IInitializable` for services that need dependency resolution
- implement `IUpdatableService` for services that should participate in update ticks
- wrap `CompositionRoot` with any project-specific bootstrap layer

## Limitations
- this package does not discover services automatically
- it intentionally does not include reflection-based auto-registration
- scene binding remains the responsibility of the consuming project
