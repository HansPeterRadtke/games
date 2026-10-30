// Copyright (c) Multiverse Studio. All rights reserved.
// Original multi-system sample for the consolidated Unity gameplay suite.
using System;
using System.Collections.Generic;
using UnityEngine;
using HPR;

namespace HPR.GameplaySuite
{
    /// <summary>
    /// One playable scene integrating the reusable runtime modules. Its intentionally
    /// simple geometry avoids licensing external art or promising a full FPS game.
    /// Use the buttons in Play mode to exercise inventory, stats, events, weapon
    /// cooldown/reload, enemy decision/health, and a memory-only save checkpoint.
    /// </summary>
    public sealed class HprGameplaySuitePlayground : MonoBehaviour
    {
        [SerializeField] private GameObject playerRoot;
        [SerializeField] private GameObject enemyVisual;
        [SerializeField] private ItemData lootItem;
        [SerializeField] private WeaponData weaponData;
        [SerializeField] private EnemyData enemyData;

        private readonly Queue<string> eventHistory = new Queue<string>();
        private EventManager eventManager;
        private InventoryComponent inventory;
        private ActorStatsComponent playerStats;
        private WeaponRuntimeState weapon;
        private EnemyRuntimeState enemy;
        private IDisposable eventSubscription;
        private SaveEntityData savedPlayer;
        private float savedEnemyHealth;
        private bool hasCheckpoint;
        private bool lootAwarded;
        private string status = "Scene loaded";

        public float PlayerHealth => playerStats != null ? playerStats.Health : 0f;
        public float EnemyHealth => enemy != null ? enemy.Health : 0f;
        public int LootCount => inventory != null && lootItem != null ? inventory.GetQuantity(lootItem.Id) : 0;
        public int MagazineAmmo => weapon != null ? weapon.MagazineAmmo : 0;
        public bool HasCheckpoint => hasCheckpoint;

        private void Awake()
        {
            if (playerRoot == null || enemyVisual == null || lootItem == null || weaponData == null || enemyData == null)
            {
                Debug.LogError("Gameplay Suite demo is missing scene references. Rebuild with Tools/HPR/Gameplay Suite/Build Showcase.", this);
                enabled = false;
                return;
            }

            eventManager = playerRoot.GetComponent<EventManager>() ?? playerRoot.AddComponent<EventManager>();
            inventory = playerRoot.GetComponent<InventoryComponent>() ?? playerRoot.AddComponent<InventoryComponent>();
            inventory.ConfigureKnownItems(new[] { lootItem });
            playerStats = playerRoot.GetComponent<ActorStatsComponent>() ?? playerRoot.AddComponent<ActorStatsComponent>();
            playerStats.ResetStats();
            playerStats.BindRuntimeEventBusSource(eventManager);
            weapon = new WeaponRuntimeState(weaponData);
            enemy = new EnemyRuntimeState(enemyData);
            eventSubscription = eventManager.EventBus.Subscribe<SuiteEvent>(evt =>
            {
                eventHistory.Enqueue(evt.Text);
                while (eventHistory.Count > 6) eventHistory.Dequeue();
                status = evt.Text;
            });
            status = "Ready: fire, reload, take damage, collect loot, heal, checkpoint, restore";
            RefreshVisual();
        }

        private void OnDestroy()
        {
            eventSubscription?.Dispose();
        }

        private void Update()
        {
            if (weapon == null || enemy == null) return;
            float dt = Mathf.Max(0f, Time.deltaTime);
            weapon.Tick(dt);
            enemy.Tick(dt);
            RefreshVisual();
        }

        public bool Fire()
        {
            if (weapon == null || enemy == null || enemy.IsDead) return Fail("Target already eliminated");
            if (!weapon.TryFire(out WeaponFireResult shot)) return Fail("Reload or allow firing cooldown");
            float dealt = enemy.ApplyDamage(shot.Damage);
            Emit("Fired " + shot.Damage.ToString("0") + " damage; applied " + dealt.ToString("0") + " to enemy");
            if (enemy.IsDead && !lootAwarded)
            {
                lootAwarded = true;
                inventory.AddItem(lootItem, 1);
                Emit("Enemy eliminated: recovered one field medkit through the inventory module");
            }
            RefreshVisual();
            return true;
        }

        public bool Reload()
        {
            if (weapon == null) return false;
            int loaded = weapon.Reload();
            if (loaded <= 0) return Fail("Nothing to reload");
            Emit("Reloaded " + loaded + " rounds from reserve");
            return true;
        }

        public bool EnemyAttack()
        {
            if (enemy == null || playerStats == null || !playerStats.IsAlive) return Fail("Player unable to take another attack");
            const float closeRange = 1.5f;
            EnemyRuntimeDecision decision = enemy.Decide(closeRange);
            if (decision != EnemyRuntimeDecision.Attack || !enemy.TryAttack(closeRange, out EnemyAttackResult attack))
                return Fail("Enemy cannot attack (dead or on cooldown)");
            // Damage is delivered through the typed event bus; stats own the damage application.
            eventManager.Publish(new DamageEvent
            {
                TargetRoot = playerRoot,
                SourceRoot = enemyVisual,
                Amount = attack.Damage,
                HitPoint = playerRoot.transform.position,
                HitDirection = Vector3.forward
            });
            Emit("Enemy attacked through EventBus; player health now " + playerStats.Health.ToString("0"));
            return true;
        }

        public bool Heal()
        {
            if (inventory == null || !inventory.RemoveItem(lootItem.Id, 1)) return Fail("No field medkit in inventory");
            playerStats.Heal(30f);
            Emit("Consumed one medkit; restored health to " + playerStats.Health.ToString("0"));
            return true;
        }

        public void SaveCheckpoint()
        {
            if (playerStats == null) return;
            savedPlayer = new SaveEntityData
            {
                id = "gameplay_suite_player",
                active = playerRoot.activeSelf,
                intValue = inventory.GetQuantity(lootItem.Id),
                health = playerStats.Health,
                position = new SerializableVector3(playerRoot.transform.position),
                rotation = new SerializableQuaternion(playerRoot.transform.rotation),
            };
            savedEnemyHealth = enemy.Health;
            hasCheckpoint = true;
            Emit("Saved an in-memory checkpoint with HPR Save payloads");
        }

        public bool RestoreCheckpoint()
        {
            if (!hasCheckpoint) return Fail("Capture a checkpoint first");
            // HPR Save models the payload; persistence to disk is the host game's policy.
            playerRoot.transform.SetPositionAndRotation(savedPlayer.position.ToVector3(), savedPlayer.rotation.ToQuaternion());
            playerStats.SetHealth(savedPlayer.health);
            inventory.ClearInventory();
            for (int i = 0; i < savedPlayer.intValue; i++) inventory.AddItem(lootItem, 1);
            enemy = new EnemyRuntimeState(enemyData);
            enemy.ApplyDamage(Mathf.Max(0f, enemy.Health - savedEnemyHealth));
            lootAwarded = enemy.IsDead;
            RefreshVisual();
            Emit("Restored health, enemy and inventory from captured in-memory checkpoint");
            return true;
        }

        public void ResetEncounter()
        {
            if (playerStats == null) return;
            playerStats.ResetStats();
            inventory.ClearInventory();
            enemy = new EnemyRuntimeState(enemyData);
            weapon = new WeaponRuntimeState(weaponData);
            lootAwarded = false;
            RefreshVisual();
            Emit("Encounter reset");
        }

        private bool Fail(string message)
        {
            status = message;
            return false;
        }

        private void Emit(string message)
        {
            eventManager.Publish(new SuiteEvent { Text = message });
        }

        private void RefreshVisual()
        {
            if (enemyVisual == null || enemy == null) return;
            Renderer renderer = enemyVisual.GetComponent<Renderer>();
            if (renderer != null) renderer.material.color = enemy.IsDead ? Color.gray : Color.red;
        }

        private void OnGUI()
        {
            if (weapon == null || enemy == null || playerStats == null) return;
            GUILayout.BeginArea(new Rect(14, 14, 475, 390), GUI.skin.box);
            GUILayout.Label("HPR GAMEPLAY SYSTEMS SUITE — integrated, original scene");
            GUILayout.Label("Health: " + PlayerHealth.ToString("0") + " / " + playerStats.MaxHealth.ToString("0")
                + "   Enemy: " + EnemyHealth.ToString("0") + " / " + enemyData.MaxHealth.ToString("0"));
            GUILayout.Label("Ammo: " + MagazineAmmo + " / " + weapon.MagazineSize
                + "   Reserve: " + weapon.ReserveAmmo + "   Medkits: " + LootCount);
            GUILayout.BeginHorizontal();
            if (GUILayout.Button("Fire")) Fire();
            if (GUILayout.Button("Reload")) Reload();
            if (GUILayout.Button("Enemy Attack")) EnemyAttack();
            if (GUILayout.Button("Use Medkit")) Heal();
            GUILayout.EndHorizontal();
            GUILayout.BeginHorizontal();
            if (GUILayout.Button("Save checkpoint")) SaveCheckpoint();
            if (GUILayout.Button("Restore")) RestoreCheckpoint();
            if (GUILayout.Button("Reset")) ResetEncounter();
            GUILayout.EndHorizontal();
            GUILayout.Label("Latest: " + status);
            GUILayout.Label("Bus events (most recent last):");
            foreach (string line in eventHistory) GUILayout.Label("• " + line);
            GUILayout.Label("No external art, online AI, telemetry, disk writes, or hidden services.");
            GUILayout.EndArea();
        }

        private sealed class SuiteEvent
        {
            public string Text;
        }
    }
}
