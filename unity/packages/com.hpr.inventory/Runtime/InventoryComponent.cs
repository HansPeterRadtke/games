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
            if (items == null) throw new ArgumentNullException(nameof(items));
            List<ItemData> candidates = items.Where(item => item != null).Distinct().ToList();
            var ids = new HashSet<string>(StringComparer.Ordinal);
            foreach (ItemData item in candidates)
            {
                if (string.IsNullOrWhiteSpace(item.Id) || !ids.Add(item.Id) ||
                    item.StartingPlayerQuantity < 0)
                    throw new ArgumentException("Each item requires one unique ID and valid start quantity.", nameof(items));
            }
            knownItems = candidates;
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

            long multiplier = data.ItemType == ItemType.Ammo ? Math.Max(1L, data.Value) : 1L;
            long delta = (long)amount * multiplier;
            long updatedQuantity = (long)GetQuantity(data.Id) + delta;
            if (delta > int.MaxValue || updatedQuantity > int.MaxValue) return false;
            if (itemLookup.TryGetValue(data.Id, out ItemData registered) &&
                !ReferenceEquals(registered, data)) return false;

            if (!itemLookup.ContainsKey(data.Id))
            {
                knownItems.Add(data);
                itemLookup[data.Id] = data;
            }
            quantities[data.Id] = (int)updatedQuantity;
            ItemAdded?.Invoke(data, (int)delta);
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
            if (savedItems == null)
                throw new ArgumentNullException(nameof(savedItems));
            var restored = new Dictionary<string, int>(StringComparer.Ordinal);
            foreach (ItemQuantitySaveData item in savedItems)
            {
                if (item == null || string.IsNullOrWhiteSpace(item.itemId) ||
                    item.quantity <= 0 || !itemLookup.ContainsKey(item.itemId) ||
                    !restored.TryAdd(item.itemId, item.quantity))
                    throw new ArgumentException("Snapshot contains invalid, unknown or duplicate items.", nameof(savedItems));
            }
            quantities.Clear();
            foreach (KeyValuePair<string, int> item in restored)
                quantities.Add(item.Key, item.Value);
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
