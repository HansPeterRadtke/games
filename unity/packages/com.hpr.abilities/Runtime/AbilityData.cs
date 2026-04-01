using System.Collections.Generic;
using UnityEngine;

namespace HPR
{
    [CreateAssetMenu(menuName = "HPR/Abilities/Ability", fileName = "AbilityData")]
    public class AbilityData : ScriptableObject
    {
        public string Id;
        public string DisplayName;
        [TextArea(2, 5)] public string Description;
        public AbilityTargetType TargetType = AbilityTargetType.Self;
        public float Cooldown = 8f;
        public float Cost = 15f;
        public List<AbilityEffectData> Effects = new();
        public string ActivationStatus = "Ability activated";
        public string FailureStatus = "Ability unavailable";
        public Color ThemeColor = new Color(0.24f, 0.72f, 0.96f, 1f);
    }
}
