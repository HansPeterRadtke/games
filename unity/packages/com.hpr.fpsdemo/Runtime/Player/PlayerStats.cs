using System.Linq;
using UnityEngine;

public class PlayerStats : MonoBehaviour, IPlayerStats
{
    [SerializeField] private float maxHealth = 100f;
    [SerializeField] private float maxStamina = 100f;
    [SerializeField] private float health = 100f;
    [SerializeField] private float stamina = 100f;
    [SerializeField] private MonoBehaviour servicesBehaviour;

    public float MaxHealth => maxHealth;
    public float MaxStamina => maxStamina;
    public float Health => health;
    public float Stamina => stamina;
    public bool IsAlive => health > 0f;

    private IGameEventBus eventBus;
    private IEventBusSource eventBusSource;
    private IStatusMessageSink statusSink;
    private IPlayerDeathHandler playerDeathHandler;

    private void Awake()
    {
        servicesBehaviour = servicesBehaviour != null ? servicesBehaviour : GetComponentsInParent<MonoBehaviour>(true).FirstOrDefault(component => component is IEventBusSource || component is IStatusMessageSink || component is IPlayerDeathHandler);
        eventBusSource = servicesBehaviour as IEventBusSource;
        statusSink = servicesBehaviour as IStatusMessageSink;
        playerDeathHandler = servicesBehaviour as IPlayerDeathHandler;
    }

    private void Start()
    {
        BindEventBus(eventBusSource != null ? eventBusSource.EventBus : null);
    }

    private void OnDestroy()
    {
        BindEventBus(null);
    }

    public void BindRuntimeServices(MonoBehaviour services)
    {
        servicesBehaviour = services;
        eventBusSource = servicesBehaviour as IEventBusSource;
        statusSink = servicesBehaviour as IStatusMessageSink;
        playerDeathHandler = servicesBehaviour as IPlayerDeathHandler;
        BindEventBus(eventBusSource != null ? eventBusSource.EventBus : null);
    }

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
        statusSink?.NotifyStatus($"Player hit: -{amount:0}");
        if (health <= 0f)
        {
            playerDeathHandler?.HandlePlayerDeath();
        }
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
