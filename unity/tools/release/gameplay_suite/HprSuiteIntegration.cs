// Copyright (c) Multiverse Studio. Included with HPR Gameplay Systems Suite.
// Real adapters, not mock components: AbilityRunner consumes Stats and AreaDamage
// is delivered to EnemyRuntimeState via the typed EventBus in the playground.
using UnityEngine;
using HPR;

namespace HPR.GameplaySuite
{
    [DisallowMultipleComponent]
    public sealed class HprSuiteAbilityPool : MonoBehaviour, IAbilityResourcePool
    {
        [SerializeField] private ActorStatsComponent stats;

        // Persist the typed component reference in the buyer scene/prefab.
        // The fallback makes an existing Stats+Pool GameObject work when a
        // customer explicitly adds both components without custom C# Bind.
        // It NEVER creates a controller or new stats component implicitly.
        public ActorStatsComponent StatsSource
        {
            get
            {
                ActorStatsComponent source = stats != null ? stats : GetComponent<ActorStatsComponent>();
                return source != null && source.gameObject == gameObject ? source : null;
            }
        }
        public bool HasValidStatsSource => StatsSource != null;

        private void Reset()
        {
            stats = GetComponent<ActorStatsComponent>();
        }

        public void Bind(ActorStatsComponent source)
        {
            if (source == null || source.gameObject != gameObject)
                throw new System.ArgumentException("HPR ability pool requires a Stats component on the same scene object.");
            stats = source;
        }

        public float Health => StatsSource != null ? StatsSource.Health : 0f;
        public float MaxHealth => StatsSource != null ? StatsSource.MaxHealth : 0f;
        public float Stamina => StatsSource != null ? StatsSource.Stamina : 0f;
        public float MaxStamina => StatsSource != null ? StatsSource.MaxStamina : 0f;
        public bool SpendAbilityCost(float amount)
        {
            var source = StatsSource;
            return source != null && source.IsAlive && source.ConsumeStamina(amount);
        }
        public void Heal(float amount)
        {
            var source = StatsSource;
            if (source != null) source.Heal(amount);
        }
        public void RestoreStamina(float amount)
        {
            var source = StatsSource;
            if (source != null) source.RegenerateStamina(amount);
        }
    }

    [DisallowMultipleComponent]
    public sealed class HprSuiteEnemyTarget : MonoBehaviour, IDamageable
    {
        private HprGameplaySuitePlayground host;
        public void Bind(HprGameplaySuitePlayground controller) { host = controller; }
        public bool IsAlive => host != null && host.EnemyHealth > 0f;
        public void ApplyDamage(float amount, Vector3 point, Vector3 direction)
        {
            if (host != null) host.DamageEnemy(amount, "Ability AreaDamage");
        }
    }
}
