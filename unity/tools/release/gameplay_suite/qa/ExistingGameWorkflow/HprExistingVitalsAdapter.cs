// Private integration example. Delegates to the EXISTING game-owned state.
using System;
using UnityEngine;
using HPR;
namespace ExistingGameWorkflow
{
    public sealed class HprExistingVitalsAdapter : MonoBehaviour, IAbilityResourcePool
    {
        [SerializeField] private ExistingGameVitals source;
        private ExistingGameVitals Source => source != null ? source : throw new InvalidOperationException("Existing game vitals must be assigned");
        public void Configure(ExistingGameVitals value)
        {
            if (value == null || value.gameObject != gameObject) throw new ArgumentException("Assign vitals on this same actor");
            source = value;
        }
        public float Health => Source.Health;
        public float MaxHealth => Source.MaxHealth;
        public float Stamina => Source.Stamina;
        public float MaxStamina => Source.MaxStamina;
        public bool SpendAbilityCost(float amount) => Source.TrySpend(amount);
        public void Heal(float amount) => Source.Heal(amount);
        public void RestoreStamina(float amount) => Source.RestoreStamina(amount);
    }
}
