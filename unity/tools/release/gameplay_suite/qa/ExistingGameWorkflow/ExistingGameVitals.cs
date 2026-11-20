// Private representative customer fixture. No HPR dependency or shadow vendor health.
using System;
using UnityEngine;
namespace ExistingGameWorkflow
{
    public sealed class ExistingGameVitals : MonoBehaviour
    {
        [SerializeField] private float health = 40f;
        [SerializeField] private float stamina = 100f;
        public float Health => health;
        public float Stamina => stamina;
        public float MaxHealth => 100f;
        public float MaxStamina => 100f;
        public event Action Changed;
        private static bool Valid(float value) => !float.IsNaN(value) && !float.IsInfinity(value) && value >= 0f;
        public bool TrySpend(float amount)
        {
            if (!Valid(amount) || amount > stamina) return false;
            stamina -= amount; Changed?.Invoke(); return true;
        }
        public void Heal(float amount)
        {
            if (!Valid(amount)) throw new ArgumentOutOfRangeException(nameof(amount));
            health = Mathf.Clamp(health + amount, 0f, MaxHealth); Changed?.Invoke();
        }
        public void RestoreStamina(float amount)
        {
            if (!Valid(amount)) throw new ArgumentOutOfRangeException(nameof(amount));
            stamina = Mathf.Clamp(stamina + amount, 0f, MaxStamina); Changed?.Invoke();
        }
        public void Restore(float restoredHealth, float restoredStamina)
        {
            if (!Valid(restoredHealth) || restoredHealth > MaxHealth || !Valid(restoredStamina) || restoredStamina > MaxStamina)
                throw new ArgumentOutOfRangeException(nameof(restoredHealth));
            health = restoredHealth; stamina = restoredStamina; Changed?.Invoke();
        }
    }
}
