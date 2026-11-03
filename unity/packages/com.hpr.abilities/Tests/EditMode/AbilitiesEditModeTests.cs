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

        [Test]
        public void AbilitySnapshot_RestoresRelativeCooldownAndUnlocks()
        {
            var go = new GameObject("Ability Snapshot");
            var ability = ScriptableObject.CreateInstance<AbilityData>();
            try
            {
                ability.Id = "qa.snap";
                ability.Cooldown = 7f;
                ability.Cost = 0f;
                var resources = go.AddComponent<TestAbilityResourcePool>();
                var runner = go.AddComponent<AbilityRunnerComponent>();
                runner.BindRuntimeServices(null, resources);
                runner.ConfigureAbilities(new[] { ability });
                runner.SetUnlockedAbilityIds(new[] { ability.Id });
                Assert.That(runner.TryActivate(ability.Id), Is.True);
                AbilityRuntimeSnapshot snapshot = runner.CaptureSnapshot();
                Assert.That(snapshot.Cooldowns.Count, Is.EqualTo(1));
                runner.SetUnlockedAbilityIds(System.Array.Empty<string>());
                runner.RestoreSnapshot(snapshot);
                Assert.That(runner.BuildEntries()[0].Unlocked, Is.True);
                Assert.That(runner.BuildEntries()[0].CooldownRemaining, Is.GreaterThan(0f));
                Assert.That(runner.TryActivate(ability.Id), Is.False);
            }
            finally { Object.DestroyImmediate(ability); Object.DestroyImmediate(go); }
        }

        [Test]
        public void InvalidSnapshot_IsRejectedBeforeAbilityStateMutation()
        {
            var go = new GameObject("Ability Snapshot Validation");
            var ability = ScriptableObject.CreateInstance<AbilityData>();
            try
            {
                ability.Id = "qa.ability";
                var runner = go.AddComponent<AbilityRunnerComponent>();
                runner.ConfigureAbilities(new[] { ability });
                runner.SetUnlockedAbilityIds(new[] { ability.Id });
                var duplicateUnlocks = new AbilityRuntimeSnapshot
                {
                    UnlockedIds = new System.Collections.Generic.List<string> { ability.Id, ability.Id }
                };
                Assert.Throws<System.ArgumentException>(() => runner.RestoreSnapshot(duplicateUnlocks));
                Assert.That(runner.BuildEntries()[0].Unlocked, Is.True);

                var unknownCooldown = new AbilityRuntimeSnapshot
                {
                    UnlockedIds = new System.Collections.Generic.List<string> { ability.Id },
                    Cooldowns = new System.Collections.Generic.List<AbilityCooldownSnapshot>
                    {
                        new AbilityCooldownSnapshot { AbilityId = "unknown.ability", Remaining = 4f }
                    }
                };
                Assert.Throws<System.ArgumentException>(() => runner.RestoreSnapshot(unknownCooldown));
                Assert.That(runner.BuildEntries()[0].Unlocked, Is.True);
            }
            finally
            {
                Object.DestroyImmediate(ability);
                Object.DestroyImmediate(go);
            }
        }

        // Public runner contract: malformed built-in data must fail before customer callbacks.
        [TestCase("negative_cost")]
        [TestCase("nan_cost")]
        [TestCase("infinite_cost")]
        [TestCase("negative_cooldown")]
        [TestCase("nan_cooldown")]
        [TestCase("infinite_cooldown")]
        [TestCase("excessive_cooldown")]
        [TestCase("null_effects")]
        [TestCase("negative_value")]
        [TestCase("nan_value")]
        [TestCase("infinite_value")]
        [TestCase("unsupported_effect")]
        [TestCase("negative_radius")]
        [TestCase("nan_radius")]
        [TestCase("infinite_radius")]
        [TestCase("nan_offset")]
        [TestCase("infinite_offset")]
        public void InvalidDefinition_RejectsBeforeResourceOrEffectCallbacks(string invalidField)
        {
            var go = new GameObject("Invalid Ability");
            var ability = ScriptableObject.CreateInstance<AbilityData>();
            var effect = ScriptableObject.CreateInstance<AbilityEffectData>();
            try
            {
                ability.Id = "qa.invalid";
                ability.Cost = 20f;
                ability.Cooldown = 30f;
                effect.EffectType = AbilityEffectType.Heal;
                effect.Value = 10f;
                ability.Effects.Add(effect);
                switch (invalidField)
                {
                    case "negative_cost": ability.Cost = -1f; break;
                    case "nan_cost": ability.Cost = float.NaN; break;
                    case "infinite_cost": ability.Cost = float.PositiveInfinity; break;
                    case "negative_cooldown": ability.Cooldown = -1f; break;
                    case "nan_cooldown": ability.Cooldown = float.NaN; break;
                    case "infinite_cooldown": ability.Cooldown = float.PositiveInfinity; break;
                    case "excessive_cooldown": ability.Cooldown = 86401f; break;
                    case "null_effects": ability.Effects = null; break;
                    case "negative_value": effect.Value = -1f; break;
                    case "nan_value": effect.Value = float.NaN; break;
                    case "infinite_value": effect.Value = float.PositiveInfinity; break;
                    case "unsupported_effect": effect.EffectType = (AbilityEffectType)999; break;
                    case "negative_radius": effect.EffectType = AbilityEffectType.AreaDamage; effect.Radius = -1f; break;
                    case "nan_radius": effect.EffectType = AbilityEffectType.AreaDamage; effect.Radius = float.NaN; break;
                    case "infinite_radius": effect.EffectType = AbilityEffectType.AreaDamage; effect.Radius = float.PositiveInfinity; break;
                    case "nan_offset": effect.ForwardOffset = float.NaN; break;
                    case "infinite_offset": effect.ForwardOffset = float.PositiveInfinity; break;
                    default: Assert.Fail("Unknown malformed-data test input"); break;
                }
                var resources = go.AddComponent<TestAbilityResourcePool>();
                var runner = go.AddComponent<AbilityRunnerComponent>();
                runner.BindRuntimeServices(null, resources);
                runner.ConfigureAbilities(new[] { ability });
                runner.SetUnlockedAbilityIds(new[] { ability.Id });

                Assert.That(runner.TryActivate(ability.Id), Is.False);
                Assert.That(resources.SpendCalls, Is.Zero, "Validation must precede customer resource callbacks");
                Assert.That(resources.Health, Is.EqualTo(50f));
                Assert.That(resources.Stamina, Is.EqualTo(100f));
                Assert.That(runner.CaptureSnapshot().Cooldowns, Is.Empty);
                Assert.That(runner.LastStatusMessage, Is.Not.Null.And.Not.Empty);
            }
            finally { Object.DestroyImmediate(effect); Object.DestroyImmediate(ability); Object.DestroyImmediate(go); }
        }

        [Test]
        public void InvalidSecondEffect_DoesNotApplyFirstEffectOrCharge()
        {
            var go = new GameObject("Whole Definition Validation");
            var ability = ScriptableObject.CreateInstance<AbilityData>();
            var first = ScriptableObject.CreateInstance<AbilityEffectData>();
            var second = ScriptableObject.CreateInstance<AbilityEffectData>();
            try
            {
                ability.Id = "qa.multi";
                first.EffectType = AbilityEffectType.Heal;
                first.Value = 10f;
                second.Value = float.NaN;
                ability.Effects.Add(first);
                ability.Effects.Add(second);
                var resources = go.AddComponent<TestAbilityResourcePool>();
                var runner = go.AddComponent<AbilityRunnerComponent>();
                runner.BindRuntimeServices(null, resources);
                runner.ConfigureAbilities(new[] { ability });
                runner.SetUnlockedAbilityIds(new[] { ability.Id });
                Assert.That(runner.TryActivate(ability.Id), Is.False);
                Assert.That(resources.SpendCalls, Is.Zero);
                Assert.That(resources.Health, Is.EqualTo(50f));
                Assert.That(resources.Stamina, Is.EqualTo(100f));
                Assert.That(runner.CaptureSnapshot().Cooldowns, Is.Empty);
            }
            finally { Object.DestroyImmediate(first); Object.DestroyImmediate(second); Object.DestroyImmediate(ability); Object.DestroyImmediate(go); }
        }

        [TestCase(false)]
        [TestCase(true)]
        public void EventOnlyAbility_EmptyOrNullSlotsRetainSnapshotCompatibility(bool nullSlot)
        {
            var go = new GameObject("Event-only Compatibility");
            var ability = ScriptableObject.CreateInstance<AbilityData>();
            try
            {
                ability.Id = "qa.event";
                ability.Cooldown = 86400f;
                ability.Cost = 0f;
                if (nullSlot) ability.Effects.Add(null);
                var resources = go.AddComponent<TestAbilityResourcePool>();
                var runner = go.AddComponent<AbilityRunnerComponent>();
                runner.BindRuntimeServices(null, resources);
                runner.ConfigureAbilities(new[] { ability });
                runner.SetUnlockedAbilityIds(new[] { ability.Id });
                Assert.That(runner.TryActivate(ability.Id), Is.True);
                var snapshot = runner.CaptureSnapshot();
                Assert.DoesNotThrow(() => runner.RestoreSnapshot(snapshot));
                Assert.That(runner.TryActivate(ability.Id), Is.False);
                Assert.That(resources.Stamina, Is.EqualTo(100f));
                Assert.That(resources.Health, Is.EqualTo(50f));
                Assert.That(resources.SpendCalls, Is.EqualTo(1));
            }
            finally { Object.DestroyImmediate(ability); Object.DestroyImmediate(go); }
        }

        [Test]
        public void ValidZeroCostAndCooldown_WithNegativeOffset_ActivatesTwice()
        {
            var go = new GameObject("Valid Boundaries");
            var ability = ScriptableObject.CreateInstance<AbilityData>();
            var effect = ScriptableObject.CreateInstance<AbilityEffectData>();
            try
            {
                ability.Id = "qa.zero";
                ability.Cost = 0f;
                ability.Cooldown = 0f;
                effect.EffectType = AbilityEffectType.Heal;
                effect.Value = 10f;
                effect.ForwardOffset = -2f;
                ability.Effects.Add(effect);
                var resources = go.AddComponent<TestAbilityResourcePool>();
                var runner = go.AddComponent<AbilityRunnerComponent>();
                runner.BindRuntimeServices(null, resources);
                runner.ConfigureAbilities(new[] { ability });
                runner.SetUnlockedAbilityIds(new[] { ability.Id });
                Assert.That(runner.TryActivate(ability.Id), Is.True);
                Assert.That(runner.TryActivate(ability.Id), Is.True);
                Assert.That(resources.SpendCalls, Is.EqualTo(2));
                Assert.That(resources.Health, Is.EqualTo(70f));
                Assert.That(resources.Stamina, Is.EqualTo(100f));
            }
            finally { Object.DestroyImmediate(effect); Object.DestroyImmediate(ability); Object.DestroyImmediate(go); }
        }

        private sealed class TestAbilityResourcePool : MonoBehaviour, IAbilityResourcePool
        {
            public int SpendCalls { get; private set; }
            public float Health { get; private set; } = 50f;
            public float MaxHealth => 100f;
            public float Stamina { get; private set; } = 100f;
            public float MaxStamina => 100f;

            public bool SpendAbilityCost(float amount)
            {
                SpendCalls++;
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
