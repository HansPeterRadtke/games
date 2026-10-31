// Tests real imported buyer code, not copied source or an editor mock.
#if UNITY_EDITOR
using System;
using System.IO;
using System.Reflection;
using HPR;
using HPR.GameplaySuite;
using UnityEngine;

public static class HprGameplaySuiteRuntimeSmokeValidator
{
    private const BindingFlags Flags = BindingFlags.NonPublic | BindingFlags.Instance;

    public static void Run()
    {
        GameObject player = null, target = null, medStation = null, keyStation = null,
            gate = null, host = null;
        ItemData medkit = null, key = null;
        WeaponData rifle = null;
        EnemyData enemyData = null;
        AbilityData healing = null, pulse = null;
        AbilityEffectData healingEffect = null, pulseEffect = null;
        AssetMetadata metadata = null;
        AssetRegistry catalog = null;
        string slot = Environment.GetEnvironmentVariable("HPR_SUITE_SMOKE_JSON");
        if (string.IsNullOrWhiteSpace(slot)) throw new InvalidOperationException("Missing isolated QA JSON path");
        if (File.Exists(slot)) throw new InvalidOperationException("QA refuses to overwrite an existing save");
        try
        {
            player = new GameObject("QA-player");
            player.AddComponent<EventManager>();
            player.AddComponent<InventoryComponent>();
            player.AddComponent<ActorStatsComponent>();
            player.AddComponent<SimpleInteractionActor>();
            target = GameObject.CreatePrimitive(PrimitiveType.Cube);
            target.name = "QA-enemy-target";
            target.transform.position = new Vector3(2, 0, 0);
            target.AddComponent<HprSuiteEnemyTarget>();
            medStation = GameObject.CreatePrimitive(PrimitiveType.Cube);
            medStation.transform.position = new Vector3(.5f, 0, 0);
            var medPickup = medStation.AddComponent<InventoryPickupInteractable>();
            keyStation = GameObject.CreatePrimitive(PrimitiveType.Cube);
            keyStation.transform.position = new Vector3(1.5f, 0, 0);
            var keyPickup = keyStation.AddComponent<InventoryPickupInteractable>();
            gate = new GameObject("QA-lockable-gate");
            gate.transform.position = new Vector3(2.6f, 0, 0);
            var door = gate.AddComponent<KeyDoorInteractable>();

            medkit = ScriptableObject.CreateInstance<ItemData>();
            medkit.Id = "qa_medkit";
            medkit.DisplayName = "QA Field Medkit";
            medkit.ItemType = ItemType.Consumable;
            medkit.StartingPlayerQuantity = 0;
            key = ScriptableObject.CreateInstance<ItemData>();
            key.Id = "qa_key";
            key.DisplayName = "QA Key";
            key.ItemType = ItemType.Key;
            key.StartingPlayerQuantity = 0;
            Set(medPickup, "itemData", medkit);
            Set(keyPickup, "itemData", key);
            Set(door, "requiredKeyItem", key);

            rifle = ScriptableObject.CreateInstance<WeaponData>();
            rifle.Id = "qa_rifle";
            rifle.UsesAmmo = true;
            rifle.Damage = 20f;
            rifle.FireDelay = .35f;
            rifle.MagazineSize = 3;
            rifle.StartingMagazineAmmo = 3;
            rifle.StartingReserveAmmo = 9;
            rifle.MaxAmmo = 15;
            enemyData = ScriptableObject.CreateInstance<EnemyData>();
            enemyData.Id = "qa_raider";
            enemyData.MaxHealth = 48f;
            enemyData.AttackDamage = 8f;
            enemyData.AttackRange = 2.5f;
            enemyData.AttackCooldown = 1f;

            healingEffect = ScriptableObject.CreateInstance<AbilityEffectData>();
            healingEffect.Id = "qa_healing_effect";
            healingEffect.EffectType = AbilityEffectType.Heal;
            healingEffect.Value = 20f;
            healing = ScriptableObject.CreateInstance<AbilityData>();
            healing.Id = "qa_healing";
            healing.DisplayName = "QA Heal";
            healing.Cooldown = 4f;
            healing.Cost = 20f;
            healing.Effects.Add(healingEffect);
            pulseEffect = ScriptableObject.CreateInstance<AbilityEffectData>();
            pulseEffect.Id = "qa_pulse_effect";
            pulseEffect.EffectType = AbilityEffectType.AreaDamage;
            pulseEffect.Value = 12f;
            pulseEffect.Radius = 7f;
            pulseEffect.ForwardOffset = 0f;
            pulse = ScriptableObject.CreateInstance<AbilityData>();
            pulse.Id = "qa_pulse";
            pulse.DisplayName = "QA Pulse";
            pulse.Cooldown = 6f;
            pulse.Cost = 25f;
            pulse.Effects.Add(pulseEffect);
            metadata = ScriptableObject.CreateInstance<AssetMetadata>();
            metadata.AssetId = medkit.Id;
            metadata.DisplayName = medkit.DisplayName;
            catalog = ScriptableObject.CreateInstance<AssetRegistry>();
            catalog.SetEntries(new[] { metadata });

            host = new GameObject("QA-Suite");
            var controller = host.AddComponent<HprGameplaySuitePlayground>();
            Set(controller, "playerRoot", player);
            Set(controller, "enemyVisual", target);
            Set(controller, "medkitPickup", medStation);
            Set(controller, "keyPickup", keyStation);
            Set(controller, "demoDoor", door);
            Set(controller, "lootItem", medkit);
            Set(controller, "keyItem", key);
            Set(controller, "weaponData", rifle);
            Set(controller, "enemyData", enemyData);
            Set(controller, "healAbility", healing);
            Set(controller, "pulseAbility", pulse);
            Set(controller, "worldRegistry", catalog);
            controller.enabled = true;
            MethodInfo awake = typeof(HprGameplaySuitePlayground).GetMethod("Awake", Flags);
            Require(awake != null, "Awake method missing");
            awake.Invoke(controller, null);
            Physics.SyncTransforms();

            Require(controller.PlayerHealth == 100f && controller.PlayerStamina == 100f, "starting vitals");
            Require(controller.EnemyHealth == 48f && controller.MagazineAmmo == 3, "starting combat state");
            Require(controller.ServicesAvailable, "CompositionRoot resolved actual services");
            Require(controller.WorldCatalogAvailable, "World AssetRegistry stable item lookup");
            door.Interact(player.GetComponent<SimpleInteractionActor>());
            Require(!door.IsOpen, "gate refuses access without inventory key");

            Require(controller.EnemyAttack(), "real enemy attack through typed EventBus");
            Require(controller.PlayerHealth == 92f && controller.EnemyAttackCooldown > 0, "player stats and enemy cooldown");
            Require(!controller.EnemyAttack(), "enemy attack cooldown enforced");
            Require(controller.UseHealAbility(), "healing ability activation through resource adapter");
            Require(controller.PlayerHealth == 100f && controller.PlayerStamina == 80f, "healing costs stamina");
            Require(!controller.UseHealAbility(), "ability cooldown enforced");
            Require(controller.UsePulseAbility(), "area ability activation");
            Require(controller.EnemyHealth == 36f && controller.PlayerStamina == 55f,
                "AreaDamage physics collider -> DamageEvent -> enemy health");
            Require(!controller.UsePulseAbility(), "pulse cooldown enforced");

            Require(controller.Interact() && controller.LootCount == 1, "real medkit pickup");
            Require(!medStation.activeSelf, "collected medkit station disabled");
            Require(controller.Interact() && controller.KeyCount == 1, "real key pickup");
            Require(!keyStation.activeSelf, "collected key station disabled");
            Require(controller.Interact() && controller.DoorIsOpen, "inventory-locked door now opens");
            controller.SaveCheckpoint();
            Require(controller.HasCheckpoint, "captured in-memory snapshot");
            HprSuiteSnapshot original = controller.CaptureSnapshot();
            Require(original.Abilities.Cooldowns.Count == 2 && original.PlayerStamina == 55f,
                "ability state and stamina included in checkpoint");
            Require(original.DoorOpen && !original.MedkitPickupActive && !original.KeyPickupActive,
                "world interaction states included in checkpoint");
            Require(original.Enemy.AttackCooldownRemaining > 0f, "enemy cooldown included in checkpoint");

            Require(controller.Fire() && controller.EnemyHealth == 16f, "weapon firing and enemy state");
            Require(!controller.Fire(), "weapon cooldown enforced");
            WeaponRuntimeState weapon = (WeaponRuntimeState)typeof(HprGameplaySuitePlayground)
                .GetField("weapon", Flags).GetValue(controller);
            Require(weapon.CaptureSnapshot().CooldownRemaining > 0, "weapon cooldown actually captured");
            weapon.Tick(1f);
            Require(controller.Fire() && controller.EnemyHealth == 0f, "enemy death from weapon");
            Require(controller.LootCount == 2, "enemy loot added to previously picked inventory");
            Require(controller.Heal() && controller.LootCount == 1, "inventory consumption path");
            controller.ResetEncounter();
            Require(controller.MagazineAmmo == 3 && controller.PlayerStamina == 100f &&
                controller.LootCount == 0 && controller.KeyCount == 0 && !controller.DoorIsOpen,
                "reset clears all derived states");
            Require(controller.RestoreCheckpoint(), "memory restore");
            Require(controller.EnemyHealth == 36f && controller.PlayerStamina == 55f &&
                controller.MagazineAmmo == 3 && controller.KeyCount == 1 &&
                controller.LootCount == 1 && controller.DoorIsOpen && controller.EnemyAttackCooldown > 0,
                "full encounter restores across all modules");
            var abilityRunner = player.GetComponent<AbilityRunnerComponent>();
            Require(abilityRunner.CaptureSnapshot().Cooldowns.Count == 2, "ability cooldowns restored");

            Require(controller.SaveToDisk(slot), "opt-in local JSON slot written");
            Require(File.Exists(slot) && new FileInfo(slot).Length > 100, "JSON save actually exists");
            controller.ResetEncounter();
            Require(controller.LoadFromDisk(slot), "reload from real JSON filesystem");
            Require(controller.PlayerStamina == 55f && controller.EnemyHealth == 36f &&
                controller.KeyCount == 1 && controller.DoorIsOpen && controller.MagazineAmmo == 3,
                "serialized, restarted encounter state matches snapshot");
            Require(controller.SaveToDisk(slot), "second disk save replaces existing slot");
            HprSuiteSnapshot invalid = controller.CaptureSnapshot();
            invalid.Weapon.MagazineAmmo = 999;
            Require(!controller.RestoreSnapshot(invalid), "invalid ammunition refused");
            Require(controller.MagazineAmmo == 3 && controller.PlayerStamina == 55f,
                "invalid snapshot does not partially mutate state");
            File.WriteAllText(slot, "{not valid JSON");
            Require(!controller.LoadFromDisk(slot), "corrupted disk slot rejected");
            Require(controller.PlayerStamina == 55f, "invalid disk slot preserves live state");

            string output = Environment.GetEnvironmentVariable("HPR_SUITE_SMOKE_RECEIPT");
            if (string.IsNullOrWhiteSpace(output))
                throw new InvalidOperationException("No QA receipt path");
            File.WriteAllText(output,
                "initial_and_service_registry=PASS\nworld_registry_lookup=PASS\n" +
                "inventory_keyed_door_and_pickups=PASS\nenemy_attack_eventbus_stats=PASS\n" +
                "heal_ability_stamina_cooldown=PASS\npulse_area_damage_eventbus=PASS\n" +
                "weapon_fire_cooldown_and_loot=PASS\nfull_memory_restore_all_modules=PASS\n" +
                "real_json_disk_roundtrip=PASS\ninvalid_state_and_corruption_rejected=PASS\n");
            Debug.Log("HPR SUITE V2 QA PASS: ten independent integration checks in actual imported archive");
        }
        finally
        {
            if (File.Exists(slot)) File.Delete(slot);
            if (host != null) UnityEngine.Object.DestroyImmediate(host);
            if (player != null) UnityEngine.Object.DestroyImmediate(player);
            if (target != null) UnityEngine.Object.DestroyImmediate(target);
            if (medStation != null) UnityEngine.Object.DestroyImmediate(medStation);
            if (keyStation != null) UnityEngine.Object.DestroyImmediate(keyStation);
            if (gate != null) UnityEngine.Object.DestroyImmediate(gate);
            foreach (UnityEngine.Object obj in new UnityEngine.Object[] { medkit, key, rifle,
                enemyData, healing, pulse, healingEffect, pulseEffect, metadata, catalog })
                if (obj != null) UnityEngine.Object.DestroyImmediate(obj);
        }
    }

    private static void Set(object instance, string name, object value)
    {
        FieldInfo field = instance.GetType().GetField(name, Flags);
        if (field == null) throw new MissingFieldException(instance.GetType().Name, name);
        field.SetValue(instance, value);
    }

    private static void Require(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException("QA assertion failed: " + message);
    }
}
#endif
