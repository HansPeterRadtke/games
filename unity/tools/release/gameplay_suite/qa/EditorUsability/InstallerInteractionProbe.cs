// Private native rendered-Editor QA. Never ship with the buyer archive.
#if UNITY_EDITOR && ENABLE_INPUT_SYSTEM
using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Security.Cryptography;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEditor.UIElements;
using UnityEngine;
using UnityEngine.UIElements;
using HPR;
using HPR.GameplaySuite.Experimental;
using ExistingGameWorkflow;

namespace PrivateEditorUsability
{
    public static class InstallerInteractionProbe
    {
        [Serializable] private sealed class TextBounds
        {
            public string text, whiteSpace;
            public float x, y, width, height, measuredWidth, measuredHeight;
        }
        [Serializable] private sealed class UiState
        {
            public string stage, status, sceneHash, graphics;
            public bool attachEnabled, removeEnabled, runnerPresent, sceneDirty;
            public float windowX, windowY, windowWidth, windowHeight;
            public float buttonX, buttonY, buttonWidth, buttonHeight;
            public TextBounds[] texts;
        }
        private static string root, scenePath, savedHash;
        private static double started, lastState;
        private static int phase;
        private static GameObject player;
        private static HprSelectedAbilityInstaller window;
        private static AbilityData owned;
        private static HprExistingVitalsAdapter provider;
        private static Button attach, remove;
        private static readonly List<string> checks = new List<string>();
        private static string Hash(string path)
        {
            using (var hash = SHA256.Create()) return Convert.ToBase64String(hash.ComputeHash(File.ReadAllBytes(path)));
        }
        private static void Require(bool value, string name)
        {
            if (!value) throw new InvalidOperationException("FAILED: " + name);
            checks.Add(name);
        }
        public static void Run()
        {
            root = Environment.GetEnvironmentVariable("HPR_EDITOR_UI_OUTPUT");
            if (!Directory.Exists(root) || File.Exists(Path.Combine(root, "ui-state.json")))
                throw new InvalidOperationException("Unused private UI receipt folder required");
            started = EditorApplication.timeSinceStartup;
            phase = 0;
            EditorApplication.update += Tick;
        }
        private static void Setup()
        {
            string folder = "Assets/InstallerUiProbe_" + DateTime.UtcNow.Ticks;
            Require(!string.IsNullOrEmpty(AssetDatabase.CreateFolder("Assets", Path.GetFileName(folder))), "new_private_asset_folder");
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            player = new GameObject("Existing customer player");
            var vitals = player.AddComponent<ExistingGameVitals>();
            player.AddComponent<ExistingHealInput>();
            player.AddComponent<ExistingHealthDisplay>().Configure(vitals);
            provider = player.AddComponent<HprExistingVitalsAdapter>();
            provider.Configure(vitals);
            var effect = ScriptableObject.CreateInstance<AbilityEffectData>();
            effect.Id = "ui_owned_heal"; effect.EffectType = AbilityEffectType.Heal; effect.Value = 20;
            AssetDatabase.CreateAsset(effect, folder + "/OwnedHealEffect.asset");
            owned = ScriptableObject.CreateInstance<AbilityData>();
            owned.Id = "ui_owned_ability"; owned.Cost = 20; owned.Cooldown = 30; owned.Effects.Add(effect);
            AssetDatabase.CreateAsset(owned, folder + "/OwnedHealAbility.asset");
            scenePath = folder + "/OriginalExistingPlayer.unity";
            Require(EditorSceneManager.SaveScene(scene, scenePath), "initial_customer_scene_saved");
            savedHash = Hash(scenePath);
            Selection.activeGameObject = player;
            HprSelectedAbilityInstaller.Open();
            window = Resources.FindObjectsOfTypeAll<HprSelectedAbilityInstaller>().First();
            window.position = new Rect(60, 80, 370, 410);
            window.Focus(); window.Repaint();
            phase = 1;
        }
        private static void WriteState(string stage)
        {
            var help = window.rootVisualElement.Q<HelpBox>();
            var bounds = attach.worldBound;
            if (bounds.width <= 1 || bounds.height <= 1) return;
            var textBounds = window.rootVisualElement.Query<TextElement>().ToList().Where(x => !string.IsNullOrEmpty(x.text)).Select(x =>
            {
                Vector2 measure = x.MeasureTextSize(x.text, x.contentRect.width, x.resolvedStyle.whiteSpace == WhiteSpace.NoWrap ? VisualElement.MeasureMode.Undefined : VisualElement.MeasureMode.AtMost,
                    0, VisualElement.MeasureMode.Undefined);
                return new TextBounds { text = x.text, whiteSpace = x.resolvedStyle.whiteSpace.ToString(),
                    x = x.worldBound.x, y = x.worldBound.y, width = x.contentRect.width, height = x.contentRect.height,
                    measuredWidth = measure.x, measuredHeight = measure.y };
            }).ToArray();
            var state = new UiState { stage = stage, status = help == null ? "" : help.text,
                sceneHash = Hash(scenePath), graphics = SystemInfo.graphicsDeviceName,
                attachEnabled = attach.enabledInHierarchy, removeEnabled = remove.enabledInHierarchy,
                runnerPresent = player.GetComponent<AbilityRunnerComponent>() != null,
                sceneDirty = player.scene.isDirty, windowX = window.position.x, windowY = window.position.y,
                windowWidth = window.position.width, windowHeight = window.position.height,
                buttonX = bounds.x, buttonY = bounds.y, buttonWidth = bounds.width, buttonHeight = bounds.height,
                texts = textBounds };
            string temp = Path.Combine(root, "ui-state.tmp");
            File.WriteAllText(temp, JsonUtility.ToJson(state, true));
            string dest = Path.Combine(root, "ui-state.json");
            if (File.Exists(dest)) File.Delete(dest);
            File.Move(temp, dest);
            lastState = EditorApplication.timeSinceStartup;
        }
        private static void VerifyBinding()
        {
            var runner = player.GetComponent<AbilityRunnerComponent>();
            Require(runner != null, "runner_exists_after_ui_input");
            var serialized = new SerializedObject(runner);
            var abilities = serialized.FindProperty("configuredAbilities");
            Require(abilities.arraySize == 1 && abilities.GetArrayElementAtIndex(0).objectReferenceValue == owned,
                "actual_runner_references_customer_ability");
            Require(serialized.FindProperty("resourcePoolBehaviour").objectReferenceValue == provider,
                "actual_runner_references_existing_vitals_adapter");
            Require(serialized.FindProperty("effectOrigin").objectReferenceValue == player.transform,
                "actual_runner_origin_is_selected_actor");
        }
        private static void Tick()
        {
            try
            {
                if (phase == 0)
                {
                    if (EditorApplication.timeSinceStartup - started < 20 || EditorApplication.isCompiling || EditorApplication.isUpdating) return;
                    Setup(); return;
                }
                if (phase == 1)
                {
                    var fields = window.rootVisualElement.Query<ObjectField>().ToList();
                    if (fields.Count != 3) return;
                    attach = window.rootVisualElement.Query<Button>().ToList().First(x => x.text.StartsWith("Attach ability"));
                    remove = window.rootVisualElement.Query<Button>().ToList().First(x => x.text.StartsWith("Remove HPR runner"));
                    Require(!attach.enabledInHierarchy && player.GetComponent<AbilityRunnerComponent>() == null,
                        "initial_preview_is_read_only_and_blocked");
                    fields.Single(x => x.label == "Customer-owned ability").value = owned;
                    Require(attach.enabledInHierarchy, "owned_ability_enables_actual_ui_attach");
                    phase = 2; lastState = 0;
                }
                string command = Path.Combine(root, "command.txt");
                if (File.Exists(command))
                {
                    string text = File.ReadAllText(command).Trim(); File.Delete(command);
                    if (text == "wide") window.position = new Rect(60, 80, 640, 410);
                    if (text == "narrow") window.position = new Rect(60, 80, 370, 410);
                    if (text == "finish" && phase == 5)
                    {
                        Require(Hash(scenePath) == savedHash, "ui_attach_undo_redo_never_saved_scene");
                        Require(player.GetComponent<ExistingGameVitals>().Health == 40 && player.GetComponent<ExistingGameVitals>().Stamina == 100,
                            "ui_actions_preserved_authoritative_player_state");
                        File.WriteAllLines(Path.Combine(root, "native-result.txt"), checks);
                        window.Close(); EditorApplication.update -= Tick;
                        EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
                        EditorApplication.Exit(0); return;
                    }
                }
                var current = player.GetComponent<AbilityRunnerComponent>();
                if (phase == 2 && current != null)
                {
                    VerifyBinding(); Require(player.scene.isDirty, "attach_marks_only_open_scene_dirty");
                    Require(Hash(scenePath) == savedHash, "attach_does_not_save_scene");
                    phase = 3; lastState = 0;
                }
                else if (phase == 3 && current == null)
                {
                    Require(Hash(scenePath) == savedHash, "actual_editor_undo_restores_no_runner_without_saving");
                    phase = 4; lastState = 0;
                }
                else if (phase == 4 && current != null)
                {
                    VerifyBinding(); Require(Hash(scenePath) == savedHash, "actual_editor_redo_restores_binding_without_saving");
                    phase = 5; lastState = 0;
                }
                if (EditorApplication.timeSinceStartup - lastState > 2)
                    WriteState(phase == 2 ? "ready-for-attach" : phase == 3 ? "attached-await-undo" : phase == 4 ? "undone-await-redo" : "redone-await-finish");
                window.Repaint();
            }
            catch (Exception error)
            {
                File.WriteAllText(Path.Combine(root, "native-failure.txt"), string.Join("\n", checks) + "\n" + error);
                Debug.LogException(error); EditorApplication.update -= Tick;
                if (window != null) window.Close();
                EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
                EditorApplication.Exit(3);
            }
        }
    }
}
#endif
