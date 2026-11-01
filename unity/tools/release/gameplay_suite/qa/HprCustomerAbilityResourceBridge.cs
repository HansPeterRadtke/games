// Private QA-only example. The customer's own controller and settings are not rewritten.
// Excluded from any commercial package and included only in disposable Unity test games.
using UnityEngine;
using HPR;

namespace HprCustomerIntegrationQa
{
    public sealed class HprCustomerAbilityResourceBridge : MonoBehaviour, IAbilityResourcePool
    {
        [SerializeField] private float maxHealth = 100f;
        [SerializeField] private float currentHealth = 40f;
        [SerializeField] private float maxStamina = 100f;
        [SerializeField] private float currentStamina = 100f;

        public float MaxHealth => maxHealth;
        public float Health => currentHealth;
        public float MaxStamina => maxStamina;
        public float Stamina => currentStamina;

        public bool SpendAbilityCost(float cost)
        {
            if (float.IsNaN(cost) || float.IsInfinity(cost) || cost < 0f ||
                currentStamina < cost)
                return false;
            currentStamina -= cost;
            return true;
        }

        public void Heal(float amount)
        {
            if (float.IsNaN(amount) || float.IsInfinity(amount) || amount < 0f)
                return;
            currentHealth = Mathf.Clamp(currentHealth + amount, 0f, maxHealth);
        }

        public void RestoreStamina(float amount)
        {
            if (float.IsNaN(amount) || float.IsInfinity(amount) || amount < 0f)
                return;
            currentStamina = Mathf.Clamp(currentStamina + amount, 0f, maxStamina);
        }
    }
}
