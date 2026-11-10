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
        [SerializeField] private Camera arenaCamera;
        [SerializeField] private bool automaticEnemy = true;

        [Header("Reusable data assets")]
        [SerializeField] private ItemData lootItem;
        [SerializeField] private ItemData keyItem;
        [SerializeField] private WeaponData weaponData;
        [SerializeField] private EnemyData enemyData;
        [SerializeField] private AbilityData healAbility;
        [SerializeField] private AbilityData pulseAbility;
        [SerializeField] private AssetRegistry worldRegistry;

        private readonly Queue<string> eventHistory = new Queue<string>();
        private Vector2 hudScrollPosition;
        private EventManager eventManager;
        private InventoryComponent inventory;
        private ActorStatsComponent playerStats;
        private SimpleInteractionActor actor;
        private AbilityRunnerComponent abilities;
        private HprSuiteArenaMotor playerMotor;
        private HprSuiteArenaMotor enemyMotor;
        private Vector3 initialEnemyPosition;
        private Quaternion initialEnemyRotation;
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
        [Header("Demo controls and interaction")]
        [SerializeField, Min(.1f)] private float interactionRangeMeters = 2.7f;
        [SerializeField] private KeyCode moveForwardKey = KeyCode.W;
        [SerializeField] private KeyCode moveBackwardKey = KeyCode.S;
        [SerializeField] private KeyCode moveLeftKey = KeyCode.A;
        [SerializeField] private KeyCode moveRightKey = KeyCode.D;
        [SerializeField] private KeyCode fireKey = KeyCode.F;
        [SerializeField] private KeyCode reloadKey = KeyCode.R;
        [SerializeField] private KeyCode interactKey = KeyCode.E;
        [SerializeField] private KeyCode useMedkitKey = KeyCode.H;
        [SerializeField] private KeyCode healAbilityKey = KeyCode.Q;
        [SerializeField] private KeyCode pulseAbilityKey = KeyCode.Space;
        [SerializeField] private KeyCode memorySaveKey = KeyCode.K;
        [SerializeField] private KeyCode memoryLoadKey = KeyCode.L;
        private IHprSuiteInputSource inputSource = HprSuiteUnityInputSource.Instance;
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
        public bool AutomaticEnemy => automaticEnemy;
        public string Objective => KeyCount == 0 && keyPickup != null && keyPickup.activeSelf
            ? "01  COLLECT THE AMBER ACCESS KEY"
            : !DoorIsOpen ? "02  UNLOCK THE ACCESS GATE"
            : EnemyHealth > 0f ? "03  DEFEAT THE TRAINING TARGET"
            : "04  HEAL, SAVE OR RESET THE ENCOUNTER";
        public void SetAutomaticEnemy(bool enabled) { automaticEnemy = enabled; }
        public bool CanInteract => FindNearbyInteractable() != null;
        /// <summary>Allow existing game input systems or test fakes to control the demo.</summary>
        public void BindInputSource(IHprSuiteInputSource source)
        {
            inputSource = source ?? HprSuiteUnityInputSource.Instance;
        }
        public string SavePath => System.IO.Path.Combine(Application.persistentDataPath, "HPRGameplaySuite", "demo-slot.json");

        private void Awake()
        {
            if (playerRoot == null || enemyVisual == null || lootItem == null || keyItem == null ||
                weaponData == null || enemyData == null || healAbility == null || pulseAbility == null ||
                worldRegistry == null || medkitPickup == null || keyPickup == null || demoDoor == null)
            {
                Debug.LogError("Gameplay Suite demo references missing. Re-import the complete shipped demo scene and sample assets.", this);
                enabled = false;
                return;
            }

            initialPlayerPosition = playerRoot.transform.position;
            initialPlayerRotation = playerRoot.transform.rotation;
            initialEnemyPosition = enemyVisual.transform.position;
            initialEnemyRotation = enemyVisual.transform.rotation;
            playerMotor = playerRoot.GetComponent<HprSuiteArenaMotor>();
            enemyMotor = enemyVisual.GetComponent<HprSuiteArenaMotor>();
            if (arenaCamera == null) arenaCamera = Camera.main;
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
            if (enemyMotor != null) enemyMotor.SetMoveSpeed(Mathf.Max(.5f, enemyData.MoveSpeed));
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
                float horizontal = (inputSource.IsPressed(moveRightKey) || inputSource.IsPressed(KeyCode.RightArrow) ? 1f : 0f) -
                                   (inputSource.IsPressed(moveLeftKey) || inputSource.IsPressed(KeyCode.LeftArrow) ? 1f : 0f);
                float vertical = (inputSource.IsPressed(moveForwardKey) || inputSource.IsPressed(KeyCode.UpArrow) ? 1f : 0f) -
                                 (inputSource.IsPressed(moveBackwardKey) || inputSource.IsPressed(KeyCode.DownArrow) ? 1f : 0f);
                Vector2 movement = Vector2.ClampMagnitude(new Vector2(horizontal, vertical), 1f);
                if (playerMotor != null) playerMotor.MovePlanar(movement, dt);
                else
                {
                    Vector3 pos = playerRoot.transform.position + new Vector3(movement.x, 0f, movement.y) * (MoveSpeed * dt);
                    playerRoot.transform.position = new Vector3(Mathf.Clamp(pos.x, -7f, 7f),
                        initialPlayerPosition.y, Mathf.Clamp(pos.z, -5f, 5f));
                }
                // Mouse cursor defines a real top-down aim point; no target auto-hit.
                if (TryGetPointerAim(out Vector3 pointerAim))
                {
                    Vector3 forward = pointerAim - playerRoot.transform.position;
                    forward.y = 0f;
                    if (forward.sqrMagnitude > .1f)
                        playerRoot.transform.rotation = Quaternion.LookRotation(forward.normalized);
                }
            }
            AdvanceEnemy(dt);
            if (inputSource.WasPressed(fireKey))
            {
                if (TryGetPointerAim(out Vector3 aim)) FireAt(aim);
                else Fire();
            }
            if (inputSource.WasPressed(reloadKey)) Reload();
            if (inputSource.WasPressed(interactKey)) Interact();
            if (inputSource.WasPressed(useMedkitKey)) Heal();
            if (inputSource.WasPressed(healAbilityKey)) UseHealAbility();
            if (inputSource.WasPressed(pulseAbilityKey)) UsePulseAbility();
            if (inputSource.WasPressed(memorySaveKey)) SaveCheckpoint();
            if (inputSource.WasPressed(memoryLoadKey)) RestoreCheckpoint();
            RefreshVisual();
        }

        private bool TryGetPointerAim(out Vector3 aim)
        {
            aim = Vector3.zero;
            if (arenaCamera == null || !inputSource.TryGetPointer(out Vector2 pointer)) return false;
            Plane plane = new Plane(Vector3.up, playerRoot.transform.position);
            Ray ray = arenaCamera.ScreenPointToRay(pointer);
            if (!plane.Raycast(ray, out float distance)) return false;
            aim = ray.GetPoint(distance);
            return true;
        }

        /// <summary>
        /// Explicit example target command; for normal gameplay use FireAt(cursorWorldPoint).
        /// Unlike the old button-only prototype, this respects hit geometry and line of sight.
        /// </summary>
        public bool Fire() => FireAt(enemyVisual != null ? enemyVisual.transform.position : Vector3.zero);

        /// <summary>Consumes ammunition even when the shot misses or strikes an obstacle.</summary>
        public bool FireAt(Vector3 worldPoint)
        {
            if (weapon == null || enemy == null || !playerStats.IsAlive)
                return Fail("Weapon or player unavailable");
            Vector3 origin = playerRoot.transform.position + Vector3.up * .15f;
            Vector3 direction = worldPoint - origin;
            if (direction.sqrMagnitude < .01f || !IsFinite(direction))
                return Fail("Aim at a valid world point");
            if (!weapon.TryFire(out WeaponFireResult shot))
                return Fail("Reload or allow the weapon firing cooldown");
            direction.Normalize();
            Physics.SyncTransforms();
            RaycastHit[] hits = Physics.RaycastAll(origin, direction, shot.Range,
                Physics.DefaultRaycastLayers, QueryTriggerInteraction.Ignore);
            Array.Sort(hits, (a, b) => a.distance.CompareTo(b.distance));
            bool hitTarget = false;
            Vector3 endpoint = origin + direction * Mathf.Min(shot.Range, 12f);
            foreach (RaycastHit hit in hits)
            {
                if (hit.collider == null) continue;
                if (hit.collider.transform == playerRoot.transform ||
                    hit.collider.transform.IsChildOf(playerRoot.transform)) continue;
                endpoint = hit.point;
                if (hit.collider.gameObject == enemyVisual ||
                    hit.collider.transform.IsChildOf(enemyVisual.transform))
                {
                    hitTarget = true;
                    DamageEnemy(shot.Damage, "Hitscan rifle");
                }
                break;
            }
            Debug.DrawLine(origin, endpoint, hitTarget ? Color.cyan : Color.yellow, .25f);
            if (!hitTarget) Emit("Rifle fired: miss or solid obstruction (ammunition consumed)");
            return true;
        }

        private static bool IsFinite(Vector3 v) =>
            !(float.IsNaN(v.x) || float.IsNaN(v.y) || float.IsNaN(v.z) ||
              float.IsInfinity(v.x) || float.IsInfinity(v.y) || float.IsInfinity(v.z));

        /// <summary>Uses real EnemyRuntime decisions, cooldowns, position and collisions.</summary>
        public void AdvanceEnemy(float deltaTime)
        {
            if (!automaticEnemy || enemy == null || enemy.IsDead || !playerStats.IsAlive ||
                deltaTime <= 0f || deltaTime > 1f) return;
            Vector3 toPlayer = playerRoot.transform.position - enemyVisual.transform.position;
            toPlayer.y = 0f;
            float distance = toPlayer.magnitude;
            EnemyRuntimeDecision decision = enemy.Decide(distance);
            if (decision == EnemyRuntimeDecision.Chase && distance > enemyData.AttackRange + .25f)
            {
                Vector2 direction = new Vector2(toPlayer.x, toPlayer.z).normalized;
                if (enemyMotor != null) enemyMotor.MovePlanar(direction, deltaTime);
                else
                {
                    Vector3 next = enemyVisual.transform.position + new Vector3(direction.x, 0f, direction.y) *
                        Mathf.Max(0f, enemyData.MoveSpeed) * deltaTime;
                    enemyVisual.transform.position = next;
                }
                if (toPlayer.sqrMagnitude > .01f)
                    enemyVisual.transform.rotation = Quaternion.LookRotation(toPlayer.normalized);
            }
            else if (decision == EnemyRuntimeDecision.Attack)
            {
                DeliverEnemyAttack(distance);
            }
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
            // Test/demo button simulates a close target. Autonomous mode measures actual distance.
            return DeliverEnemyAttack(1.5f);
        }

        private bool DeliverEnemyAttack(float range)
        {
            if (enemy.Decide(range) != EnemyRuntimeDecision.Attack ||
                !enemy.TryAttack(range, out EnemyAttackResult attack))
                return Fail("Enemy is dead, too far away, or attack is cooling down");
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
            float bestDistance = Mathf.Max(.1f, interactionRangeMeters);
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
            catch (Exception exception) when (exception is System.IO.InvalidDataException ||
                exception is System.IO.IOException ||
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
            catch (Exception exception) when (exception is System.IO.InvalidDataException ||
                exception is System.IO.IOException ||
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
                EnemyPosition = new SerializableVector3(enemyVisual.transform.position),
                EnemyRotation = new SerializableQuaternion(enemyVisual.transform.rotation),
                AutomaticEnemy = automaticEnemy,
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
            if (playerMotor != null) playerMotor.Warp(snapshot.Player.position.ToVector3(),
                snapshot.Player.rotation.ToQuaternion());
            else playerRoot.transform.SetPositionAndRotation(snapshot.Player.position.ToVector3(),
                snapshot.Player.rotation.ToQuaternion());
            if (enemyMotor != null) enemyMotor.Warp(snapshot.EnemyPosition.ToVector3(),
                snapshot.EnemyRotation.ToQuaternion());
            else enemyVisual.transform.SetPositionAndRotation(snapshot.EnemyPosition.ToVector3(),
                snapshot.EnemyRotation.ToQuaternion());
            playerStats.SetHealth(snapshot.Player.health);
            playerStats.SetStamina(snapshot.PlayerStamina);
            inventory.RestoreItemQuantities(snapshot.Inventory);
            weapon = validatedWeapon;
            enemy = validatedEnemy;
            automaticEnemy = snapshot.AutomaticEnemy;
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
            if (s == null || s.SchemaVersion != 3 || s.WeaponId != weaponData.Id ||
                s.EnemyId != enemyData.Id || s.Player == null || s.Player.id != "suite-player" ||
                !s.Player.active || s.Inventory == null || s.Inventory.Count > 32 ||
                s.Abilities == null || s.Abilities.Cooldowns == null || s.Abilities.UnlockedIds == null ||
                s.Abilities.Cooldowns.Count > 16 || s.Abilities.UnlockedIds.Count > 16 ||
                !IsWithin(s.Player.health, 0f, playerStats.MaxHealth) ||
                !IsWithin(s.PlayerStamina, 0f, playerStats.MaxStamina) ||
                !IsWithinArena(s.Player.position) ||
                !IsWithinArena(s.EnemyPosition) ||
                !IsWithin(s.EnemyRotation.x, -1f, 1f) || !IsWithin(s.EnemyRotation.y, -1f, 1f) ||
                !IsWithin(s.EnemyRotation.z, -1f, 1f) || !IsWithin(s.EnemyRotation.w, -1f, 1f) ||
                !IsWithin(s.Player.rotation.x, -1f, 1f) || !IsWithin(s.Player.rotation.y, -1f, 1f) ||
                !IsWithin(s.Player.rotation.z, -1f, 1f) || !IsWithin(s.Player.rotation.w, -1f, 1f) ||
                !IsUnitQuaternion(s.Player.rotation) || !IsUnitQuaternion(s.EnemyRotation))
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
            // The host must reject nested ability errors before it mutates
            // player transforms, inventory, weapon or enemy state.
            if (!abilities.TryValidateSnapshot(s.Abilities, out _)) return false;
            return true;
        }

        private static bool IsWithin(float value, float lower, float upper)
        {
            return !float.IsNaN(value) && !float.IsInfinity(value) && value >= lower && value <= upper;
        }

        private static bool IsWithinArena(SerializableVector3 position)
        {
            // Both characters share the same actual collision-bounded arena:
            // side walls centered at x +/-8.5 and end walls at z +/-6.0.
            // The previous player-only [-7,7] bound rejected legitimate
            // positions alongside the walls after collision-aware movement.
            return IsWithin(position.x, -8f, 8f) &&
                   IsWithin(position.z, -6f, 6f) &&
                   IsWithin(position.y, 0f, 2.5f);
        }

        private static bool IsUnitQuaternion(SerializableQuaternion value)
        {
            // Unity transform rotations are unit quaternions. Four values
            // independently within [-1, 1] can nevertheless encode an
            // invalid zero-length or nonunit orientation. Validate before
            // making any changes to a loaded encounter.
            double normSquared = (double)value.x * value.x +
                                 (double)value.y * value.y +
                                 (double)value.z * value.z +
                                 (double)value.w * value.w;
            return normSquared >= 0.99 && normSquared <= 1.01;
        }

        public void ResetEncounter()
        {
            if (playerStats == null) return;
            if (playerMotor != null) playerMotor.Warp(initialPlayerPosition, initialPlayerRotation);
            else playerRoot.transform.SetPositionAndRotation(initialPlayerPosition, initialPlayerRotation);
            if (enemyMotor != null) enemyMotor.Warp(initialEnemyPosition, initialEnemyRotation);
            else enemyVisual.transform.SetPositionAndRotation(initialEnemyPosition, initialEnemyRotation);
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
            float panelWidth = Mathf.Max(140f, Mathf.Min(550f, Screen.width - 24f));
            float panelHeight = Mathf.Max(120f, Mathf.Min(485f, Screen.height - 24f));
            GUILayout.BeginArea(new Rect(12f, 12f, panelWidth, panelHeight), GUI.skin.box);
            hudScrollPosition = GUILayout.BeginScrollView(hudScrollPosition);
            GUILayout.Label("HPR GAMEPLAY SYSTEMS SUITE   |   INTEGRATED TRAINING ARENA");
            GUILayout.Label("OBJECTIVE  " + Objective);
            GUILayout.Label("PLAYER " + PlayerHealth.ToString("0") + "/" + playerStats.MaxHealth.ToString("0") +
                " HP    STAMINA " + PlayerStamina.ToString("0") +
                "    ENEMY " + EnemyHealth.ToString("0") + "/" + enemyData.MaxHealth.ToString("0") + " HP");
            GUILayout.Label("RIFLE " + MagazineAmmo + "/" + weapon.MagazineSize +
                "    RESERVE " + ReserveAmmo + "    MEDKITS " + LootCount + "    KEYS " + KeyCount +
                "    DOOR " + (DoorIsOpen ? "OPEN" : "LOCKED"));
            GUILayout.Label("Movement " + moveForwardKey + "/" + moveLeftKey + "/" +
                moveBackwardKey + "/" + moveRightKey + " or arrows | Aim with mouse, fire " + fireKey);
            GUILayout.Label("Reload " + reloadKey + " | Interact " + interactKey +
                " | Heal " + healAbilityKey + " | Pulse " + pulseAbilityKey +
                " | Save " + memorySaveKey + " | Restore " + memoryLoadKey);
            GUILayout.BeginHorizontal();
            if (GUILayout.Button("Training target [button]")) Fire();
            if (GUILayout.Button("Reload [" + reloadKey + "]")) Reload();
            if (GUILayout.Button("Enemy attacks")) EnemyAttack();
            if (GUILayout.Button("Use medkit [" + useMedkitKey + "]")) Heal();
            GUILayout.EndHorizontal();
            GUILayout.BeginHorizontal();
            if (GUILayout.Button("Interact [" + interactKey + "]")) Interact();
            if (GUILayout.Button("Heal ability [" + healAbilityKey + "]")) UseHealAbility();
            if (GUILayout.Button("Damage pulse [" + pulseAbilityKey + "]")) UsePulseAbility();
            GUILayout.EndHorizontal();
            GUILayout.BeginHorizontal();
            GUILayout.Label("ENEMY CHASE/ATTACK: " + (AutomaticEnemy ? "LIVE" : "PAUSED"));
            if (GUILayout.Button(AutomaticEnemy ? "Pause" : "Resume")) SetAutomaticEnemy(!AutomaticEnemy);
            GUILayout.EndHorizontal();
            GUILayout.Label("ABILITIES: " + abilities.BuildHudSummary(healAbilityKey.ToString(), pulseAbilityKey.ToString()));
            IInteractable target = FindNearbyInteractable();
            GUILayout.Label("NEARBY: " + (target != null ? target.GetPrompt(actor) : "move to the cyan or yellow pickups / door"));
            GUILayout.BeginHorizontal();
            if (GUILayout.Button("Memory checkpoint [" + memorySaveKey + "]")) SaveCheckpoint();
            if (GUILayout.Button("Restore memory [" + memoryLoadKey + "]")) RestoreCheckpoint();
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
            GUILayout.EndScrollView();
            GUILayout.EndArea();
        }

        private sealed class SuiteEvent { public string Text; }
    }
}
