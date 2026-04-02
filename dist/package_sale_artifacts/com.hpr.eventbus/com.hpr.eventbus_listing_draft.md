# HPR Typed Event Bus Listing Draft

## Release recommendation
- Status: `launch_now`
- Reason: Clear standalone value, isolated API surface, strong reusable fit across gameplay and tool layers, and easy screenshotable story once event flow is visualized.

## Title
HPR Typed Event Bus

## Short description
Strongly typed publish/subscribe routing for Unity projects that want modular runtime systems without manager coupling.

## Positioning
A lightweight typed event transport for modular Unity projects that want explicit publish/subscribe flow without global managers.

## Long description
HPR Typed Event Bus gives Unity projects a small, explicit event transport that stays usable in clean scene setups, runtime services, and headless validation code. It is built for teams that want strongly typed publish/subscribe flow without wiring everything through a central GameManager.
The package ships with a pure C# event bus, a Unity MonoBehaviour adapter, isolated demos, and validation tooling. It is a good fit when you want UI, gameplay, and tools to communicate through contracts instead of direct references.

## Feature bullets
- Strongly typed Publish<T> and Subscribe<T> API.
- Pure C# EventBus plus optional Unity EventManager adapter.
- Supports exact-type and base-type dispatch.
- Disposable subscription handling and explicit unsubscribe flow.
- Clean-project demo scene, validator, and EditMode tests included.

## Use cases
- Decouple gameplay systems from UI reactions.
- Drive tool and editor workflows from runtime events.
- Share the same event contracts between headless tests and scene code.

## Installation summary
- Import the .unitypackage into a clean Unity project.
- Open the included demo scene from the package folder to review the sample flow.
- Instantiate EventBus directly in pure C# code or add EventManager to a scene as the Unity adapter.
- Demo/sample path after import: `Assets/com.hpr.eventbus/Samples~/Demo`

## Technical details
- Package id: `com.hpr.eventbus`
- Version: `0.1.0`
- Unity version: `6000.4`
- Category recommendation: `Tools / Scripting`
- Price recommendation: `$9.99`
- Explicit dependencies: `none`
- Pure C# core plus Unity adapter.
- No dependency on GameManager, SceneBootstrap, or fpsdemo code.
- Validated in clean projects and official Asset Store Tools runs.
- Artifact info file: `com.hpr.eventbus_info.txt`

## Known limits / non-goals
- No replay buffer or queued delivery layer.
- No persistence or message recording system.
- Delivery order follows subscription order only.

## Screenshot order recommendation
- `screenshots/01_overview.png` — Overview of the typed event bus architecture and included API surface.
- `screenshots/02_workflow.png` — Publisher to event transport to multiple subscriber workflow.
- `screenshots/03_details.png` — Headless and Unity scene integration details and boundaries.

## Cover art recommendation
Use screenshots/01_overview.png as the initial store cover image.

## Keywords
- event bus
- typed events
- publish subscribe
- modular architecture
- unity scripting

## Cross-sell / bundle recommendation
- com.hpr.composition
- com.hpr.stats
- com.hpr.abilities
- com.hpr.interaction

## Naming recommendation
Use 'HPR Typed Event Bus' as the storefront title; keep the package id unchanged.

## Pricing strategy note
Paid low-ticket first-wave package.

## Support field
Set one publisher support email address or support URL in the Asset Store portal before upload. Keep it consistent across every listing.
