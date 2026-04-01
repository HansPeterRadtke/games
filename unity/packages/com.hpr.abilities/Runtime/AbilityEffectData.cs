using UnityEngine;

namespace HPR
{
    [CreateAssetMenu(menuName = "HPR/Abilities/Effect", fileName = "AbilityEffectData")]
    public class AbilityEffectData : ScriptableObject
    {
        public string Id;
        public string DisplayName;
        public AbilityEffectType EffectType;
        public float Value = 10f;
        public float Radius = 4f;
        public float ForwardOffset = 1.25f;
        public Color ThemeColor = new Color(0.32f, 0.7f, 1f, 1f);
    }
}
