using UnityEngine;

public class PlayerStats : MonoBehaviour, IDamageable
{
    [SerializeField] private float maxHealth = 100f;
    [SerializeField] private float maxStamina = 100f;
    [SerializeField] private float health = 100f;
    [SerializeField] private float stamina = 100f;

    public float MaxHealth => maxHealth;
    public float MaxStamina => maxStamina;
    public float Health => health;
    public float Stamina => stamina;
    public bool IsAlive => health > 0f;

    public void ResetStats()
    {
        health = maxHealth;
        stamina = maxStamina;
    }

    public void SetHealth(float value)
    {
        health = Mathf.Clamp(value, 0f, maxHealth);
    }

    public void SetStamina(float value)
    {
        stamina = Mathf.Clamp(value, 0f, maxStamina);
    }

    public bool ConsumeStamina(float amount)
    {
        if (stamina < amount)
        {
            return false;
        }

        stamina = Mathf.Max(0f, stamina - amount);
        return true;
    }

    public void RegenerateStamina(float amount)
    {
        stamina = Mathf.Min(maxStamina, stamina + amount);
    }

    public void Heal(float amount)
    {
        health = Mathf.Min(maxHealth, health + amount);
    }

    public void ApplyDamage(float amount, Vector3 hitPoint, Vector3 hitDirection)
    {
        if (!IsAlive)
        {
            return;
        }

        health = Mathf.Max(0f, health - amount);
        GameManager.Instance?.NotifyStatus($"Player hit: -{amount:0}");
        if (health <= 0f)
        {
            GameManager.Instance?.HandlePlayerDeath();
        }
    }
}
