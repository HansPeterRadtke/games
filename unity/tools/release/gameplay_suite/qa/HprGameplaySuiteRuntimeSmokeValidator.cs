// Verifies real cross-module Gameplay Suite state in a disposable Unity Editor project.
// No publishing, account access, or buyer-file modifications.
#if UNITY_EDITOR
using System;
using System.IO;
using System.Reflection;
using HPR;
using HPR.GameplaySuite;
using UnityEditor;
using UnityEngine;

public static class HprGameplaySuiteRuntimeSmokeValidator
{
    private const BindingFlags Flags = BindingFlags.NonPublic | BindingFlags.Instance;

    public static void Run()
    {
        GameObject player = null, enemyVisual = null, host = null;
        ItemData medkit = null;
        WeaponData rifle = null;
        EnemyData raider = null;
        try
        {
            player = new GameObject("QA-player");
            player.AddComponent<EventManager>();
            player.AddComponent<InventoryComponent>();
            player.AddComponent<ActorStatsComponent>();
            enemyVisual = GameObject.CreatePrimitive(PrimitiveType.Cube);
            enemyVisual.name = "QA-enemy-visual";
            host = new GameObject("QA-controller");
            var controller = host.AddComponent<HprGameplaySuitePlayground>();

            medkit = ScriptableObject.CreateInstance<ItemData>();
            medkit.Id = "qa_medkit";
            medkit.ItemType = ItemType.Consumable;
            medkit.StartingPlayerQuantity = 0;
            rifle = ScriptableObject.CreateInstance<WeaponData>();
            rifle.Id = "qa_rifle";
            rifle.UsesAmmo = true;
            rifle.Damage = 20f;
            rifle.FireDelay = 0.15f;
            rifle.MagazineSize = 3;
            rifle.StartingMagazineAmmo = 3;
            rifle.StartingReserveAmmo = 9;
            rifle.MaxAmmo = 15;
            raider = ScriptableObject.CreateInstance<EnemyData>();
            raider.Id = "qa_raider";
            raider.MaxHealth = 35f;
            raider.AttackDamage = 8f;
            raider.AttackRange = 2.5f;
            raider.AttackCooldown = 1f;

            Set(controller, "playerRoot", player);
            Set(controller, "enemyVisual", enemyVisual);
            Set(controller, "lootItem", medkit);
            Set(controller, "weaponData", rifle);
            Set(controller, "enemyData", raider);
            controller.enabled = true;
            typeof(HprGameplaySuitePlayground).GetMethod("Awake", Flags)?.Invoke(controller, null);
            Require(controller.PlayerHealth == 100f, "initial player health");
            Require(controller.EnemyHealth == 35f, "initial enemy health");
            Require(controller.MagazineAmmo == 3 && controller.LootCount == 0, "initial equipment");

            Require(controller.EnemyAttack(), "enemy attack should dispatch");
            Require(controller.PlayerHealth == 92f, "EventBus => Stats health damage");
            Require(!controller.EnemyAttack(), "enemy cooldown enforced");
            controller.SaveCheckpoint();
            Require(controller.HasCheckpoint, "checkpoint created");
            Require(controller.Fire(), "first shot");
            Require(controller.EnemyHealth == 15f, "first shot damage");
            Require(!controller.Fire(), "weapon cooldown enforced");
            var weaponField = typeof(HprGameplaySuitePlayground).GetField("weapon", Flags);
            var weaponState = weaponField?.GetValue(controller) as WeaponRuntimeState;
            Require(weaponState != null, "real weapon runtime reachable");
            weaponState.Tick(1f);
            Require(controller.Fire(), "second shot");
            Require(controller.EnemyHealth == 0f, "enemy death");
            Require(controller.LootCount == 1, "enemy loot delivered through Inventory");
            Require(controller.Heal(), "medkit consumed");
            Require(controller.LootCount == 0 && controller.PlayerHealth == 100f, "inventory and stats heal");
            Require(controller.RestoreCheckpoint(), "checkpoint restored");
            Require(controller.PlayerHealth == 92f && controller.EnemyHealth == 35f, "restored saved stats");
            Require(controller.LootCount == 0, "restored original loot count");
            Require(controller.Reload(), "remaining rounds reload");
            controller.ResetEncounter();
            Require(controller.PlayerHealth == 100f && controller.EnemyHealth == 35f, "encounter reset");
            Require(controller.MagazineAmmo == 3, "reset weapon magazine");

            string output = Environment.GetEnvironmentVariable("HPR_SUITE_SMOKE_RECEIPT");
            if (string.IsNullOrWhiteSpace(output)) throw new InvalidOperationException("No QA receipt path");
            File.WriteAllText(output,
                "initial_state=PASS\nweapon_fire_and_cooldown=PASS\n" +
                "enemy_health_and_death=PASS\nenemy_attack_cooldown=PASS\n" +
                "eventbus_damage_to_stats=PASS\ninventory_loot_and_heal=PASS\n" +
                "save_restore_checkpoint=PASS\nreload_and_reset=PASS\n");
            Debug.Log("HPR SUITE RUNTIME SMOKE PASS: original integrated components and state transitions");
        }
        finally
        {
            if (host != null) UnityEngine.Object.DestroyImmediate(host);
            if (player != null) UnityEngine.Object.DestroyImmediate(player);
            if (enemyVisual != null) UnityEngine.Object.DestroyImmediate(enemyVisual);
            if (medkit != null) UnityEngine.Object.DestroyImmediate(medkit);
            if (rifle != null) UnityEngine.Object.DestroyImmediate(rifle);
            if (raider != null) UnityEngine.Object.DestroyImmediate(raider);
        }
    }

    private static void Set(object instance, string name, object value)
    {
        FieldInfo field = typeof(HprGameplaySuitePlayground).GetField(name, Flags);
        if (field == null) throw new MissingFieldException(name);
        field.SetValue(instance, value);
    }

    private static void Require(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException("QA assertion failed: " + message);
    }
}
#endif
