using UnityEngine;

[CreateAssetMenu(menuName = "FPS Demo/Data/Weapon", fileName = "WeaponData")]
public class WeaponData : ScriptableObject
{
    public string Id;
    public string DisplayName;
    public bool IncludeInDefaultLoadout = true;
    public int DefaultSlot = -1;
    public float Damage;
    public float Range;
    public float FireDelay;
    public int MaxAmmo;
    public int AmmoPerPickup;
    public GameObject ProjectilePrefab;
    public EquipmentKind Kind;
    public WeaponUtilityAction UtilityAction;
    public string LinkedItemId;
    public string UtilityMessage;
    public PrimitiveType ViewShape = PrimitiveType.Cube;
    public Color ViewColor = Color.white;
    public Vector3 ViewLocalPosition;
    public Vector3 ViewLocalEuler;
    public Vector3 ViewLocalScale = Vector3.one;
    public Vector3 AimLocalPosition;
    public float Spread;
    public int Pellets = 1;
    public int MagazineSize;
    public int StartingMagazineAmmo;
    public int StartingReserveAmmo;
    public bool UsesAmmo = true;
    public float ProjectileSpeed = 48f;
    public float ImpactForce = 12f;
    public float ProjectileScale = 0.08f;
    public float ExplosiveRadius;
}
