# HPR Composition Root Listing Draft

## Release recommendation
- Status: `launch_now`
- Reason: Architecturally clean, independently useful, validated headless, and strong companion product for teams building modular Unity runtime composition.

## Title
HPR Composition Root

## Short description
Explicit service registration and lifecycle orchestration for modular Unity runtime systems.

## Positioning
An explicit composition root and service registry for Unity teams that want deterministic startup, ticking, and teardown without DI container magic.

## Long description
HPR Composition Root packages the minimum runtime orchestration needed to register services, initialize them in a predictable order, tick them explicitly, and dispose them cleanly. It is intentionally small and readable so it can serve as a real composition layer instead of another hidden framework core.
This package is strongest for teams that want to build around package boundaries, headless validation, and thin scene adapters. It avoids reflection-based discovery, hidden singletons, and scene-hierarchy service lookup.

## Feature bullets
- IService, IInitializable, IUpdatableService, IServiceResolver, and IServiceRegistry contracts.
- Explicit ServiceRegistry and CompositionRoot implementation.
- Headless-friendly lifecycle orchestration for tests and command-line validation.
- Works cleanly with thin scene adapters instead of acting as a global manager.
- Includes demo scene, validator, and EditMode test coverage.

## Use cases
- Build scene bootstraps that only wire package-owned services together.
- Run the same service graph in headless tests and live scenes.
- Replace ad-hoc update hubs with explicit composition code.

## Installation summary
- Import the .unitypackage and open the included demo scene for the sample lifecycle flow.
- Register service instances explicitly through ServiceRegistry.
- Drive initialization and ticking through CompositionRoot or your own thin adapter.
- Demo/sample path after import: `Assets/com.hpr.composition/Samples~/Demo`

## Technical details
- Package id: `com.hpr.composition`
- Version: `0.1.0`
- Unity version: `6000.4`
- Category recommendation: `Tools / Scripting`
- Price recommendation: `$9.99`
- Explicit dependencies: `none`
- No reflection-based service discovery.
- No dependency on GameManager, SceneBootstrap, or scene hierarchy assumptions.
- Validated headlessly and in clean Unity projects.
- Artifact info file: `com.hpr.composition_info.txt`

## Known limits / non-goals
- No scoped containers or nested composition graphs.
- No attribute injection or automatic construction.
- No serialization or persistence layer.

## Screenshot order recommendation
- `screenshots/01_overview.png` — Overview of the composition root, registry, and service contracts.
- `screenshots/02_workflow.png` — Registration, initialization, ticking, and disposal workflow.
- `screenshots/03_details.png` — Boundaries, non-goals, and package-safe composition guidance.

## Cover art recommendation
Use screenshots/01_overview.png as the initial store cover image.

## Keywords
- composition root
- service registry
- dependency wiring
- unity architecture
- modular runtime

## Cross-sell / bundle recommendation
- com.hpr.eventbus
- com.hpr.save
- com.hpr.stats
- com.hpr.abilities

## Naming recommendation
Use 'HPR Composition Root' as the storefront title.

## Pricing strategy note
Paid low-ticket first-wave package.

## Support field
Set one publisher support email address or support URL in the Asset Store portal before upload. Keep it consistent across every listing.
