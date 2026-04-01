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
    }
}
