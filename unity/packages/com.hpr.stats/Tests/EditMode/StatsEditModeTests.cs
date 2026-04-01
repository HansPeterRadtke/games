using NUnit.Framework;
using UnityEngine;

namespace HPR
{
    public class StatsEditModeTests
    {
        [Test]
        public void RuntimeBonuses_ClampHealthAndStaminaAgainstEffectiveMaximums()
        {
            var go = new GameObject("Stats");
            try
            {
                var stats = go.AddComponent<ActorStatsComponent>();
                stats.SetRuntimeBonuses(50f, 25f);
                stats.SetHealth(500f);
                stats.SetStamina(500f);

                Assert.That(stats.Health, Is.EqualTo(stats.MaxHealth));
                Assert.That(stats.Stamina, Is.EqualTo(stats.MaxStamina));
            }
            finally
            {
                Object.DestroyImmediate(go);
            }
        }

        [Test]
        public void ApplyDamage_ReducesHealth()
        {
            var go = new GameObject("Stats");
            try
            {
                var stats = go.AddComponent<ActorStatsComponent>();
                stats.ResetStats();
                stats.ApplyDamage(10f, Vector3.zero, Vector3.forward);

                Assert.That(stats.Health, Is.EqualTo(stats.MaxHealth - 10f));
            }
            finally
            {
                Object.DestroyImmediate(go);
            }
        }
    }
}
