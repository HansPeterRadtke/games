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

## Unity version
- tested with Unity `6000.4` (`6000.4.0f1`)
- intended minimum Unity editor version: `6000.4`

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
- Builder: `HPR.CompositionDemoSceneBuilder.BuildDemoScene`
- Batch validator: `HPR.CompositionPackageValidator.ValidateInBatch`

## Validation
- Unity batch mode:
  - `Unity -batchmode -projectPath <your-project> -executeMethod HPR.CompositionPackageValidator.ValidateInBatch -quit`
- repository helper (used inside this repo):
  - `EXECUTE_METHOD=HPR.CompositionPackageValidator.ValidateInBatch unity/tools/packages/validate_local_packages.sh com.hpr.composition`

## Extension points
- implement `IInitializable` for services that need dependency resolution
- implement `IUpdatableService` for services that should participate in update ticks
- wrap `CompositionRoot` with any project-specific bootstrap layer

## Limitations
- this package does not discover services automatically
- it intentionally does not include reflection-based auto-registration
- scene binding remains the responsibility of the consuming project

## Samples
- Import the package sample from Package Manager > Samples > Composition Demo.
- The imported sample contains the demo scene and helper scripts from `Samples~/Demo`.

## Documentation
- `Documentation~/Overview.md` provides package-specific installation and integration notes.
- `Documentation~/Support.md` lists the support and issue-reporting path.

## Support
- issue tracker: https://github.com/HansPeterRadtke/games/issues
- when reporting a package issue, include the package name, Unity version, and the validator log if available.
