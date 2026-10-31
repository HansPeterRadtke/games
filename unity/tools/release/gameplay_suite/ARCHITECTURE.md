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
movement is planar; it stores the transform but does not serialize arbitrary
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
