using System;
using UnityEngine;

namespace HPR
{
    public enum EnemyRuntimeDecision
    {
        Dead,
        Patrol,
        Hold,
        Chase,
        Attack
    }

    public readonly struct EnemyAttackResult
    {
        public EnemyAttackResult(EnemyData enemy, float damage, EnemyAttackStyle style, float projectileSpeed, float projectileImpact)
        {
            Enemy = enemy;
            Damage = damage;
            Style = style;
            ProjectileSpeed = projectileSpeed;
            ProjectileImpact = projectileImpact;
        }

        public EnemyData Enemy { get; }
        public float Damage { get; }
        public EnemyAttackStyle Style { get; }
        public float ProjectileSpeed { get; }
        public float ProjectileImpact { get; }
    }

    public sealed class EnemyRuntimeState
    {
        private readonly EnemyData enemy;

        public EnemyRuntimeState(EnemyData enemy)
        {
            this.enemy = enemy != null ? enemy : throw new ArgumentNullException(nameof(enemy));
            Health = Mathf.Max(0f, enemy.MaxHealth);
        }

        public EnemyData Enemy => enemy;
        public float Health { get; private set; }
        public float AttackCooldownRemaining { get; private set; }
        public bool IsDead => Health <= 0f;
        public bool CanAttack => !IsDead && AttackCooldownRemaining <= 0f;

        public void Tick(float deltaTime)
        {
            if (deltaTime < 0f)
            {
                throw new ArgumentOutOfRangeException(nameof(deltaTime), "deltaTime must be non-negative.");
            }

            AttackCooldownRemaining = Mathf.Max(0f, AttackCooldownRemaining - deltaTime);
        }

        public float ApplyDamage(float amount)
        {
            if (amount <= 0f || IsDead)
            {
                return 0f;
            }

            float previous = Health;
            Health = Mathf.Max(0f, Health - amount);
            return previous - Health;
        }

        public float Heal(float amount)
        {
            if (amount <= 0f || IsDead)
            {
                return 0f;
            }

            float previous = Health;
            Health = Mathf.Min(Mathf.Max(0f, enemy.MaxHealth), Health + amount);
            return Health - previous;
        }

        public EnemyRuntimeDecision Decide(float targetDistance)
        {
            if (targetDistance < 0f)
            {
                throw new ArgumentOutOfRangeException(nameof(targetDistance), "targetDistance must be non-negative.");
            }

            if (IsDead)
            {
                return EnemyRuntimeDecision.Dead;
            }

            if (targetDistance <= Mathf.Max(0f, enemy.AttackRange))
            {
                return CanAttack ? EnemyRuntimeDecision.Attack : GetWaitingDecision(targetDistance);
            }

            switch (enemy.AIType)
            {
                case EnemyAIType.StationaryAttack:
                    return EnemyRuntimeDecision.Hold;
                case EnemyAIType.AggressiveChase:
                    return EnemyRuntimeDecision.Chase;
                case EnemyAIType.PatrolChase:
                default:
                    return targetDistance <= Mathf.Max(0f, enemy.ChaseRange)
                        ? EnemyRuntimeDecision.Chase
                        : EnemyRuntimeDecision.Patrol;
            }
        }

        public bool TryAttack(float targetDistance, out EnemyAttackResult result)
        {
            if (targetDistance < 0f)
            {
                throw new ArgumentOutOfRangeException(nameof(targetDistance), "targetDistance must be non-negative.");
            }

            if (!CanAttack || targetDistance > Mathf.Max(0f, enemy.AttackRange))
            {
                result = default;
                return false;
            }

            AttackCooldownRemaining = Mathf.Max(0f, enemy.AttackCooldown);
            result = new EnemyAttackResult(
                enemy,
                enemy.AttackDamage,
                enemy.AttackStyle,
                Mathf.Max(0f, enemy.ProjectileSpeed),
                Mathf.Max(0f, enemy.ProjectileImpact));
            return true;
        }

        private EnemyRuntimeDecision GetWaitingDecision(float targetDistance)
        {
            if (enemy.AIType == EnemyAIType.StationaryAttack)
            {
                return EnemyRuntimeDecision.Hold;
            }

            if (enemy.AIType == EnemyAIType.AggressiveChase)
            {
                return EnemyRuntimeDecision.Chase;
            }

            return targetDistance <= Mathf.Max(0f, enemy.ChaseRange)
                ? EnemyRuntimeDecision.Chase
                : EnemyRuntimeDecision.Patrol;
        }
    }
}
