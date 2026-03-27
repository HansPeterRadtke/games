# HPR Composition

Explicit service registration and lifecycle primitives for modular Unity packages.

## Included
- `IServiceResolver` and `IServiceRegistry`
- `IService`, `IInitializable`, `IUpdatableService`
- `ServiceRegistry`
- `CompositionRoot`

## Setup
1. Add `com.hpr.composition` to `Packages/manifest.json`.
2. Register concrete services explicitly through `ServiceRegistry`.
3. Call `CompositionRoot.Initialize()` once registration is complete.
4. Resolve dependencies through interfaces only.

## API overview
- `Register<TService>(instance)` stores an explicit service mapping.
- `Resolve<TService>()` and `TryResolve<TService>(out service)` expose lookup.
- `Initialize()` invokes `IInitializable.Initialize(...)` on registered services.
- `Tick(deltaTime)` invokes `IUpdatableService.Tick(...)`.
- `Dispose()` shuts down the composition root and disposes registered services in reverse order.

## Intended use
- headless validation
- explicit bootstrap wiring
- scene-independent composition

## Validation
- clean-project import validation should run through `unity/tools/packages/validate_local_packages.sh com.hpr.composition`
- headless validation runs through `unity/tools/architecture/run_phase1_headless_validation.sh`
