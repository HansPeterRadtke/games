using UnityEngine;

[CreateAssetMenu(menuName = "FPS Demo/Data/Item", fileName = "ItemData")]
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
}
