using System.Collections.Generic;
using UnityEngine;

namespace HPR
{
    [CreateAssetMenu(menuName = "HPR/FPS Demo/Skill", fileName = "SkillNodeData")]
    public class SkillNodeData : ScriptableObject
    {
        public string Id;
        public string DisplayName;
        [TextArea(2, 5)] public string Description;
        public int Cost = 1;
        public bool StartingUnlocked;
        public List<SkillNodeData> Prerequisites = new();
        public float MaxHealthBonus;
        public float MaxStaminaBonus;
        [Min(0f)] public float DamageMultiplierBonus;
        [Min(0f)] public float MoveSpeedMultiplierBonus;
        public List<AbilityData> GrantedAbilities = new();
        public Color ThemeColor = new Color(0.26f, 0.66f, 0.95f, 1f);
    }
}
