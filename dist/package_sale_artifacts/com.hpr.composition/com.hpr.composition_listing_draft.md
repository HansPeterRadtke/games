# HPR Composition Asset Store Listing Draft

## Title
HPR Composition

## Short description
Explicit service registration, lifecycle management, and composition root primitives for modular Unity packages with standalone demo validation.

## Long description
Explicit service registration and lifecycle primitives for Unity projects that want composition without hidden singletons, scene hierarchy assumptions, or reflection magic.

Use this package when you want:
- explicit runtime service registration
- deterministic initialization and disposal ordering
- the same composition model in Unity and headless validation tools

Included:
- `IService`
- `IServiceResolver`
- `IServiceRegistry`
- `IInitializable`
- `IUpdatableService`
- `ServiceRegistry`
- `CompositionRoot`

Installation summary:
- Add `com.hpr.composition` to your Unity project.
- Reference `HPR.Composition.Runtime` from any dependent asmdef.
- Register services explicitly in a bootstrap layer.
- Call `CompositionRoot.Initialize()` after registration.

Documentation summary:
Explicit service registration, lifecycle management, and composition root primitives for modular Unity packages with standalone demo validation.

Known product limits:
- this package does not discover services automatically
- it intentionally does not include reflection-based auto-registration
- scene binding remains the responsibility of the consuming project

## Technical details
- Package name: `com.hpr.composition`
- Version: `0.1.0`
- Unity version: `6000.4`
- Dependencies: none
- Sample import path: `Samples~/Demo`
- Screenshot: `screenshots/com.hpr.composition.png`
- Artifact info: `com.hpr.composition_info.txt`

## Human-only fields to fill before upload
- Price
- Category/subcategory
- Support email or support URL
- Marketing screenshots selection and ordering
- Package icon / cover art if you want a bespoke visual instead of the captured demo screenshot

## Suggested keywords
- composition
- services
- bootstrap
- architecture
