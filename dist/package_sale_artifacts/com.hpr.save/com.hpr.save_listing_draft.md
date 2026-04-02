# HPR Save Snapshots Listing Draft

## Release recommendation
- Status: `launch_now`
- Reason: Narrow, understandable product scope: snapshot contracts and restore flow that buyers can integrate into their own persistence layer without framework lock-in.

## Title
HPR Save Snapshots

## Short description
Capture and restore runtime state through reusable save snapshot contracts instead of a hard-coded save manager.

## Positioning
Backend-agnostic snapshot contracts for Unity projects that want save/restore behavior without adopting a monolithic save framework.

## Long description
HPR Save Snapshots focuses on one job: capture runtime state into explicit save data objects and restore that state back into scene entities later. It does not force a storage backend, slot UI, cloud sync layer, or project-wide manager pattern on the buyer.
That narrow scope makes it useful as a building block. You can pair it with your own JSON, binary, encryption, or platform persistence code while keeping gameplay state capture inside reusable package contracts.

## Feature bullets
- SaveData base contract and sample entity state types.
- Explicit capture, mutate, and restore flow in the included demo.
- Transform, active state, and gameplay value restore examples.
- No forced persistence backend or project singleton.
- Clean-project validator and EditMode tests included.

## Use cases
- Prototype a save system without adopting a full framework.
- Package state capture contracts separately from storage policy.
- Round-trip object state in tests and gameplay demos.

## Installation summary
- Import the .unitypackage and open the included demo scene.
- Implement CaptureState and RestoreState on your own entities.
- Serialize the generated SaveData objects with your preferred storage backend.
- Demo/sample path after import: `Assets/com.hpr.save/Samples~/Demo`

## Technical details
- Package id: `com.hpr.save`
- Version: `0.1.0`
- Unity version: `6000.4`
- Category recommendation: `Tools / Utilities`
- Price recommendation: `$9.99`
- Explicit dependencies: `none`
- Snapshot contracts only; storage backend stays external.
- No cross-scene manager dependency.
- Validated in isolated clean-project demos and tests.
- Artifact info file: `com.hpr.save_info.txt`

## Known limits / non-goals
- No serialization backend, slot management, or encryption layer.
- No cross-device sync.
- No save menu UI.

## Screenshot order recommendation
- `screenshots/01_overview.png` — Overview of capture, mutate, and restore contracts.
- `screenshots/02_workflow.png` — The sample capture -> runtime mutation -> restore flow.
- `screenshots/03_details.png` — Technical boundaries and extension points for backend integration.

## Cover art recommendation
Use screenshots/01_overview.png as the initial store cover image.

## Keywords
- save system
- snapshot
- restore state
- persistence
- unity utilities

## Cross-sell / bundle recommendation
- com.hpr.stats
- com.hpr.inventory
- com.hpr.interaction
- com.hpr.abilities

## Naming recommendation
Use 'HPR Save Snapshots' as the storefront title for clearer buyer-facing value.

## Pricing strategy note
Paid low-ticket first-wave package.

## Support field
Set one publisher support email address or support URL in the Asset Store portal before upload. Keep it consistent across every listing.
