using System.Collections.Generic;
using UnityEngine;

public interface IInteractable
{
    string GetPrompt(IPlayerActor player);
    void Interact(IPlayerActor player);
}

public interface IImpactReceiver
{
    void ApplyImpact(Vector3 impulse, Vector3 point);
}

public interface IPlayerStats : ICharacterStats
{
}

public interface IWeaponLoadout
{
    IReadOnlyList<WeaponRuntimeState> RuntimeSlots { get; }
    int SlotCount { get; }
    int CurrentIndex { get; }
    WeaponRuntimeState CurrentState { get; }
    void SelectSlot(int index);
    bool TrySelectWeapon(string weaponId);
    void AddAmmo(string weaponId, int amount);
    List<WeaponRuntimeSaveData> CaptureRuntimeState();
    void RestoreRuntimeState(IEnumerable<WeaponRuntimeSaveData> savedState, string selectedWeaponId);
    void Reload();
    void TriggerCurrent(IPlayerActor owner);
    void TickPresentation(float movementAmount, bool isAiming, bool isRunning);
}

public interface IPlayerActor
{
    Transform ActorTransform { get; }
    Camera ViewCamera { get; }
    IInventoryService InventoryService { get; }
    IPlayerStats Stats { get; }
    IWeaponLoadout WeaponSystem { get; }
    bool IsAiming { get; }
}

public interface IPlayerActorSource
{
    IPlayerActor Player { get; }
}

public interface IEnemyRegistry
{
    void RegisterEnemy(EnemyAgent enemy);
    void UnregisterEnemy(EnemyAgent enemy);
}
