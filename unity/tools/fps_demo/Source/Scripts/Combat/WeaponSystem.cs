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
    private Camera playerCamera;
    private float nextFireTime;

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
                FireHitscan(owner, slot, 1, slot.spread);
                break;
            case EquipmentKind.Scatter:
                FireHitscan(owner, slot, Mathf.Max(1, slot.pellets), slot.spread);
                break;
            case EquipmentKind.Melee:
                FireMelee(owner, slot);
                break;
            case EquipmentKind.Explosive:
                FireExplosive(owner, slot);
                break;
            case EquipmentKind.Utility:
                UseUtility(owner, slot);
                break;
        }

        GameManager.Instance?.RefreshHud();
    }

    private void FireHitscan(PlayerController owner, WeaponSlot slot, int pellets, float spread)
    {
        if (!ConsumeAmmoIfNeeded(slot))
        {
            return;
        }

        for (int i = 0; i < pellets; i++)
        {
            Vector3 direction = playerCamera.transform.forward;
            if (spread > 0f)
            {
                direction = Quaternion.Euler(UnityEngine.Random.Range(-spread, spread), UnityEngine.Random.Range(-spread, spread), 0f) * direction;
            }

            if (Physics.Raycast(playerCamera.transform.position, direction, out RaycastHit hit, slot.range, ~0, QueryTriggerInteraction.Ignore))
            {
                if (hit.collider.GetComponentInParent<IDamageable>() is { } damageable)
                {
                    damageable.ApplyDamage(slot.damage, hit.point, direction);
                }
            }
        }

        GameManager.Instance?.NotifyStatus($"{slot.displayName} fired");
    }

    private void FireMelee(PlayerController owner, WeaponSlot slot)
    {
        Vector3 origin = playerCamera.transform.position + playerCamera.transform.forward * 0.5f;
        if (Physics.SphereCast(origin, 0.75f, playerCamera.transform.forward, out RaycastHit hit, slot.range, ~0, QueryTriggerInteraction.Ignore))
        {
            if (hit.collider.GetComponentInParent<IDamageable>() is { } damageable)
            {
                damageable.ApplyDamage(slot.damage, hit.point, playerCamera.transform.forward);
                GameManager.Instance?.NotifyStatus($"{slot.displayName} connected");
                return;
            }
        }

        GameManager.Instance?.NotifyStatus($"{slot.displayName} missed");
    }

    private void FireExplosive(PlayerController owner, WeaponSlot slot)
    {
        if (!ConsumeAmmoIfNeeded(slot))
        {
            return;
        }

        Vector3 center = playerCamera.transform.position + playerCamera.transform.forward * Mathf.Min(slot.range, 12f);
        if (Physics.Raycast(playerCamera.transform.position, playerCamera.transform.forward, out RaycastHit hit, slot.range, ~0, QueryTriggerInteraction.Ignore))
        {
            center = hit.point;
        }

        foreach (Collider collider in Physics.OverlapSphere(center, 4f))
        {
            if (collider.GetComponentInParent<IDamageable>() is { } damageable)
            {
                damageable.ApplyDamage(slot.damage, center, (collider.transform.position - center).normalized);
            }
        }

        GameManager.Instance?.NotifyStatus($"{slot.displayName} detonated");
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

        for (int i = 0; i < slots.Count; i++)
        {
            var slot = slots[i];
            var go = GameObject.CreatePrimitive(slot.shape);
            go.name = $"WeaponView_{slot.displayName}";
            go.layer = 2;
            foreach (var collider in go.GetComponentsInChildren<Collider>())
            {
                Destroy(collider);
            }

            go.transform.SetParent(playerCamera.transform, false);
            go.transform.localPosition = slot.localPosition;
            go.transform.localEulerAngles = slot.localEuler;
            go.transform.localScale = slot.localScale;
            var renderer = go.GetComponent<Renderer>();
            if (renderer != null)
            {
                renderer.sharedMaterial = new Material(Shader.Find("Standard"))
                {
                    color = slot.color
                };
            }
            go.SetActive(false);
            viewModels.Add(go);
        }
    }

    private static List<WeaponSlot> CreateDefaultLoadout()
    {
        return new List<WeaponSlot>
        {
            new WeaponSlot { displayName = "1 Pulse Pistol", kind = EquipmentKind.Hitscan, shape = PrimitiveType.Cube, color = new Color(0.18f,0.18f,0.22f), localPosition = new Vector3(0.35f,-0.3f,0.8f), localEuler = new Vector3(0f, 15f, 0f), localScale = new Vector3(0.16f,0.12f,0.42f), damage = 18f, range = 60f, fireDelay = 0.22f, spread = 1.2f, pellets = 1, magazineSize = 16, ammoInMagazine = 16, reserveAmmo = 64, usesAmmo = true },
            new WeaponSlot { displayName = "2 Scatter Shot", kind = EquipmentKind.Scatter, shape = PrimitiveType.Sphere, color = new Color(0.35f,0.15f,0.1f), localPosition = new Vector3(0.32f,-0.28f,0.74f), localEuler = new Vector3(5f, 0f, -12f), localScale = new Vector3(0.26f,0.18f,0.55f), damage = 8f, range = 35f, fireDelay = 0.8f, spread = 6.5f, pellets = 8, magazineSize = 6, ammoInMagazine = 6, reserveAmmo = 24, usesAmmo = true },
            new WeaponSlot { displayName = "3 Security Baton", kind = EquipmentKind.Melee, shape = PrimitiveType.Cylinder, color = new Color(0.78f,0.78f,0.25f), localPosition = new Vector3(0.42f,-0.36f,0.9f), localEuler = new Vector3(4f, 16f, 78f), localScale = new Vector3(0.07f,0.34f,0.07f), damage = 28f, range = 2.3f, fireDelay = 0.55f, usesAmmo = false },
            new WeaponSlot { displayName = "4 Arc Launcher", kind = EquipmentKind.Explosive, shape = PrimitiveType.Capsule, color = new Color(0.15f,0.45f,0.7f), localPosition = new Vector3(0.3f,-0.25f,0.76f), localEuler = new Vector3(-10f, 0f, -90f), localScale = new Vector3(0.14f,0.22f,0.14f), damage = 40f, range = 25f, fireDelay = 1.1f, magazineSize = 2, ammoInMagazine = 2, reserveAmmo = 8, usesAmmo = true },
            new WeaponSlot { displayName = "5 Needler", kind = EquipmentKind.Hitscan, shape = PrimitiveType.Cylinder, color = new Color(0.45f,0.45f,0.5f), localPosition = new Vector3(0.34f,-0.31f,0.78f), localEuler = new Vector3(90f, 0f, 12f), localScale = new Vector3(0.07f,0.32f,0.07f), damage = 11f, range = 55f, fireDelay = 0.11f, spread = 1.8f, pellets = 1, magazineSize = 28, ammoInMagazine = 28, reserveAmmo = 112, usesAmmo = true },
            new WeaponSlot { displayName = "6 Med Injector", kind = EquipmentKind.Utility, shape = PrimitiveType.Cube, color = new Color(0.15f,0.7f,0.18f), localPosition = new Vector3(0.34f,-0.3f,0.72f), localEuler = new Vector3(0f, 10f, 18f), localScale = new Vector3(0.12f,0.2f,0.26f), fireDelay = 0.35f, utilityMessage = "Medical injector ready" },
            new WeaponSlot { displayName = "7 Repair Tool", kind = EquipmentKind.Utility, shape = PrimitiveType.Capsule, color = new Color(0.85f,0.55f,0.12f), localPosition = new Vector3(0.34f,-0.28f,0.8f), localEuler = new Vector3(0f, 0f, -70f), localScale = new Vector3(0.09f,0.26f,0.09f), fireDelay = 0.3f, utilityMessage = "Repair tool calibrated" },
            new WeaponSlot { displayName = "8 Scanner", kind = EquipmentKind.Utility, shape = PrimitiveType.Sphere, color = new Color(0.1f,0.65f,0.7f), localPosition = new Vector3(0.35f,-0.3f,0.72f), localEuler = Vector3.zero, localScale = new Vector3(0.18f,0.18f,0.18f), fireDelay = 0.25f, utilityMessage = "Scanner pulsed" },
            new WeaponSlot { displayName = "9 Keyring", kind = EquipmentKind.Utility, shape = PrimitiveType.Cube, color = new Color(0.9f,0.82f,0.2f), localPosition = new Vector3(0.38f,-0.33f,0.78f), localEuler = new Vector3(20f,0f,35f), localScale = new Vector3(0.12f,0.12f,0.12f), fireDelay = 0.2f, utilityMessage = "Keyring synced" }
        };
    }
}
