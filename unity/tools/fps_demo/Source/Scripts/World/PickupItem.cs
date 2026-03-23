using UnityEngine;

public enum PickupKind
{
    AmmoPistol,
    AmmoScatter,
    AmmoLauncher,
    AmmoNeedler,
    Medkit,
    ArmorPatch,
    RedKey,
    BlueKey
}

public class PickupItem : MonoBehaviour, IInteractable, ISaveableEntity
{
    [SerializeField] private string saveId;
    [SerializeField] private PickupKind pickupKind;
    [SerializeField] private int amount = 1;

    public string SaveId => saveId;

    public void Configure(string id, PickupKind kind, int pickupAmount)
    {
        saveId = id;
        pickupKind = kind;
        amount = pickupAmount;
    }

    public string GetPrompt(PlayerController player)
    {
        return pickupKind switch
        {
            PickupKind.RedKey => "Pick up red key [E]",
            PickupKind.BlueKey => "Pick up blue key [E]",
            PickupKind.Medkit => "Pick up medkit [E]",
            PickupKind.ArmorPatch => "Pick up armor patch [E]",
            _ => "Pick up supplies [E]"
        };
    }

    public void Interact(PlayerController player)
    {
        switch (pickupKind)
        {
            case PickupKind.AmmoPistol:
                player.WeaponSystem.AddAmmo(0, amount);
                break;
            case PickupKind.AmmoScatter:
                player.WeaponSystem.AddAmmo(1, amount);
                break;
            case PickupKind.AmmoLauncher:
                player.WeaponSystem.AddAmmo(3, amount);
                break;
            case PickupKind.AmmoNeedler:
                player.WeaponSystem.AddAmmo(4, amount);
                break;
            case PickupKind.Medkit:
                player.Inventory.AddMedkit(amount);
                break;
            case PickupKind.ArmorPatch:
                player.Inventory.AddArmorPatch(amount);
                break;
            case PickupKind.RedKey:
                player.Inventory.AddRedKey();
                break;
            case PickupKind.BlueKey:
                player.Inventory.AddBlueKey();
                break;
        }

        GameManager.Instance?.NotifyStatus($"Collected {pickupKind}");
        gameObject.SetActive(false);
    }

    public SaveEntityData CaptureState()
    {
        return new SaveEntityData
        {
            id = saveId,
            active = gameObject.activeSelf,
            position = new SerializableVector3(transform.position),
            rotation = new SerializableQuaternion(transform.rotation)
        };
    }

    public void RestoreState(SaveEntityData data)
    {
        gameObject.SetActive(data.active);
    }
}
