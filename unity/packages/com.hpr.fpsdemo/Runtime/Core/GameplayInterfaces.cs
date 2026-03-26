using System;
using System.Collections.Generic;
using UnityEngine;

public interface IInteractable
{
    string GetPrompt(IPlayerActor player);
    void Interact(IPlayerActor player);
}

public interface IDamageable
{
    bool IsAlive { get; }
    void ApplyDamage(float amount, Vector3 hitPoint, Vector3 hitDirection);
}

public interface IImpactReceiver
{
    void ApplyImpact(Vector3 impulse, Vector3 point);
}

public interface IPlayerStats : IDamageable
{
    float MaxHealth { get; }
    float MaxStamina { get; }
    float Health { get; }
    float Stamina { get; }
    void ResetStats();
    void SetHealth(float value);
    void SetStamina(float value);
    bool ConsumeStamina(float amount);
    void RegenerateStamina(float amount);
    void Heal(float amount);
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
