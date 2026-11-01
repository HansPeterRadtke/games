# API and extension reference

Every original module is self-contained in
`Modules/com.hpr.<name>/Runtime/` with its existing assembly definition.
The integrated runtime sample sources are under `Integration/`.
The dependency-free original scene is under `Demo/`, the authoring
menu entry is under `Editor/` and the data examples are under `Samples/`.

## Core code integrations

`HprGameplaySuitePlayground.Awake` instantiates and registers these services:

    var root = new CompositionRoot();
    root.Services.Register<IInventoryService>(inventory);
    root.Services.Register<ICharacterStats>(stats);
    root.Services.Register<IEventBus>(eventManager.EventBus);
    root.Services.Register<IAbilityLoadout>(abilityRunner);
    root.Services.Register<AssetRegistry>(catalog);
    root.Initialize();
    IInventoryService inventoryForGame = root.Services.Resolve<IInventoryService>();

`IEventBus` is used for in-process typed events:

    eventManager.EventBus.Subscribe<DamageEvent>(evt =>
    {
        if (evt.TargetRoot == target) targetRuntime.ApplyDamage(evt.Amount);
    });

`HprSuiteAbilityPool` adapts `ActorStatsComponent` to
`IAbilityResourcePool`. `AbilityRunnerComponent` uses the adapter to
consume stamina and publishes typed ability events. `HprSuiteEnemyTarget`
connects the enemy's health state to AreaDamage's collider filtering.

`InventoryPickupInteractable`, `SimpleInteractionActor`, and
`KeyDoorInteractable` demonstrate real key-and-pickup interactions. The
training controller deliberately selects a nearby `IInteractable` rather
than implementing a camera-controlled targeting system. The standalone
`InteractionSensor` remains available for raycast-based games.

`AssetRegistry` and `AssetMetadata` are demonstration data, not asset
streaming. The registry maps a stable item ID to the ScriptableObject
metadata. The `WorldCatalogAvailable` property checks that lookup.

## Snapshot contracts

`HprSuiteSnapshot` wraps `SaveEntityData`, `ItemQuantitySaveData`,
`WeaponRuntimeSnapshot`, `EnemyRuntimeSnapshot`, and
`AbilityRuntimeSnapshot`. Captured cooldowns are *relative time remaining*,
not absolute engine time. This allows a saved state to resume after Play
restarts. Weapon and enemy runtime objects validate and restore their
snapshots before any other game state is changed. The host additionally
checks the schema, matched definitions, allowed items, health/stamina
bounds, position and cooldown values.

    HprSuiteSnapshot snapshot = controller.CaptureSnapshot();
    HprSuiteSnapshotStorage.Save(myFilePath, snapshot);
    HprSuiteSnapshot loaded = HprSuiteSnapshotStorage.Load(myFilePath);
    bool applied = controller.RestoreSnapshot(loaded);

`HprSuiteSnapshotStorage` demonstrates explicit, local JSON storage. Host
applications should build migrations, tamper detection, platform-specific
persistent storage and multiple save slots as needed. This sample's player
movement uses a collision-aware CharacterController; it stores both player and
enemy transforms and encounter mode but does not serialize arbitrary
Unity physics, scene objects or other external game systems.

## Shipping scope and constraints

Targets Unity 6000.4 in the verified pipeline. Code uses built-in
`UnityEngine` components and managed C#. There is no package manager,
network, editor service or external GUI dependency. The source package
is intended for local single-player use. State changes do not replicate
over a network. The enemy decision API is deterministic, not neural AI.
The built-in scene generator creates only original primitive geometry and
sample data, not copyrighted third-party model assets.

The development tests and cleanroom validator are intentionally excluded
from the buyer archive. The package embeds a license and AI-use notice.


## Physical encounter adapter (version 0.3)

`HprSuiteArenaMotor` wraps Unity's built-in CharacterController for planar
collision-aware player/enemy motion. `AdvanceEnemy` feeds the actual target
distance into `EnemyRuntimeState.Decide`, then moves using the motor or
dispatches the existing typed attack event. Automatic chase and manual
close-range simulation are intentionally separate. This is a deterministic
teaching example, not a full pathfinding SDK.

`FireAt(worldPoint)` raycasts in the selected direction and applies enemy
damage only when an actual collider is the nearest relevant hit; all firing
consumes ammunition regardless of hit. `Fire()` remains a convenient
scripted demonstration command aiming at the enemy collider; normal keyboard
play uses a mouse-ray/ground-plane aim point. No target can be damaged through
a physical obstacle with the new sample gun.

Save schema version three adds the enemy's current physical position/rotation
and the automatic-chase toggle to existing stats/ammo/inventory/door/ability
snapshots. It intentionally rejects incompatible version-two previews.


## Materials and pipeline selection

The original Unity-primitive scene is intentionally separate from the
commercial inventory/combat source code. The editor scene generator chooses
the active pipeline's Lit shader when available; it falls back to Standard
only for Built-in. Existing sample materials can be explicitly adapted
through the Tools/HPR/Gameplay Suite menu when imported into an existing
URP or HDRP project. Adaptation retains the authored base colors and
metallic/smoothness controls and touches only HPR sample materials.
This avoids hardcoding a Registry dependency, auto-import package installs
or changes to the buyer's project-wide Graphics Settings.


## Buyer editor diagnostics

Tools/HPR/Gameplay Suite/Verify Installation checks all ten shipped runtime
modules, source script presence, sample data assets, documentation and the
integrated demo scene. It logs its findings and displays a concise on-screen
report without launching network access, changing project settings or creating
new files. Open Showcase asks permission to save modified scenes before
switching the active editor scene. This menu tool uses public AssetDatabase
and EditorSceneManager APIs, not internal Editor reflection.


## Unity Editor integration design

The optional `HprSuiteIntegrationGuide` uses Unity's public UI Toolkit
`EditorWindow` APIs. It uses one prefixed USS style sheet in `Editor/Styles`
for responsive, dockable layout and does not require UGUI. It is read-only
except for explicit user-initiated choices (opening the sample scene after
Unity's unsaved-scene confirmation, selecting/pinging assets, copying a
plain diagnostic report, or confirmed conversion of the suite's own samples).
The presence check is intentionally limited to installed files; it does not
claim to detect every assembly conflict, binary compatibility or successful
execution in an existing customer's game. Runtime modules do not depend on
Editor windows or packages.


## Input adapter contract

The demo controller does not call `UnityEngine.Input` directly.
`IHprSuiteInputSource` supplies pressed/just-pressed actions and a
pointer position; callers can inject custom actions with `BindInputSource`
without changing their project's input backend. The default provider is
compiled for the enabled `ENABLE_INPUT_SYSTEM` or
`ENABLE_LEGACY_INPUT_MANAGER` engine symbol, with no unconditional
third-party Input System dependency. The controller Inspector lets users
remap demo keys and tune interaction reach without editing source.


## Source-authored scene and serialized GUID contract

The release's Unity scene, editable data assets and materials live as
human-inspectable Unity YAML with their original `.meta` GUIDs in the
development repository's `buyer_source_assets` source baseline.
The exporter stages them along with module source code, then exports without
regenerating objects. All non-module metadata and the original module
source metadata preserve stable GUIDs across builds. The archive static check
compares the published GUID for each authored path to the baseline; a
regenerated GUID fails release validation instead of silently breaking
upgrade references.

When changing an existing scene or sample asset, edit that authored Unity
source asset with Unity's public Editor APIs or a controlled Editor workflow,
preserve its meta file, review changes and validate a clean buyer import.
Creating a new sample requires a reviewed, unique committed GUID. Do not copy
and rename files while keeping the old GUID, or regenerate scene IDs for
an existing shipped asset. The public `Build Showcase` menu is intentionally
absent so customers do not accidentally replace their own edits.


For Unity's optional Input System-only projects, the sample input bridge
translates legacy `KeyCode` names to the corresponding `Key` values.
Control modifier keys, number-row keys and numpad keys require explicit
aliases; unavailable mouse/joystick KeyCode inputs are treated as unbound
rather than triggering an unrelated action. Experienced developers with
controller, XR or action-asset workflows should inject a custom
`IHprSuiteInputSource`. The private validation suite sends actual virtual
keyboard events into Unity Input System 1.20.1; compiling its conditional
branch alone is not considered enough.
