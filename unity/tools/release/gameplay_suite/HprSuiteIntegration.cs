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
        private ActorStatsComponent stats;
        public void Bind(ActorStatsComponent source) { stats = source; }
        public float Health => stats != null ? stats.Health : 0f;
        public float MaxHealth => stats != null ? stats.MaxHealth : 0f;
        public float Stamina => stats != null ? stats.Stamina : 0f;
        public float MaxStamina => stats != null ? stats.MaxStamina : 0f;
        public bool SpendAbilityCost(float amount) => stats != null && stats.IsAlive && stats.ConsumeStamina(amount);
        public void Heal(float amount) { if (stats != null) stats.Heal(amount); }
        public void RestoreStamina(float amount) { if (stats != null) stats.RegenerateStamina(amount); }
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
