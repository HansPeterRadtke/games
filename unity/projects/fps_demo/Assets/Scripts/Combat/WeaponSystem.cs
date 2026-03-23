using System;
using System.Collections.Generic;
using UnityEngine;

public enum EquipmentKind
{
    Hitscan,
    Scatter,
    Melee,
    Explosive,
    Utility
}

[Serializable]
public class WeaponSlot
{
    public string displayName;
    public EquipmentKind kind;
    public PrimitiveType shape;
    public Color color;
    public Vector3 localPosition;
    public Vector3 localEuler;
    public Vector3 localScale;
    public Vector3 aimLocalPosition;
    public float damage;
    public float range;
    public float fireDelay;
    public float spread;
    public int pellets;
    public int magazineSize;
    public int ammoInMagazine;
    public int reserveAmmo;
    public bool usesAmmo;
    public string utilityMessage;
    public float projectileSpeed = 48f;
    public float impactForce = 12f;
    public float projectileScale = 0.08f;
    public float explosiveRadius;

    public string DisplayName => displayName;

    public string GetAmmoLabel()
    {
        if (!usesAmmo)
        {
            return kind == EquipmentKind.Utility ? "utility" : "melee";
        }

        return $"{ammoInMagazine}/{reserveAmmo}";
    }
}

public class WeaponSystem : MonoBehaviour
{
    [SerializeField] private List<WeaponSlot> slots = new List<WeaponSlot>();
    [SerializeField] private int currentIndex;

    private readonly List<GameObject> viewModels = new List<GameObject>();
    private readonly List<Transform> muzzles = new List<Transform>();

    private Camera playerCamera;
    private float nextFireTime;
    private float aimBlend;
    private float bobTimer;
    private Vector3 recoilPosition;
    private Vector3 recoilRotation;

    public int SlotCount => slots.Count;
    public int CurrentIndex => currentIndex;
    public WeaponSlot CurrentSlot => slots[Mathf.Clamp(currentIndex, 0, Mathf.Max(0, slots.Count - 1))];

    public void Initialize(Camera camera)
    {
        playerCamera = camera;
        if (slots.Count == 0)
        {
            slots = CreateDefaultLoadout();
        }

        BuildViewModels();
        SelectSlot(currentIndex);
    }

    public WeaponSlot GetSlot(int index) => slots[Mathf.Clamp(index, 0, slots.Count - 1)];

    public void SelectSlot(int index)
    {
        currentIndex = Mathf.Clamp(index, 0, slots.Count - 1);
        recoilPosition = Vector3.zero;
        recoilRotation = Vector3.zero;
        aimBlend = 0f;
        bobTimer = 0f;

        for (int i = 0; i < viewModels.Count; i++)
        {
            viewModels[i].SetActive(i == currentIndex);
        }

        GameManager.Instance?.RefreshHud();
    }

    public void AddAmmo(int slotIndex, int amount)
    {
        if (slotIndex < 0 || slotIndex >= slots.Count)
        {
            return;
        }

        slots[slotIndex].reserveAmmo += Mathf.Max(1, amount);
        GameManager.Instance?.RefreshHud();
    }

    public void SetAmmoState(int[] magazineAmmo, int[] reserveAmmo, int selectedIndex)
    {
        for (int i = 0; i < slots.Count && i < magazineAmmo.Length && i < reserveAmmo.Length; i++)
        {
            slots[i].ammoInMagazine = magazineAmmo[i];
            slots[i].reserveAmmo = reserveAmmo[i];
        }

        SelectSlot(selectedIndex);
    }

    public void CopyAmmoState(int[] magazineAmmo, int[] reserveAmmo)
    {
        for (int i = 0; i < slots.Count && i < magazineAmmo.Length && i < reserveAmmo.Length; i++)
        {
            magazineAmmo[i] = slots[i].ammoInMagazine;
            reserveAmmo[i] = slots[i].reserveAmmo;
        }
    }

    public void Reload()
    {
        var slot = CurrentSlot;
        if (!slot.usesAmmo || slot.magazineSize <= 0)
        {
            GameManager.Instance?.NotifyStatus("No reload needed");
            return;
        }

        int missing = slot.magazineSize - slot.ammoInMagazine;
        if (missing <= 0 || slot.reserveAmmo <= 0)
        {
            GameManager.Instance?.NotifyStatus("Magazine full or reserve empty");
            return;
        }

        int moved = Mathf.Min(missing, slot.reserveAmmo);
        slot.ammoInMagazine += moved;
        slot.reserveAmmo -= moved;
        GameManager.Instance?.NotifyStatus($"Reloaded {slot.displayName}");
        GameManager.Instance?.RefreshHud();
    }

    public void TriggerCurrent(PlayerController owner)
    {
        if (Time.time < nextFireTime)
        {
            return;
        }

        var slot = CurrentSlot;
        nextFireTime = Time.time + Mathf.Max(0.05f, slot.fireDelay);

        switch (slot.kind)
        {
            case EquipmentKind.Hitscan:
                FireProjectilePattern(owner, slot, 1, slot.spread, false);
                break;
            case EquipmentKind.Scatter:
                FireProjectilePattern(owner, slot, Mathf.Max(1, slot.pellets), slot.spread, false);
                break;
            case EquipmentKind.Melee:
                FireMelee(owner, slot);
                break;
            case EquipmentKind.Explosive:
                FireProjectilePattern(owner, slot, 1, slot.spread, true);
                break;
            case EquipmentKind.Utility:
                UseUtility(owner, slot);
                break;
        }

        GameManager.Instance?.RefreshHud();
    }

    public void TickPresentation(float movementAmount, bool isAiming, bool isRunning)
    {
        if (viewModels.Count == 0 || currentIndex >= viewModels.Count)
        {
            return;
        }

        var slot = CurrentSlot;
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
        Vector3 targetPosition = Vector3.Lerp(slot.localPosition, slot.aimLocalPosition, aimBlend) + bobOffset + recoilPosition;
        Vector3 targetEuler = slot.localEuler + recoilRotation;

        var currentView = viewModels[currentIndex].transform;
        currentView.localPosition = Vector3.Lerp(currentView.localPosition, targetPosition, Time.deltaTime * 18f);
        currentView.localRotation = Quaternion.Slerp(currentView.localRotation, Quaternion.Euler(targetEuler), Time.deltaTime * 18f);
    }

    private void FireProjectilePattern(PlayerController owner, WeaponSlot slot, int projectiles, float spread, bool explosive)
    {
        if (!ConsumeAmmoIfNeeded(slot))
        {
            return;
        }

        ApplyFireAnimation(slot, explosive ? 1.3f : 1f);
        GameManager.Instance?.NotifyStatus($"{slot.displayName} fired");

        for (int i = 0; i < projectiles; i++)
        {
            Vector3 direction = playerCamera.transform.forward;
            if (spread > 0f)
            {
                direction = Quaternion.Euler(UnityEngine.Random.Range(-spread, spread), UnityEngine.Random.Range(-spread, spread), 0f) * direction;
            }

            CreateProjectile(
                owner.transform,
                GetMuzzleTransform().position,
                direction,
                slot.damage,
                slot.projectileSpeed,
                slot.impactForce,
                explosive ? Mathf.Max(3.2f, slot.explosiveRadius) : 0f,
                Mathf.Clamp(slot.range / Mathf.Max(8f, slot.projectileSpeed), 1.2f, 4f),
                slot.projectileScale,
                slot.color);
        }
    }

    private void FireMelee(PlayerController owner, WeaponSlot slot)
    {
        ApplyFireAnimation(slot, 1.5f);

        Vector3 center = playerCamera.transform.position + playerCamera.transform.forward * Mathf.Clamp(slot.range * 0.65f, 1f, 1.8f);
        Collider[] hits = Physics.OverlapSphere(center, 1.15f, ~0, QueryTriggerInteraction.Ignore);
        IDamageable bestTarget = null;
        IImpactReceiver bestImpact = null;
        Vector3 bestPoint = center;
        float bestDistance = float.MaxValue;

        foreach (var collider in hits)
        {
            if (collider.transform.root == owner.transform)
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
            bestTarget.ApplyDamage(slot.damage, bestPoint, hitDirection);
            bestImpact?.ApplyImpact(hitDirection * slot.impactForce, bestPoint);
            GameManager.Instance?.NotifyStatus($"{slot.displayName} connected");
            return;
        }

        GameManager.Instance?.NotifyStatus($"{slot.displayName} missed");
    }

    private void UseUtility(PlayerController owner, WeaponSlot slot)
    {
        switch (currentIndex)
        {
            case 5:
                if (owner.Inventory.UseMedkit(owner.Stats))
                {
                    GameManager.Instance?.NotifyStatus("Med injector restored health");
                }
                else
                {
                    GameManager.Instance?.NotifyStatus("No medkit charges available");
                }
                break;
            case 6:
                GameManager.Instance?.NotifyStatus("Repair tool primed - interact with machinery");
                break;
            case 7:
                GameManager.Instance?.NotifyStatus(GameManager.Instance?.DescribeNearbyThreats(owner.transform.position) ?? slot.utilityMessage);
                break;
            case 8:
                GameManager.Instance?.NotifyStatus(owner.Inventory.HasRedKey || owner.Inventory.HasBlueKey ? "Keyring synced with security doors" : "Keyring is empty");
                break;
            default:
                GameManager.Instance?.NotifyStatus(slot.utilityMessage);
                break;
        }
    }

    private bool ConsumeAmmoIfNeeded(WeaponSlot slot)
    {
        if (!slot.usesAmmo)
        {
            return true;
        }

        if (slot.ammoInMagazine <= 0)
        {
            GameManager.Instance?.NotifyStatus("Magazine empty - press reload");
            return false;
        }

        slot.ammoInMagazine--;
        return true;
    }

    private void CreateProjectile(
        Transform ownerRoot,
        Vector3 origin,
        Vector3 direction,
        float damage,
        float speed,
        float impactForce,
        float explosiveRadius,
        float lifetime,
        float projectileScale,
        Color color)
    {
        var projectile = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        projectile.name = "Projectile";
        projectile.transform.position = origin;
        projectile.transform.localScale = Vector3.one * Mathf.Max(0.04f, projectileScale);

        var rigidbody = projectile.AddComponent<Rigidbody>();
        rigidbody.useGravity = false;
        rigidbody.collisionDetectionMode = CollisionDetectionMode.ContinuousDynamic;
        rigidbody.mass = 0.08f;

        var projectileBehaviour = projectile.AddComponent<PhysicsProjectile>();
        projectileBehaviour.Configure(ownerRoot, direction, damage, speed, impactForce, lifetime, explosiveRadius, color);
    }

    private Transform GetMuzzleTransform()
    {
        if (currentIndex < muzzles.Count && muzzles[currentIndex] != null)
        {
            return muzzles[currentIndex];
        }

        return playerCamera.transform;
    }

    private void ApplyFireAnimation(WeaponSlot slot, float multiplier)
    {
        recoilPosition += new Vector3(-0.02f, 0.015f, -0.12f * multiplier);
        recoilRotation += new Vector3(-8f * multiplier, 1.5f * multiplier, UnityEngine.Random.Range(-2f, 2f) * multiplier);
        if (slot.kind == EquipmentKind.Melee)
        {
            recoilPosition += new Vector3(0.05f, -0.04f, -0.08f);
            recoilRotation += new Vector3(0f, 0f, 16f);
        }
    }

    private void BuildViewModels()
    {
        foreach (var existing in viewModels)
        {
            if (existing != null)
            {
                Destroy(existing);
            }
        }

        viewModels.Clear();
        muzzles.Clear();

        for (int i = 0; i < slots.Count; i++)
        {
            var slot = slots[i];
            var root = new GameObject($"WeaponView_{slot.displayName}");
            root.layer = 2;
            root.transform.SetParent(playerCamera.transform, false);
            root.transform.localPosition = slot.localPosition;
            root.transform.localEulerAngles = slot.localEuler;
            root.transform.localScale = Vector3.one;

            var body = GameObject.CreatePrimitive(slot.shape);
            body.name = "Body";
            body.layer = 2;
            body.transform.SetParent(root.transform, false);
            body.transform.localPosition = Vector3.zero;
            body.transform.localRotation = Quaternion.identity;
            body.transform.localScale = slot.localScale;
            var bodyRenderer = body.GetComponent<Renderer>();
            if (bodyRenderer != null)
            {
                bodyRenderer.sharedMaterial = new Material(Shader.Find("Standard")) { color = slot.color };
            }

            foreach (var collider in body.GetComponentsInChildren<Collider>())
            {
                Destroy(collider);
            }

            var barrel = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            barrel.name = "Barrel";
            barrel.layer = 2;
            barrel.transform.SetParent(root.transform, false);
            barrel.transform.localPosition = new Vector3(0f, 0.01f, slot.localScale.z * 0.55f);
            barrel.transform.localEulerAngles = new Vector3(90f, 0f, 0f);
            barrel.transform.localScale = new Vector3(slot.localScale.x * 0.25f, slot.localScale.z * 0.22f, slot.localScale.x * 0.25f);
            var barrelRenderer = barrel.GetComponent<Renderer>();
            if (barrelRenderer != null)
            {
                barrelRenderer.sharedMaterial = new Material(Shader.Find("Standard"))
                {
                    color = Color.Lerp(slot.color, Color.white, 0.18f)
                };
            }

            foreach (var collider in barrel.GetComponentsInChildren<Collider>())
            {
                Destroy(collider);
            }

            var muzzle = new GameObject("Muzzle").transform;
            muzzle.SetParent(root.transform, false);
            muzzle.localPosition = new Vector3(0f, 0f, slot.localScale.z * 0.78f);
            muzzles.Add(muzzle);

            root.SetActive(false);
            viewModels.Add(root);
        }
    }

    private static List<WeaponSlot> CreateDefaultLoadout()
    {
        return new List<WeaponSlot>
        {
            new WeaponSlot
            {
                displayName = "Pulse Pistol", kind = EquipmentKind.Hitscan, shape = PrimitiveType.Cube, color = new Color(0.18f, 0.18f, 0.22f),
                localPosition = new Vector3(0.35f, -0.3f, 0.8f), aimLocalPosition = new Vector3(0.08f, -0.2f, 0.55f), localEuler = new Vector3(0f, 15f, 0f), localScale = new Vector3(0.16f, 0.12f, 0.42f),
                damage = 18f, range = 60f, fireDelay = 0.22f, spread = 0.6f, pellets = 1, magazineSize = 16, ammoInMagazine = 16, reserveAmmo = 64, usesAmmo = true,
                projectileSpeed = 65f, impactForce = 10f, projectileScale = 0.06f
            },
            new WeaponSlot
            {
                displayName = "Scatter Shot", kind = EquipmentKind.Scatter, shape = PrimitiveType.Cube, color = new Color(0.35f, 0.15f, 0.1f),
                localPosition = new Vector3(0.32f, -0.28f, 0.74f), aimLocalPosition = new Vector3(0.06f, -0.22f, 0.52f), localEuler = new Vector3(5f, 0f, -12f), localScale = new Vector3(0.26f, 0.18f, 0.55f),
                damage = 8f, range = 30f, fireDelay = 0.8f, spread = 5.4f, pellets = 8, magazineSize = 6, ammoInMagazine = 6, reserveAmmo = 24, usesAmmo = true,
                projectileSpeed = 38f, impactForce = 7f, projectileScale = 0.05f
            },
            new WeaponSlot
            {
                displayName = "Security Baton", kind = EquipmentKind.Melee, shape = PrimitiveType.Cylinder, color = new Color(0.78f, 0.78f, 0.25f),
                localPosition = new Vector3(0.42f, -0.36f, 0.9f), aimLocalPosition = new Vector3(0.14f, -0.3f, 0.68f), localEuler = new Vector3(4f, 16f, 78f), localScale = new Vector3(0.07f, 0.34f, 0.07f),
                damage = 32f, range = 2.6f, fireDelay = 0.48f, usesAmmo = false, impactForce = 14f
            },
            new WeaponSlot
            {
                displayName = "Arc Launcher", kind = EquipmentKind.Explosive, shape = PrimitiveType.Capsule, color = new Color(0.15f, 0.45f, 0.7f),
                localPosition = new Vector3(0.3f, -0.25f, 0.76f), aimLocalPosition = new Vector3(0.03f, -0.18f, 0.5f), localEuler = new Vector3(-10f, 0f, -90f), localScale = new Vector3(0.14f, 0.22f, 0.14f),
                damage = 48f, range = 24f, fireDelay = 1.1f, magazineSize = 2, ammoInMagazine = 2, reserveAmmo = 8, usesAmmo = true,
                projectileSpeed = 26f, impactForce = 22f, explosiveRadius = 4.2f, projectileScale = 0.12f
            },
            new WeaponSlot
            {
                displayName = "Needler", kind = EquipmentKind.Hitscan, shape = PrimitiveType.Cylinder, color = new Color(0.45f, 0.45f, 0.5f),
                localPosition = new Vector3(0.34f, -0.31f, 0.78f), aimLocalPosition = new Vector3(0.07f, -0.2f, 0.54f), localEuler = new Vector3(90f, 0f, 12f), localScale = new Vector3(0.07f, 0.32f, 0.07f),
                damage = 11f, range = 55f, fireDelay = 0.11f, spread = 1.1f, pellets = 1, magazineSize = 28, ammoInMagazine = 28, reserveAmmo = 112, usesAmmo = true,
                projectileSpeed = 72f, impactForce = 6f, projectileScale = 0.04f
            },
            new WeaponSlot
            {
                displayName = "Med Injector", kind = EquipmentKind.Utility, shape = PrimitiveType.Cube, color = new Color(0.15f, 0.7f, 0.18f),
                localPosition = new Vector3(0.34f, -0.3f, 0.72f), aimLocalPosition = new Vector3(0.1f, -0.22f, 0.56f), localEuler = new Vector3(0f, 10f, 18f), localScale = new Vector3(0.12f, 0.2f, 0.26f),
                fireDelay = 0.35f, utilityMessage = "Medical injector ready"
            },
            new WeaponSlot
            {
                displayName = "Repair Tool", kind = EquipmentKind.Utility, shape = PrimitiveType.Capsule, color = new Color(0.85f, 0.55f, 0.12f),
                localPosition = new Vector3(0.34f, -0.28f, 0.8f), aimLocalPosition = new Vector3(0.08f, -0.22f, 0.6f), localEuler = new Vector3(0f, 0f, -70f), localScale = new Vector3(0.09f, 0.26f, 0.09f),
                fireDelay = 0.3f, utilityMessage = "Repair tool calibrated"
            },
            new WeaponSlot
            {
                displayName = "Scanner", kind = EquipmentKind.Utility, shape = PrimitiveType.Sphere, color = new Color(0.1f, 0.65f, 0.7f),
                localPosition = new Vector3(0.35f, -0.3f, 0.72f), aimLocalPosition = new Vector3(0.1f, -0.2f, 0.52f), localEuler = Vector3.zero, localScale = new Vector3(0.18f, 0.18f, 0.18f),
                fireDelay = 0.25f, utilityMessage = "Scanner pulsed"
            },
            new WeaponSlot
            {
                displayName = "Keyring", kind = EquipmentKind.Utility, shape = PrimitiveType.Cube, color = new Color(0.9f, 0.82f, 0.2f),
                localPosition = new Vector3(0.38f, -0.33f, 0.78f), aimLocalPosition = new Vector3(0.12f, -0.25f, 0.56f), localEuler = new Vector3(20f, 0f, 35f), localScale = new Vector3(0.12f, 0.12f, 0.12f),
                fireDelay = 0.2f, utilityMessage = "Keyring synced"
            }
        };
    }
}
