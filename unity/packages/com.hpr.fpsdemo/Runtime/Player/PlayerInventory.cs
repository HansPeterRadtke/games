using System;
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
}

public class InventoryTabData
{
    public InventoryTab Tab;
    public string Label;
    public List<InventoryEntryData> Entries = new List<InventoryEntryData>();
}

public class PlayerInventory : MonoBehaviour, IInventoryService
{
    [SerializeField] private List<ItemData> knownItems = new List<ItemData>();

    private readonly Dictionary<string, int> quantities = new Dictionary<string, int>(StringComparer.Ordinal);
    private readonly Dictionary<string, ItemData> itemLookup = new Dictionary<string, ItemData>(StringComparer.Ordinal);

    public event Action<ItemData, int> ItemAdded;
    public event Action<ItemData, int> ItemRemoved;

    private void Awake()
    {
        RebuildLookup();
        ResetInventory();
    }

    public void ConfigureKnownItems(IEnumerable<ItemData> items)
    {
        knownItems = items.Where(item => item != null).Distinct().ToList();
        RebuildLookup();
        ResetInventory();
    }

    public void ResetInventory()
    {
        quantities.Clear();
        foreach (var item in knownItems)
        {
            if (item != null && item.StartingPlayerQuantity > 0)
            {
                quantities[item.Id] = item.StartingPlayerQuantity;
            }
        }
    }

    public void ClearInventory()
    {
        quantities.Clear();
    }

    public bool AddItem(ItemData data, int amount)
    {
        if (data == null || string.IsNullOrWhiteSpace(data.Id) || amount <= 0)
        {
            return false;
        }

        if (!itemLookup.ContainsKey(data.Id))
        {
            knownItems.Add(data);
            itemLookup[data.Id] = data;
        }

        int delta = data.ItemType == ItemType.Ammo ? amount * Mathf.Max(1, data.Value) : amount;
        if (data.ItemType != ItemType.Ammo)
        {
            quantities[data.Id] = GetQuantity(data.Id) + delta;
        }

        ItemAdded?.Invoke(data, delta);
        return true;
    }

    public bool RemoveItem(string itemId, int amount = 1)
    {
        if (string.IsNullOrWhiteSpace(itemId) || amount <= 0)
        {
            return false;
        }

        int current = GetQuantity(itemId);
        if (current < amount)
        {
            return false;
        }

        int remaining = current - amount;
        if (remaining > 0)
        {
            quantities[itemId] = remaining;
        }
        else
        {
            quantities.Remove(itemId);
        }

        if (itemLookup.TryGetValue(itemId, out var itemData))
        {
            ItemRemoved?.Invoke(itemData, amount);
        }

        return true;
    }

    public bool HasItem(string itemId, int amount = 1)
    {
        return GetQuantity(itemId) >= Mathf.Max(1, amount);
    }

    public int GetQuantity(string itemId)
    {
        return !string.IsNullOrWhiteSpace(itemId) && quantities.TryGetValue(itemId, out int quantity) ? quantity : 0;
    }

    public bool HasAnyItemOfType(ItemType itemType)
    {
        foreach (var pair in quantities)
        {
            if (pair.Value <= 0)
            {
                continue;
            }

            if (itemLookup.TryGetValue(pair.Key, out var data) && data.ItemType == itemType)
            {
                return true;
            }
        }

        return false;
    }

    public ItemData GetItemData(string itemId)
    {
        return !string.IsNullOrWhiteSpace(itemId) && itemLookup.TryGetValue(itemId, out var data) ? data : null;
    }

    public IReadOnlyDictionary<string, int> CaptureItemQuantities()
    {
        return new Dictionary<string, int>(quantities, StringComparer.Ordinal);
    }

    public void RestoreItemQuantities(IEnumerable<ItemQuantitySaveData> savedItems)
    {
        quantities.Clear();
        if (savedItems == null)
        {
            return;
        }

        foreach (var entry in savedItems)
        {
            if (entry == null || string.IsNullOrWhiteSpace(entry.itemId) || entry.quantity <= 0)
            {
                continue;
            }

            quantities[entry.itemId] = entry.quantity;
        }
    }

    public string BuildHudSummary()
    {
        var hudParts = new List<string>();
        foreach (var item in knownItems)
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
        foreach (var item in knownItems.Where(item => item != null && item.ItemType == itemType))
        {
            data.Entries.Add(new InventoryEntryData
            {
                Id = item.Id,
                Name = item.DisplayName,
                Detail = string.IsNullOrWhiteSpace(item.Description) ? item.ItemType.ToString() : item.Description,
                Count = GetQuantity(item.Id),
                IconColor = item.PlaceholderColor,
                Icon = item.Icon
            });
        }

        return data;
    }

    private void RebuildLookup()
    {
        itemLookup.Clear();
        foreach (var item in knownItems)
        {
            if (item == null || string.IsNullOrWhiteSpace(item.Id))
            {
                continue;
            }

            itemLookup[item.Id] = item;
        }
    }
}
