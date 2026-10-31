using NUnit.Framework;
using System;
using System.Collections.Generic;
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
                UnityEngine.Object.DestroyImmediate(item);
                UnityEngine.Object.DestroyImmediate(go);
            }
        }

        [Test]
        public void AmmoAddition_RefusesArithmeticOverflowWithoutMutation()
        {
            var go = new GameObject("InventoryOverflow");
            var ammo = ScriptableObject.CreateInstance<ItemData>();
            try
            {
                ammo.Id = "shells";
                ammo.ItemType = ItemType.Ammo;
                ammo.Value = int.MaxValue;
                var inventory = go.AddComponent<InventoryComponent>();
                inventory.ConfigureKnownItems(new[] { ammo });
                Assert.That(inventory.AddItem(ammo, 2), Is.False);
                Assert.That(inventory.GetQuantity(ammo.Id), Is.Zero);
                Assert.That(inventory.AddItem(ammo, 1), Is.True);
                Assert.That(inventory.AddItem(ammo, 1), Is.False);
                Assert.That(inventory.GetQuantity(ammo.Id), Is.EqualTo(int.MaxValue));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(ammo);
                UnityEngine.Object.DestroyImmediate(go);
            }
        }

        [Test]
        public void SnapshotRestore_RejectsDuplicateUnknownAndInvalidItemsAtomically()
        {
            var go = new GameObject("InventoryRestore");
            var item = ScriptableObject.CreateInstance<ItemData>();
            try
            {
                item.Id = "known";
                var inventory = go.AddComponent<InventoryComponent>();
                inventory.ConfigureKnownItems(new[] { item });
                Assert.That(inventory.AddItem(item, 7), Is.True);
                var duplicate = new[] {
                    new ItemQuantitySaveData { itemId = "known", quantity = 2 },
                    new ItemQuantitySaveData { itemId = "known", quantity = 3 }
                };
                Assert.Throws<ArgumentException>(() => inventory.RestoreItemQuantities(duplicate));
                Assert.That(inventory.GetQuantity("known"), Is.EqualTo(7));
                Assert.Throws<ArgumentException>(() => inventory.RestoreItemQuantities(new[] {
                    new ItemQuantitySaveData { itemId = "known", quantity = 1 },
                    new ItemQuantitySaveData { itemId = "unrecognized", quantity = 5 }
                }));
                Assert.That(inventory.GetQuantity("known"), Is.EqualTo(7));
                Assert.Throws<ArgumentException>(() => inventory.RestoreItemQuantities(new[] {
                    new ItemQuantitySaveData { itemId = "known", quantity = -4 }
                }));
                Assert.That(inventory.GetQuantity("known"), Is.EqualTo(7));
            }
            finally
            {
                UnityEngine.Object.DestroyImmediate(item);
                UnityEngine.Object.DestroyImmediate(go);
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
                UnityEngine.Object.DestroyImmediate(item);
                UnityEngine.Object.DestroyImmediate(go);
            }
        }
    }
}
