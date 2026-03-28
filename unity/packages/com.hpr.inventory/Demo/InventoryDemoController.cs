using System.Collections.Generic;
using UnityEngine;

public class InventoryDemoController : MonoBehaviour
{
    [SerializeField] private InventoryComponent inventory;
    [SerializeField] private List<ItemData> demoItems = new();

    private readonly List<string> entries = new();

    public void ValidateDemo()
    {
        if (inventory == null || demoItems.Count == 0)
        {
            throw new System.InvalidOperationException("Inventory demo is missing serialized references.");
        }

        inventory.ConfigureKnownItems(demoItems);
        ItemData firstItem = demoItems[0];
        if (firstItem == null)
        {
            throw new System.InvalidOperationException("Inventory demo is missing the first item asset.");
        }

        int startingQuantity = inventory.GetQuantity(firstItem.Id);
        if (!inventory.AddItem(firstItem, 1))
        {
            throw new System.InvalidOperationException("Inventory demo could not add the first item.");
        }

        if (inventory.GetQuantity(firstItem.Id) <= startingQuantity)
        {
            throw new System.InvalidOperationException("Inventory demo add path did not increase quantity.");
        }

        if (!inventory.RemoveItem(firstItem.Id, 1))
        {
            throw new System.InvalidOperationException("Inventory demo could not remove the first item.");
        }

        inventory.ResetInventory();
        if (inventory.GetQuantity(firstItem.Id) != firstItem.StartingPlayerQuantity)
        {
            throw new System.InvalidOperationException("Inventory demo reset did not restore starting quantities.");
        }
    }

    private void Awake()
    {
        if (inventory == null)
        {
            return;
        }

        inventory.ItemAdded += HandleItemAdded;
        inventory.ItemRemoved += HandleItemRemoved;
    }

    private void Start()
    {
        if (inventory == null)
        {
            return;
        }

        inventory.ConfigureKnownItems(demoItems);
        entries.Clear();
        entries.Add("Inventory configured from demo ItemData assets.");
    }

    private void OnDestroy()
    {
        if (inventory == null)
        {
            return;
        }

        inventory.ItemAdded -= HandleItemAdded;
        inventory.ItemRemoved -= HandleItemRemoved;
    }

    private void OnGUI()
    {
        GUILayout.BeginArea(new Rect(16f, 16f, 520f, 420f), GUI.skin.box);
        GUILayout.Label("HPR Inventory Demo");
        GUILayout.Label("Standalone package demo for configuring items, stacking them, and removing them by id.");
        GUILayout.Space(8f);

        foreach (var item in demoItems)
        {
            if (item == null)
            {
                continue;
            }

            GUILayout.BeginHorizontal();
            GUILayout.Label($"{item.DisplayName} ({item.Id})", GUILayout.Width(220f));
            GUILayout.Label($"Qty: {(inventory != null ? inventory.GetQuantity(item.Id) : 0)}", GUILayout.Width(80f));

            if (GUILayout.Button("Add", GUILayout.Height(28f)))
            {
                inventory?.AddItem(item, 1);
            }

            bool canRemove = inventory != null && inventory.HasItem(item.Id);
            GUI.enabled = canRemove;
            if (GUILayout.Button("Remove", GUILayout.Height(28f)))
            {
                inventory?.RemoveItem(item.Id, 1);
            }
            GUI.enabled = true;
            GUILayout.EndHorizontal();
        }

        GUILayout.Space(12f);
        if (GUILayout.Button("Reset Inventory", GUILayout.Height(30f)))
        {
            inventory?.ResetInventory();
            entries.Insert(0, "Inventory reset to starting quantities.");
            TrimEntries();
        }

        GUILayout.Space(12f);
        GUILayout.Label("Event log:");
        foreach (var entry in entries)
        {
            GUILayout.Label($"- {entry}");
        }

        GUILayout.EndArea();
    }

    private void HandleItemAdded(ItemData itemData, int amount)
    {
        entries.Insert(0, $"Added {amount} x {itemData.DisplayName}");
        TrimEntries();
    }

    private void HandleItemRemoved(ItemData itemData, int amount)
    {
        entries.Insert(0, $"Removed {amount} x {itemData.DisplayName}");
        TrimEntries();
    }

    private void TrimEntries()
    {
        while (entries.Count > 10)
        {
            entries.RemoveAt(entries.Count - 1);
        }
    }
}
