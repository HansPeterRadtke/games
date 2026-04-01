using UnityEngine;

namespace HPR
{
    public class AbilityDemoStats : ActorStatsComponent, IAbilityResourcePool
    {
        public bool SpendAbilityCost(float amount)
        {
            return ConsumeStamina(amount);
        }

        public void RestoreStamina(float amount)
        {
            RegenerateStamina(amount);
        }

        public void ResetVitals()
        {
            ResetStats();
        }
    }
}
