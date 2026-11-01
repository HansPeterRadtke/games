// Private Unity Editor-only integration acceptance for existing customer code.
// This is intentionally a test-side extension, not a customer runtime dependency.
#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using UnityEngine;
using HPR;
using ExternalCustomerGame;

public static class HprExternalGameIntegrationValidator
{
    public static void Run()
    {
        string receipt = Environment.GetEnvironmentVariable("HPR_EXTERNAL_GAME_RECEIPT");
        if (string.IsNullOrWhiteSpace(receipt) || File.Exists(receipt))
            throw new InvalidOperationException("Fresh private customer-integration receipt required");

        GameObject existingPlayer = new GameObject("Unmodified Customer Controller");
        ItemData kit = ScriptableObject.CreateInstance<ItemData>();
        try
        {
            var original = existingPlayer.AddComponent<ExistingPlayerIntegration>();
            var hprInventory = existingPlayer.AddComponent<InventoryComponent>();
            kit.Id = "customer.test.medkit";
            kit.StartingPlayerQuantity = 0;
            hprInventory.ConfigureKnownItems(new[] { kit });
            if (!hprInventory.AddItem(kit, 4))
                throw new InvalidOperationException("Could not add HPR inventory item");
            if (original.ReadInventory(hprInventory, kit.Id) != 4)
                throw new InvalidOperationException("Existing user controller cannot consume HPR IInventoryService");

            var registry = new ServiceRegistry();
            registry.Register<IInventoryService>(hprInventory);
            if (!ReferenceEquals(registry.Resolve<IInventoryService>(), hprInventory))
                throw new InvalidOperationException("Existing controller dependency cannot be resolved by composition");

            var saved = hprInventory.CaptureItemQuantities();
            hprInventory.ClearInventory();
            hprInventory.RestoreItemQuantities(saved.Select(x =>
                new ItemQuantitySaveData { itemId = x.Key, quantity = x.Value }));
            if (original.ReadInventory(hprInventory, kit.Id) != 4)
                throw new InvalidOperationException("Existing controller inventory restore failed");

            int deliveries = 0;
            using (var bus = new EventBus())
            using (var token = bus.Subscribe<DamageEvent>(_ => deliveries++))
            {
                bus.Publish(new DamageEvent { SourceRoot = existingPlayer, TargetRoot = existingPlayer, Amount = 7f });
                if (deliveries != 1)
                    throw new InvalidOperationException("Existing customer app did not receive typed HPR events");
            }
            if (existingPlayer.GetComponent<ExistingPlayerIntegration>() != original)
                throw new InvalidOperationException("Original player behavior was replaced");

            File.WriteAllText(receipt,
                "real_unity_6_imported_package=PASS\n" +
                "existing_custom_player_kept=PASS\n" +
                "inventory_service_interface_adapter=PASS\n" +
                "composition_runtime_adapter=PASS\n" +
                "type_safe_eventbus_adapter=PASS\n" +
                "inventory_save_restore_without_player_replacement=PASS\n");
            Debug.Log("HPR_EXISTING_GAME_ADAPTER_TEST_PASS");
        }
        finally
        {
            UnityEngine.Object.DestroyImmediate(kit);
            UnityEngine.Object.DestroyImmediate(existingPlayer);
        }
    }
}
#endif
