using System.Collections.Generic;
using System.Linq;
using UnityEngine;

public enum InventoryTab
{
    Weapons,
    Consumables,
    Keys,
    Utility
}

public class InventoryEntryData
{
    public string Id;
    public string Name;
    public string Detail;
    public int Count;
    public Color IconColor;
    public Sprite Icon;
    public bool Usable;
    public string UseLabel;
}

public class InventoryTabData
{
    public InventoryTab Tab;
    public string Label;
    public List<InventoryEntryData> Entries = new();
}

public class PlayerInventory : InventoryComponent
{
    public string BuildHudSummary()
    {
        var hudParts = new List<string>();
        foreach (var item in KnownItems)
        {
            if (item == null || item.ItemType == ItemType.Ammo)
            {
                continue;
            }

            int quantity = GetQuantity(item.Id);
            if (item.ItemType == ItemType.Key)
            {
                hudParts.Add(quantity > 0 ? item.DisplayName : $"{item.DisplayName} -");
                continue;
            }

            if (quantity > 0)
            {
                hudParts.Add($"{item.DisplayName} {quantity}");
            }
        }

        return hudParts.Count == 0 ? "No field supplies" : string.Join("  ", hudParts);
    }

    public List<InventoryTabData> BuildInventoryTabs(IWeaponLoadout weaponSystem)
    {
        var tabs = new List<InventoryTabData>();

        var weapons = new InventoryTabData { Tab = InventoryTab.Weapons, Label = "Weapons" };
        foreach (var runtimeState in weaponSystem.RuntimeSlots)
        {
            weapons.Entries.Add(new InventoryEntryData
            {
                Id = runtimeState.Data.Id,
                Name = runtimeState.SlotLabel,
                Detail = runtimeState.GetAmmoLabel(),
                Count = runtimeState.TotalAmmoCount,
                IconColor = runtimeState.Data.ViewColor
            });
        }
        tabs.Add(weapons);

        tabs.Add(BuildItemTab(InventoryTab.Consumables, "Consumables", ItemType.Consumable));
        tabs.Add(BuildItemTab(InventoryTab.Keys, "Keys", ItemType.Key));
        tabs.Add(BuildItemTab(InventoryTab.Utility, "Utility", ItemType.Utility));
        return tabs;
    }

    private InventoryTabData BuildItemTab(InventoryTab tab, string label, ItemType itemType)
    {
        var data = new InventoryTabData { Tab = tab, Label = label };
        foreach (var item in KnownItems.Where(item => item != null && item.ItemType == itemType))
        {
            data.Entries.Add(new InventoryEntryData
            {
                Id = item.Id,
                Name = item.DisplayName,
                Detail = string.IsNullOrWhiteSpace(item.Description) ? item.ItemType.ToString() : item.Description,
                Count = GetQuantity(item.Id),
                IconColor = item.PlaceholderColor,
                Icon = item.Icon,
                Usable = itemType == ItemType.Consumable,
                UseLabel = itemType == ItemType.Consumable ? "Use" : string.Empty
            });
        }

        return data;
    }
}
