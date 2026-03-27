using System.Linq;
using UnityEngine;

public class ActorStatsComponent : MonoBehaviour, ICharacterStats
{
    [SerializeField] private float maxHealth = 100f;
    [SerializeField] private float maxStamina = 100f;
    [SerializeField] private float health = 100f;
    [SerializeField] private float stamina = 100f;
    [SerializeField] private MonoBehaviour eventBusSourceBehaviour;
    [SerializeField] private float runtimeMaxHealthBonus;
    [SerializeField] private float runtimeMaxStaminaBonus;

    public float MaxHealth => maxHealth + runtimeMaxHealthBonus;
    public float MaxStamina => maxStamina + runtimeMaxStaminaBonus;
    public float Health => health;
    public float Stamina => stamina;
    public bool IsAlive => health > 0f;

    private IGameEventBus eventBus;
    private IEventBusSource eventBusSource;

    protected virtual void Awake()
    {
        if (eventBusSourceBehaviour == null)
        {
            eventBusSourceBehaviour = GetComponentsInParent<MonoBehaviour>(true).FirstOrDefault(component => component is IEventBusSource);
        }

        eventBusSource = eventBusSourceBehaviour as IEventBusSource;
    }

    protected virtual void Start()
    {
        BindEventBus(eventBusSource != null ? eventBusSource.EventBus : null);
    }

    protected virtual void OnDestroy()
    {
        BindEventBus(null);
    }

    public void BindRuntimeEventBusSource(MonoBehaviour source)
    {
        eventBusSourceBehaviour = source;
        eventBusSource = source as IEventBusSource;
        BindEventBus(eventBusSource != null ? eventBusSource.EventBus : null);
    }

    public virtual void ResetStats()
    {
        health = MaxHealth;
        stamina = MaxStamina;
    }

    public virtual void SetRuntimeBonuses(float healthBonus, float staminaBonus)
    {
        runtimeMaxHealthBonus = Mathf.Max(0f, healthBonus);
        runtimeMaxStaminaBonus = Mathf.Max(0f, staminaBonus);
        health = Mathf.Clamp(health, 0f, MaxHealth);
        stamina = Mathf.Clamp(stamina, 0f, MaxStamina);
    }

    public virtual void SetHealth(float value)
    {
        health = Mathf.Clamp(value, 0f, maxHealth);
    }

    public virtual void SetStamina(float value)
    {
        stamina = Mathf.Clamp(value, 0f, maxStamina);
    }

    public virtual bool ConsumeStamina(float amount)
    {
        if (stamina < amount)
        {
            return false;
        }

        stamina = Mathf.Max(0f, stamina - amount);
        return true;
    }

    public virtual void RegenerateStamina(float amount)
    {
        stamina = Mathf.Min(maxStamina, stamina + amount);
    }

    public virtual void Heal(float amount)
    {
        health = Mathf.Min(MaxHealth, health + amount);
    }

    public virtual void ApplyDamage(float amount, Vector3 hitPoint, Vector3 hitDirection)
    {
        if (!IsAlive)
        {
            return;
        }

        health = Mathf.Max(0f, health - amount);
        OnDamageApplied(amount, hitPoint, hitDirection);
        if (health <= 0f)
        {
            OnDied(hitPoint, hitDirection);
        }
    }

    protected virtual void OnDamageApplied(float amount, Vector3 hitPoint, Vector3 hitDirection)
    {
    }

    protected virtual void OnDied(Vector3 hitPoint, Vector3 hitDirection)
    {
    }

    private void BindEventBus(IGameEventBus bus)
    {
        if (eventBus == bus)
        {
            return;
        }

        if (eventBus != null)
        {
            eventBus.Unsubscribe<DamageEvent>(HandleDamageEvent);
        }

        eventBus = bus;
        if (eventBus != null)
        {
            eventBus.Subscribe<DamageEvent>(HandleDamageEvent);
        }
    }

    private void HandleDamageEvent(DamageEvent gameEvent)
    {
        if (gameEvent == null || gameEvent.TargetRoot != gameObject)
        {
            return;
        }

        ApplyDamage(gameEvent.Amount, gameEvent.HitPoint, gameEvent.HitDirection);
    }
}
