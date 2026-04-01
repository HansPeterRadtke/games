using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace HPR
{
    public class InventoryComponent : MonoBehaviour, IInventoryService
    {
        [SerializeField] protected List<ItemData> knownItems = new();

        protected readonly Dictionary<string, int> quantities = new(StringComparer.Ordinal);
        protected readonly Dictionary<string, ItemData> itemLookup = new(StringComparer.Ordinal);

        public event Action<ItemData, int> ItemAdded;
        public event Action<ItemData, int> ItemRemoved;

        public IReadOnlyList<ItemData> KnownItems => knownItems;

        protected virtual void Awake()
        {
            RebuildLookup();
            ResetInventory();
        }

        public virtual void ConfigureKnownItems(IEnumerable<ItemData> items)
        {
            knownItems = items.Where(item => item != null).Distinct().ToList();
            RebuildLookup();
            ResetInventory();
        }

        public virtual void ResetInventory()
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

        public virtual void ClearInventory()
        {
            quantities.Clear();
        }

        public virtual bool AddItem(ItemData data, int amount)
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
            quantities[data.Id] = GetQuantity(data.Id) + delta;

            ItemAdded?.Invoke(data, delta);
            return true;
        }

        public virtual bool RemoveItem(string itemId, int amount = 1)
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

        public virtual bool HasItem(string itemId, int amount = 1)
        {
            return GetQuantity(itemId) >= Mathf.Max(1, amount);
        }

        public virtual int GetQuantity(string itemId)
        {
            return !string.IsNullOrWhiteSpace(itemId) && quantities.TryGetValue(itemId, out int quantity) ? quantity : 0;
        }

        public virtual bool HasAnyItemOfType(ItemType itemType)
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

        public virtual ItemData GetItemData(string itemId)
        {
            return !string.IsNullOrWhiteSpace(itemId) && itemLookup.TryGetValue(itemId, out var data) ? data : null;
        }

        public virtual IReadOnlyDictionary<string, int> CaptureItemQuantities()
        {
            return new Dictionary<string, int>(quantities, StringComparer.Ordinal);
        }

        public virtual void RestoreItemQuantities(IEnumerable<ItemQuantitySaveData> savedItems)
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

        protected void RebuildLookup()
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
}
