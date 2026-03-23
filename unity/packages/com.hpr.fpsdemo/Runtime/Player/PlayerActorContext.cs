using System.Linq;
using UnityEngine;

[RequireComponent(typeof(PlayerController))]
[RequireComponent(typeof(PlayerStats))]
[RequireComponent(typeof(PlayerInventory))]
[RequireComponent(typeof(WeaponSystem))]
public class PlayerActorContext : MonoBehaviour, IPlayerActor
{
    public PlayerController MovementController { get; private set; }
    public PlayerStats StatsComponent { get; private set; }
    public PlayerInventory InventoryComponent { get; private set; }
    public WeaponSystem WeaponSystemComponent { get; private set; }

    public Transform ActorTransform => transform;
    public Camera ViewCamera => MovementController != null ? MovementController.PlayerCamera : null;
    public IInventoryService InventoryService => InventoryComponent;
    public IPlayerStats Stats => StatsComponent;
    public IWeaponLoadout WeaponSystem => WeaponSystemComponent;
    public bool IsAiming => MovementController != null && MovementController.IsAiming;

    private void Awake()
    {
        MovementController = GetComponent<PlayerController>();
        StatsComponent = GetComponent<PlayerStats>();
        InventoryComponent = GetComponent<PlayerInventory>();
        WeaponSystemComponent = GetComponent<WeaponSystem>();

        WeaponSystemComponent.Initialize(ViewCamera);
        WeaponSystemComponent.BindDependencies(InventoryComponent, StatsComponent);
    }

    public void ConfigureKnownItems(System.Collections.Generic.IEnumerable<ItemData> knownItems)
    {
        InventoryComponent.ConfigureKnownItems(knownItems);
    }

    public void ConfigureLoadout(System.Collections.Generic.IEnumerable<WeaponData> weaponLoadout)
    {
        WeaponSystemComponent.ConfigureLoadout(weaponLoadout);
    }

    public void RestoreFromSave(PlayerSaveData saveData)
    {
        if (saveData == null)
        {
            return;
        }

        MovementController.RestoreTransformFromSave(saveData);
        StatsComponent.SetHealth(saveData.health);
        StatsComponent.SetStamina(saveData.stamina);
        InventoryComponent.RestoreItemQuantities(saveData.inventoryItems);
        WeaponSystemComponent.RestoreRuntimeState(saveData.weapons, saveData.selectedWeaponId);
    }

    public PlayerSaveData CaptureSaveData()
    {
        var data = MovementController.CaptureTransformSaveData();
        data.health = StatsComponent.Health;
        data.stamina = StatsComponent.Stamina;
        data.selectedWeaponId = WeaponSystemComponent.CurrentState?.Data?.Id;
        data.weapons = WeaponSystemComponent.CaptureRuntimeState();
        data.inventoryItems = InventoryComponent.CaptureItemQuantities()
            .Select(pair => new ItemQuantitySaveData { itemId = pair.Key, quantity = pair.Value })
            .ToList();
        return data;
    }
}
