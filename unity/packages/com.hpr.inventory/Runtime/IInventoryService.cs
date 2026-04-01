using System;
using System.Collections.Generic;

namespace HPR
{
    public interface IInventoryService
    {
        event Action<ItemData, int> ItemAdded;
        event Action<ItemData, int> ItemRemoved;

        bool AddItem(ItemData data, int amount);
        bool RemoveItem(string itemId, int amount = 1);
        bool HasItem(string itemId, int amount = 1);
        int GetQuantity(string itemId);
        bool HasAnyItemOfType(ItemType itemType);
        ItemData GetItemData(string itemId);
        IReadOnlyDictionary<string, int> CaptureItemQuantities();
        void RestoreItemQuantities(IEnumerable<ItemQuantitySaveData> savedItems);
    }
}
