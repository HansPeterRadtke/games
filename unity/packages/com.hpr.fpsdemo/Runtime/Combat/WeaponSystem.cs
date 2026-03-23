using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

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

    private readonly List<WeaponRuntimeState> runtimeSlots = new List<WeaponRuntimeState>();

    private Camera playerCamera;
    private IInventoryService inventory;
    private IPlayerStats ownerStats;
    private float aimBlend;
    private float bobTimer;
    private Vector3 recoilPosition;
    private Vector3 recoilRotation;

    public IReadOnlyList<WeaponRuntimeState> RuntimeSlots => runtimeSlots;
    public int SlotCount => runtimeSlots.Count;
    public int CurrentIndex => currentIndex;
    public WeaponRuntimeState CurrentState => runtimeSlots.Count == 0 ? null : runtimeSlots[Mathf.Clamp(currentIndex, 0, runtimeSlots.Count - 1)];

    public void ConfigureLoadout(IEnumerable<WeaponData> weaponData)
    {
        loadout = weaponData?.Where(data => data != null).Distinct().ToList() ?? new List<WeaponData>();
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
        BuildRuntimeSlots();
        BuildViewModels();
        SelectSlot(currentIndex);
    }

    public void BindDependencies(IInventoryService inventoryService, IPlayerStats stats)
    {
        if (inventory != null)
        {
            inventory.ItemAdded -= HandleInventoryItemAdded;
            inventory.ItemRemoved -= HandleInventoryItemRemoved;
        }

        inventory = inventoryService;
        ownerStats = stats;

        if (inventory != null)
        {
            inventory.ItemAdded += HandleInventoryItemAdded;
            inventory.ItemRemoved += HandleInventoryItemRemoved;
        }
    }

    public void ResetToLoadoutDefaults()
    {
        foreach (var runtimeState in runtimeSlots)
        {
            runtimeState.ResetToDefaults();
        }

        SelectSlot(currentIndex);
        GameManager.Instance?.RefreshHud();
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

        GameManager.Instance?.RefreshHud();
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
        GameManager.Instance?.RefreshHud();
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
            GameManager.Instance?.NotifyStatus("No reload needed");
            return;
        }

        int missing = data.MagazineSize - runtimeState.MagazineAmmo;
        if (missing <= 0 || runtimeState.ReserveAmmo <= 0)
        {
            GameManager.Instance?.NotifyStatus("Magazine full or reserve empty");
            return;
        }

        int moved = Mathf.Min(missing, runtimeState.ReserveAmmo);
        runtimeState.MagazineAmmo += moved;
        runtimeState.ReserveAmmo -= moved;
        GameManager.Instance?.NotifyStatus($"Reloaded {data.DisplayName}");
        GameManager.Instance?.RefreshHud();
    }

    public void TriggerCurrent(IPlayerActor owner)
    {
        var runtimeState = CurrentState;
        if (runtimeState == null || runtimeState.Data == null || Time.time < runtimeState.CooldownUntil)
        {
            return;
        }

        runtimeState.CooldownUntil = Time.time + Mathf.Max(0.05f, runtimeState.Data.FireDelay);

        switch (runtimeState.Data.Kind)
        {
            case EquipmentKind.Hitscan:
                FireProjectilePattern(owner, runtimeState, 1, runtimeState.Data.Spread, false);
                break;
            case EquipmentKind.Scatter:
                FireProjectilePattern(owner, runtimeState, Mathf.Max(1, runtimeState.Data.Pellets), runtimeState.Data.Spread, false);
                break;
            case EquipmentKind.Melee:
                FireMelee(owner, runtimeState);
                break;
            case EquipmentKind.Explosive:
                FireProjectilePattern(owner, runtimeState, 1, runtimeState.Data.Spread, true);
                break;
            case EquipmentKind.Utility:
                UseUtility(owner, runtimeState);
                break;
        }

        GameManager.Instance?.RefreshHud();
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

    private void FireProjectilePattern(IPlayerActor owner, WeaponRuntimeState runtimeState, int projectiles, float spread, bool explosive)
    {
        if (!ConsumeAmmoIfNeeded(runtimeState))
        {
            return;
        }

        ApplyFireAnimation(runtimeState, explosive ? 1.3f : 1f);
        GameManager.Instance?.NotifyStatus($"{runtimeState.Data.DisplayName} fired");

        for (int i = 0; i < projectiles; i++)
        {
            Vector3 direction = playerCamera.transform.forward;
            if (spread > 0f)
            {
                direction = Quaternion.Euler(UnityEngine.Random.Range(-spread, spread), UnityEngine.Random.Range(-spread, spread), 0f) * direction;
            }

            CreateProjectile(
                owner.ActorTransform,
                GetMuzzleTransform().position,
                direction,
                runtimeState.Data,
                explosive ? Mathf.Max(3.2f, runtimeState.Data.ExplosiveRadius) : 0f,
                runtimeState.Data.ProjectileScale,
                Mathf.Clamp(runtimeState.Data.Range / Mathf.Max(8f, runtimeState.Data.ProjectileSpeed), 1.2f, 4f));
        }
    }

    private void FireMelee(IPlayerActor owner, WeaponRuntimeState runtimeState)
    {
        ApplyFireAnimation(runtimeState, 1.5f);

        Vector3 center = playerCamera.transform.position + playerCamera.transform.forward * Mathf.Clamp(runtimeState.Data.Range * 0.65f, 1f, 1.8f);
        Collider[] hits = Physics.OverlapSphere(center, 1.15f, ~0, QueryTriggerInteraction.Ignore);
        IDamageable bestTarget = null;
        IImpactReceiver bestImpact = null;
        Vector3 bestPoint = center;
        float bestDistance = float.MaxValue;

        foreach (var collider in hits)
        {
            if (collider.transform.root == owner.ActorTransform)
            {
                continue;
            }

            var damageable = collider.GetComponentInParent<IDamageable>();
            if (damageable == null || !damageable.IsAlive)
            {
                continue;
            }

            Vector3 point = collider.ClosestPoint(center);
            float distance = (point - center).sqrMagnitude;
            if (distance < bestDistance)
            {
                bestDistance = distance;
                bestTarget = damageable;
                bestImpact = collider.GetComponentInParent<IImpactReceiver>();
                bestPoint = point;
            }
        }

        if (bestTarget != null)
        {
            Vector3 hitDirection = (bestPoint - playerCamera.transform.position).normalized;
            bestTarget.ApplyDamage(runtimeState.Data.Damage, bestPoint, hitDirection);
            bestImpact?.ApplyImpact(hitDirection * runtimeState.Data.ImpactForce, bestPoint);
            GameManager.Instance?.NotifyStatus($"{runtimeState.Data.DisplayName} connected");
            return;
        }

        GameManager.Instance?.NotifyStatus($"{runtimeState.Data.DisplayName} missed");
    }

    private void UseUtility(IPlayerActor owner, WeaponRuntimeState runtimeState)
    {
        var data = runtimeState.Data;
        switch (data.UtilityAction)
        {
            case WeaponUtilityAction.ConsumeItem:
                UseLinkedConsumable(data);
                break;
            case WeaponUtilityAction.ThreatScan:
                GameManager.Instance?.NotifyStatus(GameManager.Instance?.DescribeNearbyThreats(owner.ActorTransform.position) ?? data.UtilityMessage);
                break;
            case WeaponUtilityAction.KeyringStatus:
                GameManager.Instance?.NotifyStatus(inventory != null && inventory.HasAnyItemOfType(ItemType.Key) ? data.UtilityMessage : "Keyring is empty");
                break;
            case WeaponUtilityAction.RepairTool:
                GameManager.Instance?.NotifyStatus(data.UtilityMessage);
                break;
            default:
                GameManager.Instance?.NotifyStatus(data.UtilityMessage);
                break;
        }
    }

    private void UseLinkedConsumable(WeaponData data)
    {
        if (inventory == null || ownerStats == null)
        {
            return;
        }

        var item = inventory.GetItemData(data.LinkedItemId);
        if (item == null)
        {
            GameManager.Instance?.NotifyStatus(data.UtilityMessage);
            return;
        }

        if (!inventory.HasItem(item.Id))
        {
            GameManager.Instance?.NotifyStatus($"No {item.DisplayName} available");
            return;
        }

        if (item.Value > 0 && ownerStats.Health >= ownerStats.MaxHealth - 1f)
        {
            GameManager.Instance?.NotifyStatus("Health already full");
            return;
        }

        if (!inventory.RemoveItem(item.Id, 1))
        {
            GameManager.Instance?.NotifyStatus($"No {item.DisplayName} available");
            return;
        }

        if (item.Value > 0)
        {
            ownerStats.Heal(item.Value);
        }

        GameManager.Instance?.NotifyStatus(string.IsNullOrWhiteSpace(data.UtilityMessage) ? $"Used {item.DisplayName}" : data.UtilityMessage);
    }

    private bool ConsumeAmmoIfNeeded(WeaponRuntimeState runtimeState)
    {
        if (!runtimeState.Data.UsesAmmo)
        {
            return true;
        }

        if (runtimeState.MagazineAmmo <= 0)
        {
            GameManager.Instance?.NotifyStatus("Magazine empty - press reload");
            return false;
        }

        runtimeState.MagazineAmmo--;
        return true;
    }

    private void CreateProjectile(
        Transform ownerRoot,
        Vector3 origin,
        Vector3 direction,
        WeaponData weaponData,
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
        projectileBehaviour.Configure(ownerRoot, direction, weaponData.Damage, weaponData.ProjectileSpeed, weaponData.ImpactForce, lifetime, explosiveRadius, weaponData.ViewColor);
    }

    private Transform GetMuzzleTransform()
    {
        return CurrentState?.Muzzle != null ? CurrentState.Muzzle : playerCamera.transform;
    }

    private void ApplyFireAnimation(WeaponRuntimeState runtimeState, float multiplier)
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
        foreach (var runtimeState in runtimeSlots)
        {
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

            var body = GameObject.CreatePrimitive(runtimeState.Data.ViewShape);
            body.name = "Body";
            body.layer = 2;
            body.transform.SetParent(root.transform, false);
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
            barrel.transform.SetParent(root.transform, false);
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

            var muzzle = new GameObject("Muzzle").transform;
            muzzle.SetParent(root.transform, false);
            muzzle.localPosition = new Vector3(0f, 0f, runtimeState.Data.ViewLocalScale.z * 0.78f);

            runtimeState.ViewModel = root;
            runtimeState.Muzzle = muzzle;
            runtimeState.SlotLabel = $"{runtimeSlots.IndexOf(runtimeState) + 1}. {runtimeState.Data.DisplayName}";
            root.SetActive(false);
        }
    }

    private void HandleInventoryItemAdded(ItemData itemData, int amount)
    {
        if (itemData == null || itemData.ItemType != ItemType.Ammo || string.IsNullOrWhiteSpace(itemData.LinkedWeaponId))
        {
            return;
        }

        AddAmmo(itemData.LinkedWeaponId, amount);
    }

    private void HandleInventoryItemRemoved(ItemData itemData, int amount)
    {
        if (itemData == null || itemData.ItemType != ItemType.Ammo || string.IsNullOrWhiteSpace(itemData.LinkedWeaponId))
        {
            return;
        }

        var runtimeState = runtimeSlots.FirstOrDefault(slot => slot.Data != null && slot.Data.Id == itemData.LinkedWeaponId);
        if (runtimeState == null || !runtimeState.Data.UsesAmmo)
        {
            return;
        }

        runtimeState.ReserveAmmo = Mathf.Clamp(runtimeState.ReserveAmmo - amount, 0, Mathf.Max(0, runtimeState.Data.MaxAmmo));
        GameManager.Instance?.RefreshHud();
    }
}
