# HPR Save Asset Store Listing Draft

## Title
HPR Save

## Short description
Reusable save-state primitives, serializable transform wrappers, and generic entity save contracts for Unity projects.

## Long description
Minimal save-state primitives for Unity projects that want serializable transform/entity data without taking a dependency on a concrete game, scene, or save-slot implementation.

Use this package when you want:
- package-safe save data wrappers for `Vector3` and `Quaternion`
- a reusable `ISaveableEntity` contract for runtime components
- generic entity state payloads that a higher-level save system can persist

Included:
- `SerializableVector3`
- `SerializableQuaternion`
- `SaveEntityData`
- `ISaveableEntity`

Installation summary:
- Add `com.hpr.save` to your Unity project.
- Reference `HPR.Save.Runtime` from dependent asmdefs.
- Implement `ISaveableEntity` on any component that should capture and restore its own state.

Documentation summary:
Reusable save-state primitives, serializable transform wrappers, and generic entity save contracts for Unity projects.

Known product limits:
- this package does not provide save-slot UI, disk IO, or profile management
- it intentionally does not define player-, quest-, or weapon-specific save models

## Technical details
- Package name: `com.hpr.save`
- Version: `0.1.0`
- Unity version: `6000.4`
- Dependencies: none
- Sample import path: `Samples~/Demo`
- Screenshot: `screenshots/com.hpr.save.png`
- Artifact info: `com.hpr.save_info.txt`

## Human-only fields to fill before upload
- Price
- Category/subcategory
- Support email or support URL
- Marketing screenshots selection and ordering
- Package icon / cover art if you want a bespoke visual instead of the captured demo screenshot

## Suggested keywords
- save
- serialization
- state
- checkpoint
