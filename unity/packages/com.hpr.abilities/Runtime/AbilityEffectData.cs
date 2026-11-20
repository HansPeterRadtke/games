using UnityEngine;

namespace HPR
{
    [CreateAssetMenu(menuName = "HPR/Abilities/Effect", fileName = "AbilityEffectData")]
    public class AbilityEffectData : ScriptableObject
    {
        public string Id;
        public string DisplayName;
        public AbilityEffectType EffectType;
        [Min(0f), Tooltip("Effect amount in health, stamina or damage points; finite and nonnegative.")]
        public float Value = 10f;
        [Min(0f), Tooltip("Area-damage radius in meters. Values below 0.25 use 0.25 meters.")]
        public float Radius = 4f;
        [Tooltip("Finite offset from the actor in meters; negative values place the origin behind it.")]
        public float ForwardOffset = 1.25f;
        public Color ThemeColor = new Color(0.32f, 0.7f, 1f, 1f);

        public bool TryValidateRuntimeSettings(out string reason)
        {
            if (EffectType != AbilityEffectType.Heal && EffectType != AbilityEffectType.RestoreStamina &&
                EffectType != AbilityEffectType.AreaDamage)
            {
                reason = "Unsupported built-in effect type.";
                return false;
            }
            if (float.IsNaN(Value) || float.IsInfinity(Value) || Value < 0f)
            {
                reason = "Effect value must be finite and nonnegative.";
                return false;
            }
            if (float.IsNaN(ForwardOffset) || float.IsInfinity(ForwardOffset))
            {
                reason = "Effect forward offset must be finite (meters).";
                return false;
            }
            if (EffectType == AbilityEffectType.AreaDamage &&
                (float.IsNaN(Radius) || float.IsInfinity(Radius) || Radius < 0f))
            {
                reason = "Area-damage radius must be finite and nonnegative (meters).";
                return false;
            }
            reason = string.Empty;
            return true;
        }
    }
}
