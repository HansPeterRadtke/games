using System.Collections.Generic;
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
    public string Name;
    public string Detail;
    public int Count;
    public Color IconColor;
}

public class InventoryTabData
{
    public InventoryTab Tab;
    public string Label;
    public List<InventoryEntryData> Entries = new List<InventoryEntryData>();
}

public class PlayerInventory : MonoBehaviour
{
    [SerializeField] private int medkits = 1;
    [SerializeField] private int armorPatches = 1;
    [SerializeField] private bool hasRedKey;
    [SerializeField] private bool hasBlueKey;

    public int Medkits => medkits;
    public int ArmorPatches => armorPatches;
    public bool HasRedKey => hasRedKey;
    public bool HasBlueKey => hasBlueKey;

    public void ResetInventory()
    {
        medkits = 1;
        armorPatches = 1;
        hasRedKey = false;
        hasBlueKey = false;
    }

    public void ClearInventory()
    {
        medkits = 0;
        armorPatches = 0;
        hasRedKey = false;
        hasBlueKey = false;
    }

    public void AddMedkit(int amount = 1) => medkits += Mathf.Max(1, amount);
    public void AddArmorPatch(int amount = 1) => armorPatches += Mathf.Max(1, amount);
    public void AddRedKey() => hasRedKey = true;
    public void AddBlueKey() => hasBlueKey = true;

    public bool HasKey(string keyName)
    {
        return keyName switch
        {
            "Red" => hasRedKey,
            "Blue" => hasBlueKey,
            _ => true
        };
    }

    public bool UseMedkit(PlayerStats stats)
    {
        if (medkits <= 0 || stats.Health >= stats.MaxHealth - 1f)
        {
            return false;
        }

        medkits--;
        stats.Heal(35f);
        return true;
    }

    public bool UseArmorPatch(PlayerStats stats)
    {
        if (armorPatches <= 0)
        {
            return false;
        }

        armorPatches--;
        stats.Heal(10f);
        return true;
    }

    public List<InventoryTabData> BuildInventoryTabs(WeaponSystem weaponSystem)
    {
        var tabs = new List<InventoryTabData>();

        var weapons = new InventoryTabData { Tab = InventoryTab.Weapons, Label = "Weapons" };
        for (int i = 0; i < weaponSystem.SlotCount; i++)
        {
            var slot = weaponSystem.GetSlot(i);
            weapons.Entries.Add(new InventoryEntryData
            {
                Name = $"{i + 1}. {slot.DisplayName}",
                Detail = slot.GetAmmoLabel(),
                Count = slot.usesAmmo ? slot.ammoInMagazine + slot.reserveAmmo : 1,
                IconColor = slot.color
            });
        }
        tabs.Add(weapons);

        var consumables = new InventoryTabData { Tab = InventoryTab.Consumables, Label = "Consumables" };
        consumables.Entries.Add(new InventoryEntryData
        {
            Name = "Medkit",
            Detail = "Restores 35 HP",
            Count = medkits,
            IconColor = new Color(0.18f, 0.72f, 0.22f)
        });
        consumables.Entries.Add(new InventoryEntryData
        {
            Name = "Armor Patch",
            Detail = "Restores 10 HP",
            Count = armorPatches,
            IconColor = new Color(0.25f, 0.56f, 0.92f)
        });
        tabs.Add(consumables);

        var keys = new InventoryTabData { Tab = InventoryTab.Keys, Label = "Keys" };
        keys.Entries.Add(new InventoryEntryData
        {
            Name = "Red Keycard",
            Detail = hasRedKey ? "Security doors unlocked" : "Missing",
            Count = hasRedKey ? 1 : 0,
            IconColor = new Color(0.82f, 0.18f, 0.14f)
        });
        keys.Entries.Add(new InventoryEntryData
        {
            Name = "Blue Keycard",
            Detail = hasBlueKey ? "Power doors unlocked" : "Missing",
            Count = hasBlueKey ? 1 : 0,
            IconColor = new Color(0.2f, 0.34f, 0.88f)
        });
        tabs.Add(keys);

        var utility = new InventoryTabData { Tab = InventoryTab.Utility, Label = "Utility" };
        utility.Entries.Add(new InventoryEntryData
        {
            Name = "Mission Pad",
            Detail = "M opens the tactical map",
            Count = 1,
            IconColor = new Color(0.92f, 0.78f, 0.18f)
        });
        utility.Entries.Add(new InventoryEntryData
        {
            Name = "Field Manual",
            Detail = "E interact, Shift sprint, RMB aim",
            Count = 1,
            IconColor = new Color(0.56f, 0.56f, 0.62f)
        });
        tabs.Add(utility);

        return tabs;
    }
}
