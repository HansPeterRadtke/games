# Modularization Status

## Checkpoint
The repo is in a verified phase-one modularization checkpoint.
The two concrete outcomes of this phase are:
- a real standalone event bus package
- a real composition root with explicit service registration and headless validation

## New package added in this phase
- `unity/packages/com.hpr.composition`

## Standalone package state in this phase
### `com.hpr.eventbus`
- now contains only generic event transport infrastructure
- no longer owns FPS-domain event payloads
- exposes:
  - `IEventBus`
  - `EventBus`
  - `EventManager`
  - `IEventBusSource`
  - `EventBusSourceAdapter`
- validated in:
  - clean Unity project
  - headless composition/event scenario

### `com.hpr.composition`
- explicit service registration and lifecycle only
- exposes:
  - `IService`
  - `IServiceResolver`
  - `IServiceRegistry`
  - `IInitializable`
  - `IUpdatableService`
  - `ServiceRegistry`
  - `CompositionRoot`
- validated in:
  - headless composition/event scenario
  - clean Unity project

## Changes in ownership
### Moved out of event bus
Gameplay-domain event payloads moved to:
- `unity/packages/com.hpr.core/Runtime/Events/GameplayEvents.cs`

### Reduced central runtime control
- `GameManager` no longer self-creates the event manager, validator, or quest manager during runtime bootstrap
- `SceneBootstrap` now wires references into `FpsDemoCompositionRoot`
- `FpsDemoCompositionRoot` owns runtime service registration
- `FpsDemoServiceAdapter` provides explicit service adaptation instead of hidden singleton access

## Current dependency truth
### Clean at phase-one level
- `com.hpr.composition`
- `com.hpr.eventbus`

### Still not clean
Primary remaining violations are in `com.hpr.fpsdemo`:
- direct `GameManager` references
- `SceneBootstrap` scene ownership
- parent `MonoBehaviour` lookup fallbacks in runtime components

Additional package-level lookup violations still exist in:
- `com.hpr.interaction`
- `com.hpr.inventory` demos
- `com.hpr.stats`

See:
- `doc/dependency-audit-phase1.md`

## Validation result at this checkpoint
Verified as `hans`:
- `unity/tools/architecture/run_phase1_headless_validation.sh`
- `unity/tools/architecture/dependency_audit.py`
- `unity/tools/packages/validate_local_packages.sh com.hpr.eventbus`
- `unity/tools/packages/validate_local_packages.sh com.hpr.composition`
- `unity/tools/fps_demo/run_unity_batch.sh SceneBootstrap.BuildLinux`
- `NO_NOTICE=1 unity/tools/fps_demo/smoke_test.sh`

## Remaining work before phase-two extraction
1. eliminate runtime parent-service discovery in `fpsdemo`
2. move more shared runtime out of `fpsdemo`
3. reduce `com.hpr.core` gameplay payload ownership where domain packages can own their own events
4. shrink `SceneBootstrap` to thin bootstrap/setup only
5. continue clean-project validation per package after each extraction
