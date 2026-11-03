using System.Collections.Generic;
using UnityEngine;

namespace HPR
{
    [CreateAssetMenu(menuName = "HPR/Abilities/Ability", fileName = "AbilityData")]
    public class AbilityData : ScriptableObject
    {
        public const float MaximumCooldownSeconds = 86400f;

        public string Id;
        public string DisplayName;
        [TextArea(2, 5)] public string Description;
        public AbilityTargetType TargetType = AbilityTargetType.Self;
        [Min(0f), Tooltip("Cooldown in seconds, from 0 through 86400 (one day). This matches saved ability state.")]
        public float Cooldown = 8f;
        [Min(0f), Tooltip("Resource cost in stamina points. Must be finite and nonnegative.")]
        public float Cost = 15f;
        public List<AbilityEffectData> Effects = new();
        public string ActivationStatus = "Ability activated";
        public string FailureStatus = "Ability unavailable";
        public Color ThemeColor = new Color(0.24f, 0.72f, 0.96f, 1f);

        /// <summary>Validate the whole built-in definition before spending any resources.</summary>
        public bool TryValidateRuntimeSettings(out string reason)
        {
            if (float.IsNaN(Cost) || float.IsInfinity(Cost) || Cost < 0f)
            {
                reason = "Ability cost must be finite and nonnegative (stamina points).";
                return false;
            }
            if (float.IsNaN(Cooldown) || float.IsInfinity(Cooldown) || Cooldown < 0f || Cooldown > MaximumCooldownSeconds)
            {
                reason = "Ability cooldown must be finite and from 0 through 86400 seconds.";
                return false;
            }
            if (Effects == null)
            {
                reason = "The ability has no configured effect.";
                return false;
            }
            foreach (AbilityEffectData effect in Effects)
            {
                // Preserve event-only loadouts and existing optional/empty effect slots.
                if (effect == null) continue;
                if (!effect.TryValidateRuntimeSettings(out string effectReason))
                {
                    reason = "Ability effect is invalid: " + effectReason;
                    return false;
                }
            }
            reason = string.Empty;
            return true;
        }
    }
}
