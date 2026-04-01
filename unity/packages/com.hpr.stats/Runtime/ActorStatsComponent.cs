using UnityEngine;

namespace HPR
{
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

        private IEventBus eventBus;
        private IEventBusSource eventBusSource;

        protected virtual void Awake()
        {
            eventBusSource = eventBusSourceBehaviour as IEventBusSource;
        }

        protected virtual void Start()
        {
            RefreshRuntimeBindings();
        }

        protected virtual void OnDestroy()
        {
            BindEventBus(null);
        }

        public void BindRuntimeEventBusSource(MonoBehaviour source)
        {
            eventBusSourceBehaviour = source;
            RefreshRuntimeBindings();
        }

        public void RefreshRuntimeBindings()
        {
            eventBusSource = eventBusSourceBehaviour as IEventBusSource;
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
            health = Mathf.Clamp(value, 0f, MaxHealth);
        }

        public virtual void SetStamina(float value)
        {
            stamina = Mathf.Clamp(value, 0f, MaxStamina);
        }

        public virtual bool ConsumeStamina(float amount)
        {
            amount = Mathf.Max(0f, amount);
            if (stamina < amount)
            {
                return false;
            }

            stamina = Mathf.Max(0f, stamina - amount);
            return true;
        }

        public virtual void RegenerateStamina(float amount)
        {
            stamina = Mathf.Min(MaxStamina, stamina + Mathf.Max(0f, amount));
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

        private void BindEventBus(IEventBus bus)
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
}
