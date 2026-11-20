using HPR;
using UnityEngine;

namespace HPR.Qa.ProviderLoss
{
    public sealed class BuyerResourcePool : MonoBehaviour, IAbilityResourcePool
    {
        public string PoolId;
        public float Health { get; private set; } = 40f;
        public float MaxHealth => 100f;
        public float Stamina { get; private set; } = 100f;
        public float MaxStamina => 100f;
        public bool SpendAbilityCost(float cost)
        {
            if (cost > Stamina) return false;
            Stamina -= cost;
            return true;
        }
        public void Heal(float amount) { Health = Mathf.Min(MaxHealth, Health + amount); }
        public void RestoreStamina(float amount) { Stamina = Mathf.Min(MaxStamina, Stamina + amount); }
    }
}
