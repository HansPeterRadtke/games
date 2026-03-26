public interface ICharacterStats : IDamageable
{
    float MaxHealth { get; }
    float MaxStamina { get; }
    float Health { get; }
    float Stamina { get; }
    void ResetStats();
    void SetHealth(float value);
    void SetStamina(float value);
    bool ConsumeStamina(float amount);
    void RegenerateStamina(float amount);
    void Heal(float amount);
}
