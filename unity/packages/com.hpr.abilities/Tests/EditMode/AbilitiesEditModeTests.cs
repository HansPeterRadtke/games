using NUnit.Framework;
using UnityEngine;

namespace HPR
{
    public class AbilitiesEditModeTests
    {
        [Test]
        public void AbilityRunner_RequiresUnlockBeforeActivation()
        {
            var go = new GameObject("AbilityRunner");
            var ability = ScriptableObject.CreateInstance<AbilityData>();
            var effect = ScriptableObject.CreateInstance<AbilityEffectData>();
            try
            {
                ability.Id = "repair";
                ability.DisplayName = "Repair";
                ability.Cost = 5f;
                effect.Id = "heal";
                effect.EffectType = AbilityEffectType.Heal;
                effect.Value = 10f;
                ability.Effects.Add(effect);

                var resources = go.AddComponent<TestAbilityResourcePool>();
                var runner = go.AddComponent<AbilityRunnerComponent>();
                runner.BindRuntimeServices(null, resources);
                runner.ConfigureAbilities(new[] { ability });

                Assert.That(runner.TryActivate(ability.Id), Is.False);

                runner.SetUnlockedAbilityIds(new[] { ability.Id });
                Assert.That(runner.TryActivate(ability.Id), Is.True);
                Assert.That(resources.Health, Is.EqualTo(60f));
            }
            finally
            {
                Object.DestroyImmediate(effect);
                Object.DestroyImmediate(ability);
                Object.DestroyImmediate(go);
            }
        }

        private sealed class TestAbilityResourcePool : MonoBehaviour, IAbilityResourcePool
        {
            public float Health { get; private set; } = 50f;
            public float MaxHealth => 100f;
            public float Stamina { get; private set; } = 100f;
            public float MaxStamina => 100f;

            public bool SpendAbilityCost(float amount)
            {
                if (Stamina < amount)
                {
                    return false;
                }

                Stamina -= amount;
                return true;
            }

            public void Heal(float amount)
            {
                Health = Mathf.Min(MaxHealth, Health + amount);
            }

            public void RestoreStamina(float amount)
            {
                Stamina = Mathf.Min(MaxStamina, Stamina + amount);
            }
        }
    }
}
