using System.Collections.Generic;
using UnityEngine;

namespace HPR
{
    public enum AbilityTargetType
    {
        Self,
        Area,
        Direction
    }

    public enum AbilityEffectType
    {
        Heal,
        RestoreStamina,
        AreaDamage
    }

    public interface IAbilityResourcePool
    {
        float Health { get; }
        float MaxHealth { get; }
        float Stamina { get; }
        float MaxStamina { get; }
        bool SpendAbilityCost(float amount);
        void Heal(float amount);
        void RestoreStamina(float amount);
    }

    public interface IAbilityLoadout
    {
        List<AbilityEntryViewData> BuildEntries();
        bool TryActivate(string abilityId);
        bool TryActivateBySlot(int slotIndex);
        string BuildHudSummary(params string[] slotLabels);
    }

    public sealed class AbilityEntryViewData
    {
        public string Id;
        public string DisplayName;
        public string Description;
        public float Cooldown;
        public float CooldownRemaining;
        public float Cost;
        public bool Unlocked;
        public bool Ready;
        public Color ThemeColor;
    }
}
