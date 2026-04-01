# HPR Event Bus Asset Store Listing Draft

## Title
HPR Event Bus

## Short description
Strongly typed publish/subscribe infrastructure for Unity projects with a pure C# event bus, Unity adapter, and standalone demo validation.

## Long description
Strongly typed publish/subscribe infrastructure for Unity projects that need an event transport without taking a dependency on project-specific managers or scene hierarchies.

Use this package when you want:
- a reusable event transport shared by multiple runtime systems
- a pure C# event bus that also works outside Unity scenes
- an optional Unity `MonoBehaviour` adapter for scene composition

Included:
- `IEventBus`
- `EventBus`
- `EventManager`
- `IEventBusSource`
- `EventBusSourceAdapter`

Installation summary:
- Add `com.hpr.eventbus` to your Unity project.
- Reference `HPR.Eventbus.Runtime` from any dependent asmdef.
- Register `IEventBus` explicitly in your composition root, or place `EventManager`

Documentation summary:
Strongly typed publish/subscribe infrastructure for Unity projects with a pure C# event bus, Unity adapter, and standalone demo validation.

Known product limits:
- this package does not define domain events for you
- subscription ordering is registration-order based and intentionally simple
- no replay, persistence, or buffering is included

## Technical details
- Package name: `com.hpr.eventbus`
- Version: `0.1.0`
- Unity version: `6000.4`
- Dependencies: none
- Sample import path: `Samples~/Demo`
- Screenshot: `screenshots/com.hpr.eventbus.png`
- Artifact info: `com.hpr.eventbus_info.txt`

## Human-only fields to fill before upload
- Price
- Category/subcategory
- Support email or support URL
- Marketing screenshots selection and ordering
- Package icon / cover art if you want a bespoke visual instead of the captured demo screenshot

## Suggested keywords
- eventbus
- events
- architecture
- messaging
