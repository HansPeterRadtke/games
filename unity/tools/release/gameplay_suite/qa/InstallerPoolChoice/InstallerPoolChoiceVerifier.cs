using System;
using System.IO;
using System.Linq;
using System.Reflection;
using HPR.GameplaySuite;
using HPR.GameplaySuite.Experimental;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEditor.UIElements;
using UnityEngine;
using UnityEngine.UIElements;

namespace HPR.Qa.InstallerPoolChoice
{
    public static class InstallerPoolChoiceVerifier
    {
        private const string AbilityPath = "Assets/BuyerRecovery.asset";
        private const string ScenePath = "Assets/BuyerPoolChoice.unity";

        private static void Check(bool ok, string message)
        {
            if (!ok) throw new InvalidOperationException(message);
        }

        // Invoke the handler used by the real button, including its final validation.
        private static void Attach(HprSelectedAbilityInstaller window)
        {
            typeof(HprSelectedAbilityInstaller).GetMethod("AttachRequested",
                BindingFlags.Instance | BindingFlags.NonPublic).Invoke(window, null);
        }

        public static void Run()
        {
            Check(Application.isBatchMode && !File.Exists(AbilityPath) && !File.Exists(ScenePath),
                "Use a new disposable buyer project.");
            var ability = (AbilityData)HprSuiteIntegrationGuide.CopySampleToCustomerPath(
                "Assets/HPRGameplaySuite/Samples/RepairAbility.asset", AbilityPath);
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var player = new GameObject("Buyer player");
            var shield = player.AddComponent<BuyerResourcePool>();
            shield.PoolId = "shield";
            var spell = player.AddComponent<BuyerResourcePool>();
            spell.PoolId = "spell";
            var empty = new GameObject("Buyer without a provider");
            var single = new GameObject("Buyer with one provider");
            var sole = single.AddComponent<BuyerResourcePool>();
            sole.PoolId = "solo";
            Check(EditorSceneManager.SaveScene(scene, ScenePath), "Could not save buyer fixture.");
            byte[] before = File.ReadAllBytes(ScenePath);
            ability = AssetDatabase.LoadAssetAtPath<AbilityData>(AbilityPath);
            Check(ability != null && !string.IsNullOrWhiteSpace(ability.Id), "Copied ability must be reloaded after asset import.");
            Selection.activeGameObject = player;
            var window = ScriptableObject.CreateInstance<HprSelectedAbilityInstaller>();
            // In batch mode a detached ObjectField does not dispatch value changes.
            // Host the actual controls on the installed Editor's in-memory event panel.
            var panelType = typeof(VisualElement).Assembly.GetType("UnityEngine.UIElements.Panel", true);
            var createPanel = panelType.GetMethod("CreateEditorPanel",
                BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic);
            var panel = (IPanel)createPanel.Invoke(null, new object[] { window });
            try
            {
                panel.visualTree.Add(window.rootVisualElement);
                window.CreateGUI();
                var fields = window.rootVisualElement.Query<ObjectField>().ToList();
                var target = fields.Single(x => x.label == "Selected object");
                var pool = fields.Single(x => x.label == "Resource provider");
                fields.Single(x => x.label == "Customer-owned ability").value = ability;
                typeof(HprSelectedAbilityInstaller).GetField("ability", BindingFlags.Instance | BindingFlags.NonPublic).SetValue(window, ability);
                typeof(HprSelectedAbilityInstaller).GetMethod("Refresh", BindingFlags.Instance | BindingFlags.NonPublic).Invoke(window, null);
                var attach = window.rootVisualElement.Query<Button>().ToList()
                    .Single(x => x.text.StartsWith("Attach ability"));
                var help = window.rootVisualElement.Q<HelpBox>();
                Check(target.value == player && pool.panel == panel, "The buyer controls lack their target or event panel.");
                Debug.Log("HPR_POOL_PREVIEW provider=" + (pool.value as BuyerResourcePool)?.PoolId +
                    " attach=" + attach.enabledSelf + " message=" + help.text);
                if (pool.value == shield && attach.enabledSelf)
                {
                    Attach(window);
                    var wrong = player.GetComponent<AbilityRunnerComponent>();
                    Check(wrong != null, "The baseline button did not attach a runner.");
                    wrong.RefreshRuntimeBindings();
                    Check(wrong.TryActivateBySlot(0) && shield.Stamina == 80f && spell.Stamina == 100f,
                        "The baseline cast did not reproduce the expected wrong debit.");
                    throw new InvalidOperationException("HPR_POOL_CHOICE_REGRESSION: no provider chosen; shield 80, spell 100");
                }
                Check(pool.value == null && !attach.enabledSelf && help.text.Contains("multiple"),
                    "Two providers need an explicit choice and an explanation.");
                Selection.activeGameObject = empty;
                typeof(HprSelectedAbilityInstaller).GetMethod("RefreshFromSelection", BindingFlags.Instance | BindingFlags.NonPublic).Invoke(window, null);
                Check(pool.value == null && !attach.enabledSelf, "A player without a pool was accepted.");
                Selection.activeGameObject = single;
                typeof(HprSelectedAbilityInstaller).GetMethod("RefreshFromSelection", BindingFlags.Instance | BindingFlags.NonPublic).Invoke(window, null);
                Debug.Log("HPR_POOL_ABILITY id=" + ability.Id + " windowAbility=" + (typeof(HprSelectedAbilityInstaller).GetField("ability", BindingFlags.Instance | BindingFlags.NonPublic).GetValue(window) as AbilityData)?.Id);
                typeof(HprSelectedAbilityInstaller).GetField("ability", BindingFlags.Instance | BindingFlags.NonPublic).SetValue(window, ability);
                typeof(HprSelectedAbilityInstaller).GetMethod("Refresh", BindingFlags.Instance | BindingFlags.NonPublic).Invoke(window, null);
                Debug.Log("HPR_POOL_SINGLE selected=" + (target.value as GameObject)?.name + " provider=" + (pool.value as BuyerResourcePool)?.PoolId + " attach=" + attach.enabledSelf + " message=" + help.text);
                Check(pool.value == sole && attach.enabledSelf, "A single provider should be selected.");
                // Change the components while the preview is open. No frame or new selection is required.
                var second = single.AddComponent<BuyerResourcePool>();
                second.PoolId = "second";
                Attach(window);
                Check(single.GetComponent<AbilityRunnerComponent>() == null && pool.value == null && !attach.enabledSelf,
                    "A stale single-provider preview attached after a second pool appeared.");
                Selection.activeGameObject = player;
                typeof(HprSelectedAbilityInstaller).GetMethod("RefreshFromSelection", BindingFlags.Instance | BindingFlags.NonPublic).Invoke(window, null);
                pool.value = spell;
                typeof(HprSelectedAbilityInstaller).GetField("provider", BindingFlags.Instance | BindingFlags.NonPublic).SetValue(window, spell);
                typeof(HprSelectedAbilityInstaller).GetField("providerChosen", BindingFlags.Instance | BindingFlags.NonPublic).SetValue(window, true);
                typeof(HprSelectedAbilityInstaller).GetMethod("Refresh", BindingFlags.Instance | BindingFlags.NonPublic).Invoke(window, null);
                Check(pool.value == spell && attach.enabledSelf, "The buyer's explicit choice was refused.");
                Check(player.GetComponent<AbilityRunnerComponent>() == null && before.SequenceEqual(File.ReadAllBytes(ScenePath)),
                    "Preview changed the saved buyer scene or added a runner.");
                Attach(window);
                var runner = player.GetComponent<AbilityRunnerComponent>();
                Check(runner != null && new SerializedObject(runner).FindProperty("resourcePoolBehaviour")
                    .objectReferenceValue == spell, "The runner did not receive the selected provider.");
                Check(before.SequenceEqual(File.ReadAllBytes(ScenePath)), "Attach saved the buyer scene automatically.");
                Check(EditorSceneManager.SaveScene(scene), "Could not save the buyer's explicit choice.");
            }
            finally
            {
                window.rootVisualElement.RemoveFromHierarchy();
                ((IDisposable)panel).Dispose();
                UnityEngine.Object.DestroyImmediate(window);
            }
            EditorSceneManager.OpenScene(ScenePath);
            player = GameObject.Find("Buyer player");
            var pools = player.GetComponents<BuyerResourcePool>();
            shield = pools.Single(p => p.PoolId == "shield");
            spell = pools.Single(p => p.PoolId == "spell");
            var loaded = player.GetComponent<AbilityRunnerComponent>();
            Check(loaded != null && new SerializedObject(loaded).FindProperty("resourcePoolBehaviour")
                .objectReferenceValue == spell, "Reload lost the chosen provider.");
            loaded.RefreshRuntimeBindings();
            Check(loaded.TryActivateBySlot(0) && spell.Stamina == 80f && spell.Health == 60f &&
                shield.Stamina == 100f && shield.Health == 40f, "Reloaded cast used the wrong buyer pool.");
            Debug.Log("HPR_POOL_CHOICE_PASS: zero, one, multiple, stale preview, explicit choice, saved reload; shield 100, spell 80");
        }
    }
}
