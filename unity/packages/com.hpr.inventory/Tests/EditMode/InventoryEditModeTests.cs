using NUnit.Framework;
using UnityEngine;

namespace HPR
{
    public class InventoryEditModeTests
    {
        [Test]
        public void AmmoItems_UseValueMultiplierWhenAdded()
        {
            var go = new GameObject("Inventory");
            var item = ScriptableObject.CreateInstance<ItemData>();
            try
            {
                item.Id = "ammo.shell";
                item.ItemType = ItemType.Ammo;
                item.Value = 4;

                var inventory = go.AddComponent<InventoryComponent>();
                inventory.ConfigureKnownItems(new[] { item });

                inventory.AddItem(item, 2);

                Assert.That(inventory.GetQuantity(item.Id), Is.EqualTo(8));
            }
            finally
            {
                Object.DestroyImmediate(item);
                Object.DestroyImmediate(go);
            }
        }

        [Test]
        public void RemoveItem_DecrementsStoredQuantity()
        {
            var go = new GameObject("Inventory");
            var item = ScriptableObject.CreateInstance<ItemData>();
            try
            {
                item.Id = "key.card";
                item.ItemType = ItemType.Key;

                var inventory = go.AddComponent<InventoryComponent>();
                inventory.ConfigureKnownItems(new[] { item });
                inventory.AddItem(item, 3);

                bool removed = inventory.RemoveItem(item.Id, 2);

                Assert.That(removed, Is.True);
                Assert.That(inventory.GetQuantity(item.Id), Is.EqualTo(1));
            }
            finally
            {
                Object.DestroyImmediate(item);
                Object.DestroyImmediate(go);
            }
        }
    }
}
