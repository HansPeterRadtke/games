// Private native Unity regression. Exercises the actual imported buyer archive, not mock APIs.
#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using HPR;
using HPR.GameplaySuite;
using HPR.GameplaySuite.Experimental;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace HPR.Qa.ProviderLoss
{
    public static class ProviderLossVerifier
    {
        private const string AbilityPath = "Assets/BuyerLostProviderAbility.asset";
        private const string ScenePath = "Assets/BuyerLostProviderScene.unity";
        private static void Check(bool value, string message)
        {
            if (!value) throw new InvalidOperationException(message);
        }

        public static void Run()
        {
            Check(Application.isBatchMode && !File.Exists(AbilityPath) && !File.Exists(ScenePath),
                  "Use a fresh disposable imported buyer project for this test.");
            HprSuiteIntegrationGuide.CopySampleToCustomerPath(
                "Assets/HPRGameplaySuite/Samples/RepairAbility.asset", AbilityPath);
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var player = new GameObject("Buyer actor with two independent pools");
            var shield = player.AddComponent<BuyerResourcePool>(); shield.PoolId = "shield";
            var spell = player.AddComponent<BuyerResourcePool>(); spell.PoolId = "spell";
            Check(EditorSceneManager.SaveScene(scene, ScenePath), "Could not save buyer fixture");
            var ability = AssetDatabase.LoadAssetAtPath<AbilityData>(AbilityPath);
            Check(ability != null && !string.IsNullOrWhiteSpace(ability.Id), "Customer-owned ability was not imported");
            var runner = HprSelectedAbilityInstaller.AttachExplicitly(player, ability, spell);
            Check(runner != null && new SerializedObject(runner)
                  .FindProperty("explicitResourcePoolSelection")?.boolValue == true,
                  "Installer failed to persist the buyer's explicit pool selection");
            Check(EditorSceneManager.SaveScene(scene, ScenePath),
                  "Could not save the explicit selection as a real Unity scene");
            runner.RefreshRuntimeBindings();
            Check(runner.TryActivateBySlot(0) && spell.Stamina == 80f && shield.Stamina == 100f,
                  "Initial explicit spell provider selection was not honored");
            Debug.Log("HPR_PROVIDER_LOSS_BASELINE_SELECTED_SPELL_PASS");

            // Buyer removes the selected component and saves the scene. This deletes only
            // a disposable test component, not any existing buyer project/data.
            UnityEngine.Object.DestroyImmediate(spell);
            Check(EditorSceneManager.SaveScene(scene), "Unable to save the deliberately removed provider");
            EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
            player = GameObject.Find("Buyer actor with two independent pools");
            Check(player != null, "Buyer actor disappeared after scene reload");
            shield = player.GetComponents<BuyerResourcePool>().Single();
            runner = player.GetComponent<AbilityRunnerComponent>();
            Check(runner != null && shield.PoolId == "shield" && shield.Stamina == 100f,
                  "Wrong reopened buyer configuration");
            runner.RefreshRuntimeBindings();
            bool castAfterLoss = runner.TryActivateBySlot(0);
            Debug.Log("HPR_PROVIDER_LOSS_OBSERVED after_loss_cast=" + castAfterLoss +
                      " shield_stamina=" + shield.Stamina + " status=" + runner.LastStatusMessage);
            Check(!castAfterLoss && shield.Stamina == 100f,
                  "HPR_PROVIDER_LOSS_UNSAFE_FALLBACK: selected spell provider was removed but shield was charged");

            // A deliberate new runtime binding recovers without touching Unity project settings.
            runner.BindRuntimeServices(null, shield);
            Check(runner.TryActivateBySlot(0) && shield.Stamina == 80f,
                  "An intentional new provider choice was not honored");
            Debug.Log("HPR_PROVIDER_LOSS_SAFE_AND_EXPLICIT_RECOVERY_PASS");

            var one = new GameObject("Unconfigured buyer with one provider");
            var sole = one.AddComponent<BuyerResourcePool>(); sole.PoolId = "sole";
            var autoRunner = one.AddComponent<AbilityRunnerComponent>();
            autoRunner.ConfigureAbilities(new[] { ability });
            autoRunner.SetUnlockedAbilityIds(new[] { ability.Id });
            autoRunner.RefreshRuntimeBindings();
            Check(autoRunner.TryActivateBySlot(0) && sole.Stamina == 80f,
                  "Implicit single-provider compatibility has been broken");

            var two = new GameObject("Unconfigured buyer with ambiguous providers");
            var first = two.AddComponent<BuyerResourcePool>(); first.PoolId = "first";
            var second = two.AddComponent<BuyerResourcePool>(); second.PoolId = "second";
            var ambiguous = two.AddComponent<AbilityRunnerComponent>();
            ambiguous.ConfigureAbilities(new[] { ability });
            ambiguous.SetUnlockedAbilityIds(new[] { ability.Id });
            ambiguous.RefreshRuntimeBindings();
            Check(!ambiguous.TryActivateBySlot(0) && first.Stamina == 100f && second.Stamina == 100f,
                  "Unconfigured runner silently chose one of two providers");
            Debug.Log("HPR_PROVIDER_IMPLICIT_SOLE_AND_AMBIGUOUS_PASS");
        }
    }
}
#endif
