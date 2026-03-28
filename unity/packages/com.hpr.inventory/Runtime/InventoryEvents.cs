using System;

[Serializable]
public class ItemQuantitySaveData
{
    public string itemId;
    public int quantity;
}

public sealed class ItemPickedEvent
{
    public UnityEngine.GameObject PickerRoot;
    public string ItemId;
    public string ItemDisplayName;
    public string LinkedWeaponId;
    public string PickupStatus;
    public int ItemType;
    public int Amount;
}

