using UnityEngine;

public enum ConsumableEffectType
{
    Heal,
    RestoreStamina
}

[CreateAssetMenu(menuName = "HPR/FPS Demo/Consumable Effect", fileName = "ConsumableEffectData")]
public class ConsumableEffectData : ScriptableObject
{
    public string Id;
    public string ItemId;
    public ConsumableEffectType EffectType = ConsumableEffectType.Heal;
    public float Amount = 10f;
    public string SuccessStatus = "Consumable applied";
    public string FailureStatus = "Consumable has no effect right now";
    public Color ThemeColor = new Color(0.2f, 0.7f, 0.3f, 1f);
}
