using UnityEngine;

[CreateAssetMenu(menuName = "HPR/Inventory/Item", fileName = "ItemData")]
public class ItemData : ScriptableObject
{
    public string Id;
    public ItemType ItemType;
    public string DisplayName;
    public bool IncludeInKnownItems = true;
    public Sprite Icon;
    public int Value;
    public string Description;
    public string PickupPrompt;
    public string PickupStatus;
    public string LinkedWeaponId;
    public Color PlaceholderColor = Color.white;
    public int StartingPlayerQuantity;
    public GameObject PickupPrefab;
    public Vector3 PickupVisualLocalPosition;
    public Vector3 PickupVisualLocalEuler;
    public Vector3 PickupVisualLocalScale = Vector3.one;
}
