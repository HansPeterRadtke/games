// Private native API/Editor-validation regression; no GUI or terms interaction.
#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using HPR;
using HPR.GameplaySuite.Experimental;
using ExistingGameWorkflow;

public static class HprAbilityConfigurationValidator
{
    [Serializable] private sealed class CaseResult
    {
        public string name, exception, previewMessage;
        public bool expectedAccepted, expectedPreviewAccepted, actualAccepted, previewAccepted, snapshotRestorable, passed;
        public float health, stamina;
    }
    [Serializable] private sealed class Results { public CaseResult[] cases; }
    private sealed class Spec
    {
        public string name;
        public bool valid, preview;
        public float healing;
        public Action<AbilityData, AbilityEffectData> configure;
        public Spec(string name, bool valid, Action<AbilityData, AbilityEffectData> configure, bool? preview = null, float healing = 20f)
        { this.name = name; this.valid = valid; this.configure = configure; this.preview = preview ?? valid; this.healing = healing; }
    }
    private static double started;
    public static void RunAfterStartup()
    {
        started = EditorApplication.timeSinceStartup;
        EditorApplication.update += WhenIdle;
    }
    private static void WhenIdle()
    {
        if (EditorApplication.timeSinceStartup - started < 20 || EditorApplication.isCompiling || EditorApplication.isUpdating) return;
        EditorApplication.update -= WhenIdle;
        string root = Environment.GetEnvironmentVariable("HPR_WORKFLOW_RECEIPT_ROOT");
        try
        {
            if (!Directory.Exists(root) || EditorApplication.isPlayingOrWillChangePlaymode)
                throw new InvalidOperationException("Unused private API regression root required");
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            string folder = "Assets/AbilityConfigProbe_" + DateTime.UtcNow.Ticks;
            AssetDatabase.CreateFolder("Assets", Path.GetFileName(folder));
            var specs = new[]
            {
                new Spec("valid_default", true, (a,e) => { }),
                new Spec("valid_zero_cost_and_cooldown", true, (a,e) => { a.Cost = 0; a.Cooldown = 0; }),
                new Spec("valid_maximum_saved_cooldown", true, (a,e) => a.Cooldown = 86400),
                new Spec("valid_event_only_runtime_snapshot", true, (a,e) => { a.Cost = 0; a.Cooldown = 7; a.Effects.Clear(); }, false, 0),
                new Spec("reject_excessive_cooldown", false, (a,e) => a.Cooldown = 86401),
                new Spec("reject_negative_cooldown", false, (a,e) => a.Cooldown = -1),
                new Spec("reject_nan_cooldown", false, (a,e) => a.Cooldown = float.NaN),
                new Spec("reject_infinite_cooldown", false, (a,e) => a.Cooldown = float.PositiveInfinity),
                new Spec("reject_negative_cost", false, (a,e) => a.Cost = -1),
                new Spec("reject_nan_cost", false, (a,e) => a.Cost = float.NaN),
                new Spec("reject_infinite_cost", false, (a,e) => a.Cost = float.PositiveInfinity),
                new Spec("reject_null_effect_list", false, (a,e) => a.Effects = null),
                new Spec("reject_nan_effect_value", false, (a,e) => e.Value = float.NaN),
                new Spec("reject_negative_effect_value", false, (a,e) => e.Value = -1),
                new Spec("reject_unsupported_effect_type", false, (a,e) => e.EffectType = (AbilityEffectType)999),
                new Spec("reject_negative_damage_radius", false, (a,e) => { e.EffectType = AbilityEffectType.AreaDamage; e.Radius = -1; }),
                new Spec("reject_infinite_effect_offset", false, (a,e) => e.ForwardOffset = float.PositiveInfinity)
            };
            var results = new List<CaseResult>();
            foreach (Spec spec in specs)
            {
                var actor = new GameObject("Configuration regression " + spec.name);
                var vitals = actor.AddComponent<ExistingGameVitals>();
                var provider = actor.AddComponent<HprExistingVitalsAdapter>(); provider.Configure(vitals);
                var effect = ScriptableObject.CreateInstance<AbilityEffectData>();
                effect.Id = "effect_" + spec.name; effect.EffectType = AbilityEffectType.Heal; effect.Value = 20;
                var ability = ScriptableObject.CreateInstance<AbilityData>();
                ability.Id = "ability_" + spec.name; ability.Cost = 20; ability.Cooldown = 30; ability.Effects.Add(effect);
                spec.configure(ability, effect);
                AssetDatabase.CreateAsset(effect, folder + "/" + spec.name + "_effect.asset");
                AssetDatabase.CreateAsset(ability, folder + "/" + spec.name + "_ability.asset");
                string preview = HprSelectedAbilityInstaller.ValidateSelection(actor, ability, provider);
                var runner = actor.AddComponent<AbilityRunnerComponent>();
                runner.BindRuntimeServices(null, provider); runner.ConfigureAbilities(new[] { ability });
                runner.SetUnlockedAbilityIds(new[] { ability.Id });
                bool activated = false; string thrown = "";
                try { activated = runner.TryActivate(ability.Id); }
                catch (Exception error) { thrown = error.GetType().Name; }
                bool restorable = runner.TryValidateSnapshot(runner.CaptureSnapshot(), out string reason);
                bool eventOnlyCompatible = true;
                if (spec.name == "valid_event_only_runtime_snapshot" && activated && restorable)
                {
                    var saved = runner.CaptureSnapshot();
                    runner.SetUnlockedAbilityIds(Array.Empty<string>()); runner.RestoreSnapshot(saved);
                    eventOnlyCompatible = runner.BuildEntries().Single(x => x.Id == ability.Id).Unlocked &&
                        runner.BuildEntries().Single(x => x.Id == ability.Id).CooldownRemaining > 0 && !runner.TryActivate(ability.Id);
                }
                float expectedHealth = spec.valid ? 40 + spec.healing : 40;
                float expectedStamina = spec.valid ? 100 - ability.Cost : 100;
                var result = new CaseResult { name = spec.name, expectedAccepted = spec.valid,
                    actualAccepted = activated, expectedPreviewAccepted = spec.preview, previewAccepted = preview == null, previewMessage = preview ?? "",
                    exception = thrown, snapshotRestorable = restorable, health = vitals.Health, stamina = vitals.Stamina };
                result.passed = activated == spec.valid && (preview == null) == spec.preview && thrown == "" && restorable && eventOnlyCompatible &&
                    vitals.Health == expectedHealth && vitals.Stamina == expectedStamina;
                results.Add(result);
                UnityEngine.Object.DestroyImmediate(actor);
            }
            File.WriteAllText(Path.Combine(root, "configuration-cases.json"), JsonUtility.ToJson(new Results { cases = results.ToArray() }, true));
            File.WriteAllLines(Path.Combine(root, "native-config-result.txt"), results.Select(x => x.name + (x.passed ? "=PASS" : "=FAIL")));
            bool passed = results.All(x => x.passed);
            if (!passed) File.WriteAllText(Path.Combine(root, "native-config-failure.txt"), string.Join("\n", results.Where(x => !x.passed).Select(x => x.name)));
            EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            EditorApplication.Exit(passed ? 0 : 3);
        }
        catch (Exception error)
        {
            if (Directory.Exists(root)) File.WriteAllText(Path.Combine(root, "native-config-failure.txt"), error.ToString());
            Debug.LogException(error); EditorApplication.Exit(3);
        }
    }
}
#endif
