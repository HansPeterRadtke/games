using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace HPR
{
    [Serializable]
    public class WeaponRuntimeState
    {
        [field: SerializeField] public WeaponData Data { get; private set; }
        [field: SerializeField] public int MagazineAmmo { get; set; }
        [field: SerializeField] public int ReserveAmmo { get; set; }
        [field: SerializeField] public float CooldownUntil { get; set; }

        public GameObject ViewModel { get; set; }
        public Transform Muzzle { get; set; }

        public string SlotLabel { get; set; }
        public int TotalAmmoCount => Data != null && Data.UsesAmmo ? MagazineAmmo + ReserveAmmo : 1;

        public WeaponRuntimeState(WeaponData data)
        {
            Data = data;
            SlotLabel = data != null ? data.DisplayName : string.Empty;
            ResetToDefaults();
        }

        public void ResetToDefaults()
        {
            if (Data == null)
            {
                MagazineAmmo = 0;
                ReserveAmmo = 0;
                CooldownUntil = 0f;
                return;
            }

            MagazineAmmo = Mathf.Clamp(Data.StartingMagazineAmmo, 0, Mathf.Max(0, Data.MagazineSize));
            ReserveAmmo = Mathf.Clamp(Data.StartingReserveAmmo, 0, Mathf.Max(0, Data.MaxAmmo));
            CooldownUntil = 0f;
        }

        public string GetAmmoLabel()
        {
            if (Data == null || !Data.UsesAmmo)
            {
                return Data != null && Data.Kind == EquipmentKind.Utility ? "utility" : "melee";
            }

            return $"{MagazineAmmo}/{ReserveAmmo}";
        }
    }

    public class WeaponSystem : MonoBehaviour, IWeaponLoadout
    {
        [SerializeField] private List<WeaponData> loadout = new List<WeaponData>();
        [SerializeField] private int currentIndex;
        [SerializeField] private MonoBehaviour servicesBehaviour;

        private readonly List<WeaponRuntimeState> runtimeSlots = new List<WeaponRuntimeState>();
        private readonly Dictionary<FireModeType, IFireMode> fireModes = new Dictionary<FireModeType, IFireMode>();

        private Camera playerCamera;
        private IInventoryService inventory;
        private IPlayerStats ownerStats;
        private IEventBus eventBus;
        private IEventBusSource eventBusSource;
        private IStatusMessageSink statusSink;
        private IHudRefreshSink hudRefreshSink;
        private float aimBlend;
        private float bobTimer;
        private Vector3 recoilPosition;
        private Vector3 recoilRotation;

        internal Camera PlayerCamera => playerCamera;
        internal IInventoryService InventoryService => inventory;
        internal IPlayerStats OwnerStats => ownerStats;
        internal IEventBus EventBus => eventBus;
        internal IStatusMessageSink StatusSink => statusSink;
        internal IThreatScanner ThreatScanner => servicesBehaviour as IThreatScanner;
        public IReadOnlyList<WeaponRuntimeState> RuntimeSlots => runtimeSlots;
        public int SlotCount => runtimeSlots.Count;
        public int CurrentIndex => currentIndex;
        public WeaponRuntimeState CurrentState => runtimeSlots.Count == 0 ? null : runtimeSlots[Mathf.Clamp(currentIndex, 0, runtimeSlots.Count - 1)];

        private void Awake()
        {
            servicesBehaviour = servicesBehaviour != null ? servicesBehaviour : GetComponentsInParent<MonoBehaviour>(true).FirstOrDefault(component => component is IEventBusSource || component is IStatusMessageSink || component is IHudRefreshSink);
            eventBusSource = servicesBehaviour as IEventBusSource;
            statusSink = servicesBehaviour as IStatusMessageSink;
            hudRefreshSink = servicesBehaviour as IHudRefreshSink;
        }

        public void ConfigureLoadout(IEnumerable<WeaponData> weaponData)
        {
            loadout = weaponData?.Where(data => data != null).Distinct().ToList() ?? new List<WeaponData>();
            EnsureFireModes();
            BuildRuntimeSlots();
            if (playerCamera != null)
            {
                BuildViewModels();
                SelectSlot(currentIndex);
            }
        }

        public void Initialize(Camera camera)
        {
            playerCamera = camera;
            EnsureFireModes();
            BuildRuntimeSlots();
            BuildViewModels();
            SelectSlot(currentIndex);
        }

        public void BindRuntimeServices(MonoBehaviour services)
        {
            servicesBehaviour = services;
            eventBusSource = servicesBehaviour as IEventBusSource;
            statusSink = servicesBehaviour as IStatusMessageSink;
            hudRefreshSink = servicesBehaviour as IHudRefreshSink;
            BindEventBus(eventBusSource != null ? eventBusSource.EventBus : null);
        }

        private void Start()
        {
            EnsureEventBusBinding();
        }

        private void OnDisable()
        {
            BindEventBus(null);
        }

        public void BindDependencies(IInventoryService inventoryService, IPlayerStats stats)
        {
            inventory = inventoryService;
            ownerStats = stats;
        }

        public void ResetToLoadoutDefaults()
        {
            foreach (var runtimeState in runtimeSlots)
            {
                runtimeState.ResetToDefaults();
            }

            SelectSlot(currentIndex);
            hudRefreshSink?.RefreshHud();
        }

        public WeaponRuntimeState GetSlot(int index)
        {
            return runtimeSlots.Count == 0 ? null : runtimeSlots[Mathf.Clamp(index, 0, runtimeSlots.Count - 1)];
        }

        public void SelectSlot(int index)
        {
            if (runtimeSlots.Count == 0)
            {
                return;
            }

            currentIndex = Mathf.Clamp(index, 0, runtimeSlots.Count - 1);
            recoilPosition = Vector3.zero;
            recoilRotation = Vector3.zero;
            aimBlend = 0f;
            bobTimer = 0f;

            for (int i = 0; i < runtimeSlots.Count; i++)
            {
                runtimeSlots[i].SlotLabel = $"{i + 1}. {runtimeSlots[i].Data.DisplayName}";
                if (runtimeSlots[i].ViewModel != null)
                {
                    runtimeSlots[i].ViewModel.SetActive(i == currentIndex);
                }
            }

            hudRefreshSink?.RefreshHud();
        }

        public bool TrySelectWeapon(string weaponId)
        {
            if (string.IsNullOrWhiteSpace(weaponId))
            {
                return false;
            }

            int index = runtimeSlots.FindIndex(slot => slot.Data != null && slot.Data.Id == weaponId);
            if (index < 0)
            {
                return false;
            }

            SelectSlot(index);
            return true;
        }

        public void AddAmmo(string weaponId, int amount)
        {
            if (string.IsNullOrWhiteSpace(weaponId) || amount <= 0)
            {
                return;
            }

            var runtimeState = runtimeSlots.FirstOrDefault(slot => slot.Data != null && slot.Data.Id == weaponId);
            if (runtimeState == null || !runtimeState.Data.UsesAmmo)
            {
                return;
            }

            runtimeState.ReserveAmmo = Mathf.Clamp(runtimeState.ReserveAmmo + amount, 0, Mathf.Max(0, runtimeState.Data.MaxAmmo));
            hudRefreshSink?.RefreshHud();
        }

        public List<WeaponRuntimeSaveData> CaptureRuntimeState()
        {
            return runtimeSlots.Select(slot => new WeaponRuntimeSaveData
            {
                weaponId = slot.Data.Id,
                magazineAmmo = slot.MagazineAmmo,
                reserveAmmo = slot.ReserveAmmo
            }).ToList();
        }

        public void RestoreRuntimeState(IEnumerable<WeaponRuntimeSaveData> savedState, string selectedWeaponId)
        {
            ResetToLoadoutDefaults();
            if (savedState != null)
            {
                foreach (var state in savedState)
                {
                    if (state == null || string.IsNullOrWhiteSpace(state.weaponId))
                    {
                        continue;
                    }

                    var runtimeState = runtimeSlots.FirstOrDefault(slot => slot.Data != null && slot.Data.Id == state.weaponId);
                    if (runtimeState == null)
                    {
                        continue;
                    }

                    runtimeState.MagazineAmmo = Mathf.Clamp(state.magazineAmmo, 0, Mathf.Max(0, runtimeState.Data.MagazineSize));
                    runtimeState.ReserveAmmo = Mathf.Clamp(state.reserveAmmo, 0, Mathf.Max(0, runtimeState.Data.MaxAmmo));
                }
            }

            if (!TrySelectWeapon(selectedWeaponId))
            {
                SelectSlot(currentIndex);
            }
        }

        public void Reload()
        {
            var runtimeState = CurrentState;
            if (runtimeState == null)
            {
                return;
            }

            var data = runtimeState.Data;
            if (!data.UsesAmmo || data.MagazineSize <= 0)
            {
                statusSink?.NotifyStatus("No reload needed");
                return;
            }

            int missing = data.MagazineSize - runtimeState.MagazineAmmo;
            if (missing <= 0 || runtimeState.ReserveAmmo <= 0)
            {
                statusSink?.NotifyStatus("Magazine full or reserve empty");
                return;
            }

            int moved = Mathf.Min(missing, runtimeState.ReserveAmmo);
            runtimeState.MagazineAmmo += moved;
            runtimeState.ReserveAmmo -= moved;
            statusSink?.NotifyStatus($"Reloaded {data.DisplayName}");
            hudRefreshSink?.RefreshHud();
        }

        public void TriggerCurrent(IPlayerActor owner)
        {
            EnsureEventBusBinding();
            var runtimeState = CurrentState;
            if (runtimeState == null || runtimeState.Data == null || Time.time < runtimeState.CooldownUntil)
            {
                return;
            }

            runtimeState.CooldownUntil = Time.time + Mathf.Max(0.05f, runtimeState.Data.FireDelay);
            IFireMode fireMode = ResolveFireMode(runtimeState.Data);
            if (fireMode != null && fireMode.Execute(new WeaponFireContext(this, owner, runtimeState)))
            {
                hudRefreshSink?.RefreshHud();
            }
        }

        public void TickPresentation(float movementAmount, bool isAiming, bool isRunning)
        {
            var runtimeState = CurrentState;
            if (runtimeState == null || runtimeState.ViewModel == null)
            {
                return;
            }

            var data = runtimeState.Data;
            aimBlend = Mathf.MoveTowards(aimBlend, isAiming ? 1f : 0f, Time.deltaTime * 6f);
            recoilPosition = Vector3.Lerp(recoilPosition, Vector3.zero, Time.deltaTime * 10f);
            recoilRotation = Vector3.Lerp(recoilRotation, Vector3.zero, Time.deltaTime * 10f);

            if (movementAmount > 0.05f)
            {
                bobTimer += Time.deltaTime * (isRunning ? 11f : 7f) * Mathf.Clamp(movementAmount, 0f, 1.6f);
            }
            else
            {
                bobTimer = Mathf.Lerp(bobTimer, 0f, Time.deltaTime * 5f);
            }

            Vector3 bobOffset = new Vector3(
                Mathf.Sin(bobTimer) * 0.012f,
                Mathf.Cos(bobTimer * 2f) * 0.008f,
                0f);
            Vector3 targetPosition = Vector3.Lerp(data.ViewLocalPosition, data.AimLocalPosition, aimBlend) + bobOffset + recoilPosition;
            Vector3 targetEuler = data.ViewLocalEuler + recoilRotation;

            var currentView = runtimeState.ViewModel.transform;
            currentView.localPosition = Vector3.Lerp(currentView.localPosition, targetPosition, Time.deltaTime * 18f);
            currentView.localRotation = Quaternion.Slerp(currentView.localRotation, Quaternion.Euler(targetEuler), Time.deltaTime * 18f);
        }

        internal bool TryConsumeAmmo(WeaponRuntimeState runtimeState)
        {
            if (!runtimeState.Data.UsesAmmo)
            {
                return true;
            }

            if (runtimeState.MagazineAmmo <= 0)
            {
                statusSink?.NotifyStatus("Magazine empty - press reload");
                return false;
            }

            runtimeState.MagazineAmmo--;
            return true;
        }

        internal void CreateProjectile(
            Transform ownerRoot,
            Vector3 origin,
            Vector3 direction,
            WeaponData weaponData,
            float damageAmount,
            float explosiveRadius,
            float projectileScale,
            float lifetime)
        {
            GameObject projectile = weaponData.ProjectilePrefab != null
                ? Instantiate(weaponData.ProjectilePrefab, origin, Quaternion.identity)
                : GameObject.CreatePrimitive(PrimitiveType.Sphere);

            projectile.name = $"{weaponData.Id}_Projectile";
            projectile.transform.position = origin;
            projectile.transform.localScale = Vector3.one * Mathf.Max(0.04f, projectileScale);

            var rigidbody = projectile.GetComponent<Rigidbody>();
            if (rigidbody == null)
            {
                rigidbody = projectile.AddComponent<Rigidbody>();
            }
            rigidbody.useGravity = false;
            rigidbody.collisionDetectionMode = CollisionDetectionMode.ContinuousDynamic;
            rigidbody.mass = 0.08f;

            var projectileBehaviour = projectile.GetComponent<PhysicsProjectile>();
            if (projectileBehaviour == null)
            {
                projectileBehaviour = projectile.AddComponent<PhysicsProjectile>();
            }
            projectileBehaviour.Configure(ownerRoot, direction, damageAmount, weaponData.ProjectileSpeed, weaponData.ImpactForce, lifetime, explosiveRadius, weaponData.ViewColor, eventBus);
        }

        internal Transform ResolveCurrentMuzzle()
        {
            return CurrentState?.Muzzle != null ? CurrentState.Muzzle : playerCamera.transform;
        }

        internal void ApplyFireAnimation(WeaponRuntimeState runtimeState, float multiplier)
        {
            recoilPosition += new Vector3(-0.02f, 0.015f, -0.12f * multiplier);
            recoilRotation += new Vector3(-8f * multiplier, 1.5f * multiplier, UnityEngine.Random.Range(-2f, 2f) * multiplier);
            if (runtimeState.Data.Kind == EquipmentKind.Melee)
            {
                recoilPosition += new Vector3(0.05f, -0.04f, -0.08f);
                recoilRotation += new Vector3(0f, 0f, 16f);
            }
        }

        private void BuildRuntimeSlots()
        {
            string currentWeaponId = CurrentState?.Data?.Id;
            runtimeSlots.Clear();
            foreach (var weaponData in loadout.Where(data => data != null))
            {
                runtimeSlots.Add(new WeaponRuntimeState(weaponData));
            }

            if (!string.IsNullOrWhiteSpace(currentWeaponId))
            {
                int restoredIndex = runtimeSlots.FindIndex(slot => slot.Data.Id == currentWeaponId);
                currentIndex = restoredIndex >= 0 ? restoredIndex : Mathf.Clamp(currentIndex, 0, Mathf.Max(0, runtimeSlots.Count - 1));
            }
            else
            {
                currentIndex = Mathf.Clamp(currentIndex, 0, Mathf.Max(0, runtimeSlots.Count - 1));
            }
        }

        private void BuildViewModels()
        {
            for (int index = 0; index < runtimeSlots.Count; index++)
            {
                var runtimeState = runtimeSlots[index];
                if (runtimeState.ViewModel != null)
                {
                    Destroy(runtimeState.ViewModel);
                }

                var root = new GameObject($"WeaponView_{runtimeState.Data.DisplayName}");
                root.layer = 2;
                root.transform.SetParent(playerCamera.transform, false);
                root.transform.localPosition = runtimeState.Data.ViewLocalPosition;
                root.transform.localEulerAngles = runtimeState.Data.ViewLocalEuler;
                root.transform.localScale = Vector3.one;

                CreateViewVisual(root.transform, runtimeState);

                var muzzle = new GameObject("Muzzle").transform;
                muzzle.SetParent(root.transform, false);
                muzzle.localPosition = ResolveMuzzleOffset(runtimeState.Data);

                runtimeState.ViewModel = root;
                runtimeState.Muzzle = muzzle;
                runtimeState.SlotLabel = $"{index + 1}. {runtimeState.Data.DisplayName}";
                root.SetActive(false);
            }
        }

        private void CreateViewVisual(Transform root, WeaponRuntimeState runtimeState)
        {
            if (runtimeState.Data.ViewPrefab != null)
            {
                var visual = Instantiate(runtimeState.Data.ViewPrefab, root);
                visual.name = "Body";
                visual.transform.localPosition = Vector3.zero;
                visual.transform.localRotation = Quaternion.identity;
                visual.transform.localScale = runtimeState.Data.ViewLocalScale;
                AssignLayerRecursively(visual.transform, 2);
                StripPresentationPhysics(visual);
                return;
            }

            var body = GameObject.CreatePrimitive(runtimeState.Data.ViewShape);
            body.name = "Body";
            body.layer = 2;
            body.transform.SetParent(root, false);
            body.transform.localPosition = Vector3.zero;
            body.transform.localRotation = Quaternion.identity;
            body.transform.localScale = runtimeState.Data.ViewLocalScale;
            var bodyRenderer = body.GetComponent<Renderer>();
            if (bodyRenderer != null)
            {
                bodyRenderer.sharedMaterial = new Material(Shader.Find("Standard")) { color = runtimeState.Data.ViewColor };
            }

            foreach (var collider in body.GetComponentsInChildren<Collider>())
            {
                Destroy(collider);
            }

            var barrel = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            barrel.name = "Barrel";
            barrel.layer = 2;
            barrel.transform.SetParent(root, false);
            barrel.transform.localPosition = new Vector3(0f, 0.01f, runtimeState.Data.ViewLocalScale.z * 0.55f);
            barrel.transform.localEulerAngles = new Vector3(90f, 0f, 0f);
            barrel.transform.localScale = new Vector3(runtimeState.Data.ViewLocalScale.x * 0.25f, runtimeState.Data.ViewLocalScale.z * 0.22f, runtimeState.Data.ViewLocalScale.x * 0.25f);
            var barrelRenderer = barrel.GetComponent<Renderer>();
            if (barrelRenderer != null)
            {
                barrelRenderer.sharedMaterial = new Material(Shader.Find("Standard"))
                {
                    color = Color.Lerp(runtimeState.Data.ViewColor, Color.white, 0.18f)
                };
            }

            foreach (var collider in barrel.GetComponentsInChildren<Collider>())
            {
                Destroy(collider);
            }
        }

        private static Vector3 ResolveMuzzleOffset(WeaponData data)
        {
            if (data.ViewMuzzleLocalPosition != Vector3.zero)
            {
                return data.ViewMuzzleLocalPosition;
            }

            return new Vector3(0f, 0f, data.ViewLocalScale.z * 0.78f);
        }

        private static void StripPresentationPhysics(GameObject root)
        {
            foreach (var collider in root.GetComponentsInChildren<Collider>(true))
            {
                Destroy(collider);
            }

            foreach (var rigidbody in root.GetComponentsInChildren<Rigidbody>(true))
            {
                Destroy(rigidbody);
            }

            foreach (var behaviour in root.GetComponentsInChildren<MonoBehaviour>(true))
            {
                Destroy(behaviour);
            }
        }

        private static void AssignLayerRecursively(Transform root, int layer)
        {
            root.gameObject.layer = layer;
            foreach (Transform child in root)
            {
                AssignLayerRecursively(child, layer);
            }
        }

        private void EnsureFireModes()
        {
            foreach (WeaponData weaponData in loadout)
            {
                if (weaponData == null || fireModes.ContainsKey(weaponData.FireModeType))
                {
                    continue;
                }

                fireModes[weaponData.FireModeType] = FireModeFactory.Create(weaponData.FireModeType);
            }
        }

        private IFireMode ResolveFireMode(WeaponData weaponData)
        {
            EnsureFireModes();
            if (weaponData == null)
            {
                return null;
            }

            if (!fireModes.TryGetValue(weaponData.FireModeType, out IFireMode fireMode))
            {
                fireMode = FireModeFactory.Create(weaponData.FireModeType);
                fireModes[weaponData.FireModeType] = fireMode;
            }

            return fireMode;
        }

        private void EnsureEventBusBinding()
        {
            BindEventBus(eventBusSource != null ? eventBusSource.EventBus : null);
        }

        private void BindEventBus(IEventBus bus)
        {
            if (eventBus == bus)
            {
                return;
            }

            if (eventBus != null)
            {
                eventBus.Unsubscribe<ItemPickedEvent>(HandleItemPickedEvent);
            }

            eventBus = bus;
            if (eventBus != null)
            {
                eventBus.Subscribe<ItemPickedEvent>(HandleItemPickedEvent);
            }
        }

        private void HandleItemPickedEvent(ItemPickedEvent gameEvent)
        {
            int amount = gameEvent != null ? gameEvent.Amount : 0;
            if (gameEvent == null || gameEvent.ItemType != (int)ItemType.Ammo || string.IsNullOrWhiteSpace(gameEvent.LinkedWeaponId))
            {
                return;
            }

            AddAmmo(gameEvent.LinkedWeaponId, amount);
        }
    }
}
