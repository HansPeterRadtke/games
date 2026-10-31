// Copyright (c) Multiverse Studio. All rights reserved.
// Integrated, playable demonstration of ten HPR source modules.
// No network, telemetry, third-party art or generative-AI runtime.
using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using HPR;

namespace HPR.GameplaySuite
{
    public sealed class HprGameplaySuitePlayground : MonoBehaviour
    {
        [Header("Actors and pickups")]
        [SerializeField] private GameObject playerRoot;
        [SerializeField] private GameObject enemyVisual;
        [SerializeField] private GameObject medkitPickup;
        [SerializeField] private GameObject keyPickup;
        [SerializeField] private KeyDoorInteractable demoDoor;

        [Header("Reusable data assets")]
        [SerializeField] private ItemData lootItem;
        [SerializeField] private ItemData keyItem;
        [SerializeField] private WeaponData weaponData;
        [SerializeField] private EnemyData enemyData;
        [SerializeField] private AbilityData healAbility;
        [SerializeField] private AbilityData pulseAbility;
        [SerializeField] private AssetRegistry worldRegistry;

        private readonly Queue<string> eventHistory = new Queue<string>();
        private EventManager eventManager;
        private InventoryComponent inventory;
        private ActorStatsComponent playerStats;
        private SimpleInteractionActor actor;
        private AbilityRunnerComponent abilities;
        private WeaponRuntimeState weapon;
        private EnemyRuntimeState enemy;
        private CompositionRoot services;
        private MaterialPropertyBlock enemyColorBlock;
        private IDisposable statusSubscription;
        private IDisposable damageSubscription;
        private HprSuiteSnapshot savedCheckpoint;
        private bool lootAwarded;
        private string status = "Scene loaded";
        private Vector3 initialPlayerPosition;
        private Quaternion initialPlayerRotation;
        private const float InteractRange = 2.7f;
        private const float MoveSpeed = 4f;

        public float PlayerHealth => playerStats != null ? playerStats.Health : 0f;
        public float PlayerStamina => playerStats != null ? playerStats.Stamina : 0f;
        public float EnemyHealth => enemy != null ? enemy.Health : 0f;
        public int LootCount => inventory != null && lootItem != null ? inventory.GetQuantity(lootItem.Id) : 0;
        public int KeyCount => inventory != null && keyItem != null ? inventory.GetQuantity(keyItem.Id) : 0;
        public int MagazineAmmo => weapon != null ? weapon.MagazineAmmo : 0;
        public int ReserveAmmo => weapon != null ? weapon.ReserveAmmo : 0;
        public float WeaponCooldown => weapon != null ? weapon.CooldownRemaining : 0f;
        public float EnemyAttackCooldown => enemy != null ? enemy.AttackCooldownRemaining : 0f;
        public bool DoorIsOpen => demoDoor != null && demoDoor.IsOpen;
        public bool ServicesAvailable => services != null &&
            ReferenceEquals(services.Services.Resolve<IInventoryService>(), inventory) &&
            ReferenceEquals(services.Services.Resolve<ICharacterStats>(), playerStats) &&
            ReferenceEquals(services.Services.Resolve<IAbilityLoadout>(), abilities);
        public bool WorldCatalogAvailable => worldRegistry != null &&
            lootItem != null && worldRegistry.TryGet(lootItem.Id, out AssetMetadata entry) &&
            entry != null && entry.DisplayName == lootItem.DisplayName;
        public bool HasCheckpoint => savedCheckpoint != null;
        public bool CanInteract => FindNearbyInteractable() != null;
        public string SavePath => System.IO.Path.Combine(Application.persistentDataPath, "HPRGameplaySuite", "demo-slot.json");

        private void Awake()
        {
            if (playerRoot == null || enemyVisual == null || lootItem == null || keyItem == null ||
                weaponData == null || enemyData == null || healAbility == null || pulseAbility == null ||
                worldRegistry == null || medkitPickup == null || keyPickup == null || demoDoor == null)
            {
                Debug.LogError("Gameplay Suite demo references missing; choose Tools/HPR/Gameplay Suite/Build Showcase.", this);
                enabled = false;
                return;
            }

            initialPlayerPosition = playerRoot.transform.position;
            initialPlayerRotation = playerRoot.transform.rotation;
            eventManager = playerRoot.GetComponent<EventManager>() ?? playerRoot.AddComponent<EventManager>();
            inventory = playerRoot.GetComponent<InventoryComponent>() ?? playerRoot.AddComponent<InventoryComponent>();
            inventory.ConfigureKnownItems(new[] { lootItem, keyItem });
            playerStats = playerRoot.GetComponent<ActorStatsComponent>() ?? playerRoot.AddComponent<ActorStatsComponent>();
            playerStats.ResetStats();
            playerStats.BindRuntimeEventBusSource(eventManager);
            actor = playerRoot.GetComponent<SimpleInteractionActor>() ?? playerRoot.AddComponent<SimpleInteractionActor>();
            actor.BindInventory(inventory);
            var abilityPool = playerRoot.GetComponent<HprSuiteAbilityPool>() ?? playerRoot.AddComponent<HprSuiteAbilityPool>();
            abilityPool.Bind(playerStats);
            abilities = playerRoot.GetComponent<AbilityRunnerComponent>() ?? playerRoot.AddComponent<AbilityRunnerComponent>();
            abilities.BindRuntimeServices(eventManager, abilityPool);
            abilities.ConfigureAbilities(new[] { healAbility, pulseAbility });
            abilities.SetUnlockedAbilityIds(new[] { healAbility.Id, pulseAbility.Id });
            weapon = new WeaponRuntimeState(weaponData);
            enemy = new EnemyRuntimeState(enemyData);
            var enemyTarget = enemyVisual.GetComponent<HprSuiteEnemyTarget>() ?? enemyVisual.AddComponent<HprSuiteEnemyTarget>();
            enemyTarget.Bind(this);
            medkitPickup.GetComponent<InventoryPickupInteractable>()?.BindRuntimeEventBusSource(eventManager);
            keyPickup.GetComponent<InventoryPickupInteractable>()?.BindRuntimeEventBusSource(eventManager);

            services = new CompositionRoot();
            services.Services.Register<IInventoryService>(inventory);
            services.Services.Register<ICharacterStats>(playerStats);
            services.Services.Register<IEventBus>(eventManager.EventBus);
            services.Services.Register<IAbilityLoadout>(abilities);
            services.Services.Register<AssetRegistry>(worldRegistry);
            services.Initialize();

            statusSubscription = eventManager.EventBus.Subscribe<SuiteEvent>(evt => EmitLocal(evt.Text));
            damageSubscription = eventManager.EventBus.Subscribe<DamageEvent>(evt =>
            {
                if (evt != null && evt.TargetRoot == enemyVisual)
                    DamageEnemy(evt.Amount, "typed Ability DamageEvent");
            });
            Emit("Ready: E pick up a key, unlock the door, F fire, Q heal, Space pulse, K checkpoint.");
            RefreshVisual();
        }

        private void OnDestroy()
        {
            statusSubscription?.Dispose();
            damageSubscription?.Dispose();
            services?.Dispose();
        }

        private void Update()
        {
            if (weapon == null || enemy == null) return;
            float dt = Mathf.Max(0f, Time.deltaTime);
            weapon.Tick(dt);
            enemy.Tick(dt);
            services.Tick(dt);
            if (playerStats.IsAlive)
            {
                float horizontal = (Input.GetKey(KeyCode.D) || Input.GetKey(KeyCode.RightArrow) ? 1f : 0f) -
                                   (Input.GetKey(KeyCode.A) || Input.GetKey(KeyCode.LeftArrow) ? 1f : 0f);
                float vertical = (Input.GetKey(KeyCode.W) || Input.GetKey(KeyCode.UpArrow) ? 1f : 0f) -
                                 (Input.GetKey(KeyCode.S) || Input.GetKey(KeyCode.DownArrow) ? 1f : 0f);
                Vector3 movement = new Vector3(horizontal, 0, vertical);
                if (movement.sqrMagnitude > 1f) movement.Normalize();
                // Bounded training arena: deliberately simple, not a full character controller.
                Vector3 pos = playerRoot.transform.position + movement * (MoveSpeed * dt);
                playerRoot.transform.position = new Vector3(Mathf.Clamp(pos.x, -7f, 7f),
                    initialPlayerPosition.y, Mathf.Clamp(pos.z, -5f, 5f));
            }
            if (Input.GetKeyDown(KeyCode.F)) Fire();
            if (Input.GetKeyDown(KeyCode.R)) Reload();
            if (Input.GetKeyDown(KeyCode.E)) Interact();
            if (Input.GetKeyDown(KeyCode.H)) Heal();
            if (Input.GetKeyDown(KeyCode.Q)) UseHealAbility();
            if (Input.GetKeyDown(KeyCode.Space)) UsePulseAbility();
            if (Input.GetKeyDown(KeyCode.K)) SaveCheckpoint();
            if (Input.GetKeyDown(KeyCode.L)) RestoreCheckpoint();
            RefreshVisual();
        }

        public bool Fire()
        {
            if (weapon == null || enemy == null || enemy.IsDead || !playerStats.IsAlive)
                return Fail("No living attacker or target");
            if (!weapon.TryFire(out WeaponFireResult shot))
                return Fail("Reload or allow firing cooldown");
            DamageEnemy(shot.Damage, "Rifle");
            return true;
        }

        public void DamageEnemy(float amount, string source)
        {
            if (enemy == null || enemy.IsDead) return;
            float dealt = enemy.ApplyDamage(Mathf.Max(0f, amount));
            if (dealt <= 0f) return;
            Emit(source + ": " + dealt.ToString("0") + " damage applied");
            if (enemy.IsDead && !lootAwarded)
            {
                lootAwarded = true;
                inventory.AddItem(lootItem, 1);
                Emit("Target eliminated: one field medkit added to inventory");
            }
            RefreshVisual();
        }

        public bool Reload()
        {
            if (weapon == null) return false;
            int loaded = weapon.Reload();
            if (loaded <= 0) return Fail("No magazine space or reserve ammunition");
            Emit("Reloaded " + loaded + " rounds");
            return true;
        }

        public bool EnemyAttack()
        {
            if (enemy == null || playerStats == null || !playerStats.IsAlive)
                return Fail("Player unable to take another attack");
            // The training button simulates a close-range encounter; no pathfinding is claimed.
            const float closeRange = 1.5f;
            if (enemy.Decide(closeRange) != EnemyRuntimeDecision.Attack ||
                !enemy.TryAttack(closeRange, out EnemyAttackResult attack))
                return Fail("Enemy is dead or attack is cooling down");
            eventManager.Publish(new DamageEvent
            {
                TargetRoot = playerRoot, SourceRoot = enemyVisual, Amount = attack.Damage,
                HitPoint = playerRoot.transform.position, HitDirection = Vector3.forward
            });
            Emit("Enemy attack via typed EventBus: player has " + PlayerHealth.ToString("0") + " health");
            return true;
        }

        public bool Heal()
        {
            if (inventory == null || !services.Services.Resolve<IInventoryService>().RemoveItem(lootItem.Id, 1))
                return Fail("No field medkit available");
            services.Services.Resolve<ICharacterStats>().Heal(30f);
            Emit("Inventory consumable: restored health to " + PlayerHealth.ToString("0"));
            return true;
        }

        public bool UseHealAbility()
        {
            if (abilities == null || !abilities.TryActivate(healAbility.Id))
                return Fail(abilities != null ? abilities.LastStatusMessage : "Ability unavailable");
            Emit("Heal ability spent stamina and began its cooldown");
            return true;
        }

        public bool UsePulseAbility()
        {
            if (abilities == null || !abilities.TryActivate(pulseAbility.Id))
                return Fail(abilities != null ? abilities.LastStatusMessage : "Ability unavailable");
            Emit("Pulse ability: physics overlap and typed damage delivery");
            return true;
        }

        private IInteractable FindNearbyInteractable()
        {
            if (playerRoot == null) return null;
            IInteractable nearest = null;
            float bestDistance = InteractRange;
            foreach (GameObject obj in new[] { medkitPickup, keyPickup, demoDoor != null ? demoDoor.gameObject : null })
            {
                if (obj == null || !obj.activeInHierarchy) continue;
                float distance = Vector3.Distance(playerRoot.transform.position, obj.transform.position);
                if (distance > bestDistance) continue;
                var candidate = obj.GetComponents<MonoBehaviour>().OfType<IInteractable>().FirstOrDefault();
                if (candidate == null) continue;
                bestDistance = distance;
                nearest = candidate;
            }
            return nearest;
        }

        public bool Interact()
        {
            IInteractable target = FindNearbyInteractable();
            if (target == null) return Fail("Move closer to a colored pickup or the door");
            string prompt = target.GetPrompt(actor);
            bool beforeDoor = DoorIsOpen;
            int beforeKey = KeyCount, beforeMedkit = LootCount;
            target.Interact(actor);
            if (target is KeyDoorInteractable && DoorIsOpen == beforeDoor)
                return Fail("Door locked: collect the key first");
            if (beforeKey == KeyCount && beforeMedkit == LootCount && DoorIsOpen == beforeDoor)
                return Fail("Interaction had no effect");
            Emit("Interaction: " + prompt);
            return true;
        }

        public void SaveCheckpoint()
        {
            if (playerStats == null) return;
            savedCheckpoint = CaptureSnapshot();
            Emit("Captured full in-memory checkpoint (health, stamina, ammo, cooldowns, pickups and door)");
        }

        public bool RestoreCheckpoint()
        {
            if (savedCheckpoint == null) return Fail("Capture a checkpoint first");
            return RestoreSnapshot(savedCheckpoint);
        }

        public bool SaveToDisk(string destination = null)
        {
            if (playerStats == null) return false;
            try
            {
                HprSuiteSnapshotStorage.Save(destination ?? SavePath, CaptureSnapshot());
                Emit("Saved versioned JSON encounter to local persistent-data slot");
                return true;
            }
            catch (Exception exception) when (exception is System.IO.IOException ||
                exception is UnauthorizedAccessException || exception is ArgumentException)
            {
                return Fail("Local save unavailable: " + exception.Message);
            }
        }

        public bool LoadFromDisk(string destination = null)
        {
            try
            {
                HprSuiteSnapshot snapshot = HprSuiteSnapshotStorage.Load(destination ?? SavePath);
                if (!RestoreSnapshot(snapshot)) return false;
                savedCheckpoint = snapshot;
                Emit("Restored complete encounter from local JSON slot");
                return true;
            }
            catch (Exception exception) when (exception is System.IO.IOException ||
                exception is UnauthorizedAccessException || exception is ArgumentException)
            {
                return Fail("Local load unavailable: " + exception.Message);
            }
        }

        public HprSuiteSnapshot CaptureSnapshot()
        {
            if (playerStats == null || enemy == null || weapon == null || abilities == null)
                throw new InvalidOperationException("Demo is not initialized");
            return new HprSuiteSnapshot
            {
                WeaponId = weaponData.Id, EnemyId = enemyData.Id,
                Player = new SaveEntityData
                {
                    id = "suite-player", active = playerRoot.activeSelf,
                    health = playerStats.Health,
                    position = new SerializableVector3(playerRoot.transform.position),
                    rotation = new SerializableQuaternion(playerRoot.transform.rotation)
                },
                PlayerStamina = playerStats.Stamina,
                Inventory = inventory.CaptureItemQuantities()
                    .Select(entry => new ItemQuantitySaveData { itemId = entry.Key, quantity = entry.Value }).ToList(),
                Weapon = weapon.CaptureSnapshot(),
                Enemy = enemy.CaptureSnapshot(),
                Abilities = abilities.CaptureSnapshot(),
                LootAwarded = lootAwarded,
                MedkitPickupActive = medkitPickup.activeSelf,
                KeyPickupActive = keyPickup.activeSelf,
                DoorOpen = demoDoor.IsOpen
            };
        }

        public bool RestoreSnapshot(HprSuiteSnapshot snapshot)
        {
            if (!ValidateSnapshot(snapshot)) return Fail("Save is incompatible or invalid; current game state retained");
            // Validation of the saved combat state is done on disposable objects first.
            var validatedWeapon = new WeaponRuntimeState(weaponData);
            var validatedEnemy = new EnemyRuntimeState(enemyData);
            try
            {
                validatedWeapon.RestoreSnapshot(snapshot.Weapon);
                validatedEnemy.RestoreSnapshot(snapshot.Enemy);
            }
            catch (ArgumentException)
            {
                return Fail("Save contains invalid combat state");
            }
            playerRoot.transform.SetPositionAndRotation(snapshot.Player.position.ToVector3(),
                snapshot.Player.rotation.ToQuaternion());
            playerStats.SetHealth(snapshot.Player.health);
            playerStats.SetStamina(snapshot.PlayerStamina);
            inventory.RestoreItemQuantities(snapshot.Inventory);
            weapon = validatedWeapon;
            enemy = validatedEnemy;
            abilities.RestoreSnapshot(snapshot.Abilities);
            lootAwarded = snapshot.LootAwarded;
            medkitPickup.SetActive(snapshot.MedkitPickupActive);
            keyPickup.SetActive(snapshot.KeyPickupActive);
            demoDoor.SetOpen(snapshot.DoorOpen);
            RefreshVisual();
            Emit("Encounter state restored, including ammo, cooldowns, stamina, door and pickups");
            return true;
        }

        private bool ValidateSnapshot(HprSuiteSnapshot s)
        {
            if (s == null || s.SchemaVersion != 2 || s.WeaponId != weaponData.Id ||
                s.EnemyId != enemyData.Id || s.Player == null || s.Player.id != "suite-player" ||
                !s.Player.active || s.Inventory == null || s.Inventory.Count > 32 ||
                s.Abilities == null || s.Abilities.Cooldowns == null || s.Abilities.UnlockedIds == null ||
                s.Abilities.Cooldowns.Count > 16 || s.Abilities.UnlockedIds.Count > 16 ||
                !IsWithin(s.Player.health, 0f, playerStats.MaxHealth) ||
                !IsWithin(s.PlayerStamina, 0f, playerStats.MaxStamina) ||
                !IsWithin(s.Player.position.x, -7f, 7f) || !IsWithin(s.Player.position.z, -5f, 5f) ||
                !IsWithin(s.Player.position.y, 0f, 2.5f) ||
                !IsWithin(s.Player.rotation.x, -1f, 1f) || !IsWithin(s.Player.rotation.y, -1f, 1f) ||
                !IsWithin(s.Player.rotation.z, -1f, 1f) || !IsWithin(s.Player.rotation.w, -1f, 1f))
                return false;
            var seen = new HashSet<string>(StringComparer.Ordinal);
            foreach (ItemQuantitySaveData item in s.Inventory)
                if (item == null || (item.itemId != lootItem.Id && item.itemId != keyItem.Id) ||
                    item.quantity <= 0 || item.quantity > 10000 || !seen.Add(item.itemId))
                    return false;
            foreach (string id in s.Abilities.UnlockedIds)
                if (id != healAbility.Id && id != pulseAbility.Id) return false;
            foreach (AbilityCooldownSnapshot cooldown in s.Abilities.Cooldowns)
                if (cooldown == null || (cooldown.AbilityId != healAbility.Id && cooldown.AbilityId != pulseAbility.Id) ||
                    !IsWithin(cooldown.Remaining, 0f, 86400f)) return false;
            return true;
        }

        private static bool IsWithin(float value, float lower, float upper)
        {
            return !float.IsNaN(value) && !float.IsInfinity(value) && value >= lower && value <= upper;
        }

        public void ResetEncounter()
        {
            if (playerStats == null) return;
            playerRoot.transform.SetPositionAndRotation(initialPlayerPosition, initialPlayerRotation);
            playerStats.ResetStats();
            inventory.ClearInventory();
            weapon = new WeaponRuntimeState(weaponData);
            enemy = new EnemyRuntimeState(enemyData);
            abilities.RestoreSnapshot(new AbilityRuntimeSnapshot
            {
                UnlockedIds = new List<string> { healAbility.Id, pulseAbility.Id }
            });
            medkitPickup.SetActive(true);
            keyPickup.SetActive(true);
            demoDoor.SetOpen(false);
            lootAwarded = false;
            RefreshVisual();
            Emit("New encounter initialized");
        }

        private bool Fail(string message)
        {
            status = message;
            return false;
        }

        private void EmitLocal(string message)
        {
            eventHistory.Enqueue(message);
            while (eventHistory.Count > 5) eventHistory.Dequeue();
            status = message;
        }

        private void Emit(string message)
        {
            eventManager.Publish(new SuiteEvent { Text = message });
        }

        private void RefreshVisual()
        {
            if (enemyVisual == null || enemy == null) return;
            Renderer renderer = enemyVisual.GetComponent<Renderer>();
            if (renderer == null) return;
            if (enemyColorBlock == null) enemyColorBlock = new MaterialPropertyBlock();
            Color color = enemy.IsDead ? new Color(0.25f, 0.28f, 0.32f) :
                new Color(0.98f, 0.32f, 0.18f);
            enemyColorBlock.SetColor("_Color", color); // Built-in Standard shader
            enemyColorBlock.SetColor("_BaseColor", color); // URP Lit shader
            renderer.SetPropertyBlock(enemyColorBlock);
        }

        private void OnGUI()
        {
            if (weapon == null || enemy == null || playerStats == null) return;
            GUILayout.BeginArea(new Rect(12, 12, 550, 480), GUI.skin.box);
            GUILayout.Label("HPR GAMEPLAY SYSTEMS SUITE   |   INTEGRATED TRAINING ARENA");
            GUILayout.Label("PLAYER " + PlayerHealth.ToString("0") + "/" + playerStats.MaxHealth.ToString("0") +
                " HP    STAMINA " + PlayerStamina.ToString("0") +
                "    ENEMY " + EnemyHealth.ToString("0") + "/" + enemyData.MaxHealth.ToString("0") + " HP");
            GUILayout.Label("RIFLE " + MagazineAmmo + "/" + weapon.MagazineSize +
                "    RESERVE " + ReserveAmmo + "    MEDKITS " + LootCount + "    KEYS " + KeyCount +
                "    DOOR " + (DoorIsOpen ? "OPEN" : "LOCKED"));
            GUILayout.Label("WASD / arrows move  |  E interact  |  F fire  |  R reload  |  H medkit");
            GUILayout.Label("Q heal ability  |  Space pulse  |  K memory checkpoint  |  L restore");
            GUILayout.BeginHorizontal();
            if (GUILayout.Button("Fire [F]")) Fire();
            if (GUILayout.Button("Reload [R]")) Reload();
            if (GUILayout.Button("Enemy attacks")) EnemyAttack();
            if (GUILayout.Button("Use medkit [H]")) Heal();
            GUILayout.EndHorizontal();
            GUILayout.BeginHorizontal();
            if (GUILayout.Button("Interact [E]")) Interact();
            if (GUILayout.Button("Heal ability [Q]")) UseHealAbility();
            if (GUILayout.Button("Damage pulse [Space]")) UsePulseAbility();
            GUILayout.EndHorizontal();
            GUILayout.Label("ABILITIES: " + abilities.BuildHudSummary("Q", "Space"));
            IInteractable target = FindNearbyInteractable();
            GUILayout.Label("NEARBY: " + (target != null ? target.GetPrompt(actor) : "move to the cyan or yellow pickups / door"));
            GUILayout.BeginHorizontal();
            if (GUILayout.Button("Memory checkpoint [K]")) SaveCheckpoint();
            if (GUILayout.Button("Restore memory [L]")) RestoreCheckpoint();
            if (GUILayout.Button("Reset arena")) ResetEncounter();
            GUILayout.EndHorizontal();
            GUILayout.BeginHorizontal();
            if (GUILayout.Button("Save disk slot")) SaveToDisk();
            if (GUILayout.Button("Load disk slot")) LoadFromDisk();
            GUILayout.EndHorizontal();
            GUILayout.Label("COMPOSITION ROOT: " + (ServicesAvailable ? "registered" : "missing") +
                "    WORLD REGISTRY: " + (WorldCatalogAvailable ? "lookups live" : "unavailable"));
            GUILayout.Label("LATEST: " + status);
            foreach (string line in eventHistory) GUILayout.Label("  " + line);
            GUILayout.Label("No network access, telemetry, external 3D assets or runtime AI.");
            GUILayout.EndArea();
        }

        private sealed class SuiteEvent { public string Text; }
    }
}
