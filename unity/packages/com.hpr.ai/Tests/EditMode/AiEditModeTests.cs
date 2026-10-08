using NUnit.Framework;
using UnityEngine;

namespace HPR
{
    public class AiEditModeTests
    {
        [Test]
        public void EnemyData_DefaultsRemainStable()
        {
            var enemy = ScriptableObject.CreateInstance<EnemyData>();
            try
            {
                Assert.That(enemy.AIType, Is.EqualTo(EnemyAIType.PatrolChase));
                Assert.That(enemy.AttackStyle, Is.EqualTo(EnemyAttackStyle.Melee));
                Assert.That(enemy.ProjectileSpeed, Is.EqualTo(28f));
            }
            finally
            {
                Object.DestroyImmediate(enemy);
            }
        }

        [Test]
        public void PatrolChase_DecidesPatrolChaseAndAttackByDistance()
        {
            var enemy = CreateEnemy();
            try
            {
                var runtime = new EnemyRuntimeState(enemy);
                Assert.That(runtime.Decide(20f), Is.EqualTo(EnemyRuntimeDecision.Patrol));
                Assert.That(runtime.Decide(8f), Is.EqualTo(EnemyRuntimeDecision.Chase));
                Assert.That(runtime.Decide(1.5f), Is.EqualTo(EnemyRuntimeDecision.Attack));
            }
            finally
            {
                Object.DestroyImmediate(enemy);
            }
        }

        [Test]
        public void TryAttack_AppliesCooldownAndReturnsAuthoredCombatData()
        {
            var enemy = CreateEnemy();
            enemy.AttackStyle = EnemyAttackStyle.Ranged;
            try
            {
                var runtime = new EnemyRuntimeState(enemy);
                Assert.That(runtime.TryAttack(1f, out EnemyAttackResult result), Is.True);
                Assert.That(result.Damage, Is.EqualTo(14f));
                Assert.That(result.Style, Is.EqualTo(EnemyAttackStyle.Ranged));
                Assert.That(runtime.AttackCooldownRemaining, Is.EqualTo(1.2f).Within(0.0001f));
                Assert.That(runtime.TryAttack(1f, out _), Is.False);
                Assert.That(runtime.Decide(1f), Is.EqualTo(EnemyRuntimeDecision.Chase));

                runtime.Tick(1.2f);
                Assert.That(runtime.Decide(1f), Is.EqualTo(EnemyRuntimeDecision.Attack));
            }
            finally
            {
                Object.DestroyImmediate(enemy);
            }
        }

        [Test]
        public void StationaryAttack_HoldsInsteadOfChasing()
        {
            var enemy = CreateEnemy();
            enemy.AIType = EnemyAIType.StationaryAttack;
            try
            {
                var runtime = new EnemyRuntimeState(enemy);
                Assert.That(runtime.Decide(8f), Is.EqualTo(EnemyRuntimeDecision.Hold));
            }
            finally
            {
                Object.DestroyImmediate(enemy);
            }
        }

        [Test]
        public void DamageAndHealing_ClampAndDeathStopsBehavior()
        {
            var enemy = CreateEnemy();
            try
            {
                var runtime = new EnemyRuntimeState(enemy);
                Assert.That(runtime.ApplyDamage(30f), Is.EqualTo(30f));
                Assert.That(runtime.Health, Is.EqualTo(70f));
                Assert.That(runtime.Heal(50f), Is.EqualTo(30f));
                Assert.That(runtime.Health, Is.EqualTo(100f));
                Assert.That(runtime.ApplyDamage(150f), Is.EqualTo(100f));
                Assert.That(runtime.IsDead, Is.True);
                Assert.That(runtime.Decide(1f), Is.EqualTo(EnemyRuntimeDecision.Dead));
                Assert.That(runtime.TryAttack(1f, out _), Is.False);
                Assert.That(runtime.Heal(10f), Is.EqualTo(0f));
            }
            finally
            {
                Object.DestroyImmediate(enemy);
            }
        }

        private static EnemyData CreateEnemy()
        {
            var enemy = ScriptableObject.CreateInstance<EnemyData>();
            enemy.MaxHealth = 100f;
            enemy.MoveSpeed = 4f;
            enemy.ChaseRange = 10f;
            enemy.AttackRange = 2f;
            enemy.AttackDamage = 14f;
            enemy.AttackCooldown = 1.2f;
            enemy.AIType = EnemyAIType.PatrolChase;
            return enemy;
        }
    }
}
