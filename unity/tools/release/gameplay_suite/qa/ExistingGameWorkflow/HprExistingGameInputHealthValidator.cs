// Private native Unity QA. Never included in the buyer archive.
#if UNITY_EDITOR && ENABLE_INPUT_SYSTEM
using System;
using System.IO;
using System.Collections.Generic;
using System.Security.Cryptography;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.LowLevel;
using HPR;
using HPR.GameplaySuite.Experimental;
using ExistingGameWorkflow;
using HprCustomerIntegrationQa;

[InitializeOnLoad]
public static class HprExistingGameInputHealthValidator
{
    private const string StateKey = "HPR_EXISTING_INPUT_HEALTH_WAVE1";
    private static int frames;
    private static Keyboard keyboard;
    private static readonly List<string> checks = new List<string>();
    private static string root;
    private static string scenario;
    private static string baselineScene;
    private static string baselineHash;
    private static int inputBeforeDetach;
    private static bool subscribed;
    static HprExistingGameInputHealthValidator()
    {
        if (SessionState.GetInt(StateKey, 0) != 0)
        {
            string savedChecks = SessionState.GetString(StateKey + "checks", "");
            if (!string.IsNullOrEmpty(savedChecks)) checks.AddRange(savedChecks.Split('\n'));
            Subscribe();
        }
    }
    private static string Hash(string path)
    {
        using (var hash = SHA256.Create()) return Convert.ToBase64String(hash.ComputeHash(File.ReadAllBytes(path)));
    }
    private static void Require(bool value, string name)
    {
        if (!value) throw new InvalidOperationException("FAILED: " + name);
        checks.Add(name); SessionState.SetString(StateKey + "checks", string.Join("\n", checks));
    }
    // Private batch QA option: let delayed Editor startup/indexing callbacks run
    // before scene authoring and Play. This is not a product/runtime workaround.
    private static double startupWaitBegan;
    public static void RunAfterStartup()
    {
        startupWaitBegan = EditorApplication.timeSinceStartup;
        EditorApplication.update += WaitForStartup;
    }
    private static void WaitForStartup()
    {
        if (EditorApplication.timeSinceStartup - startupWaitBegan < 20 ||
            EditorApplication.isCompiling || EditorApplication.isUpdating) return;
        EditorApplication.update -= WaitForStartup;
        Run();
    }
    public static void Run()
    {
        root = Environment.GetEnvironmentVariable("HPR_WORKFLOW_RECEIPT_ROOT");
        scenario = Environment.GetEnvironmentVariable("HPR_WORKFLOW_SCENARIO");
        if (!Directory.Exists(root) || File.Exists(Path.Combine(root, "native-result.txt")))
            throw new InvalidOperationException("Expected fresh private receipt root");
        if (scenario != "shadow" && scenario != "wired") throw new InvalidOperationException("Unknown scenario");
        if (EditorApplication.isPlayingOrWillChangePlaymode || SessionState.GetInt(StateKey, 0) != 0)
            throw new InvalidOperationException("Prior Play mode state exists");
        checks.Clear(); SessionState.SetString(StateKey + "checks", "");
        string folder = "Assets/WorkflowProbe_" + scenario + "_" + DateTime.UtcNow.Ticks;
        if (AssetDatabase.IsValidFolder(folder)) throw new InvalidOperationException("Refusing to replay scene generation");
        if (string.IsNullOrEmpty(AssetDatabase.CreateFolder("Assets", Path.GetFileName(folder))))
            throw new InvalidOperationException("Could not create unique private scene folder");
        baselineScene = folder + "/OriginalCustomerGame.unity";
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var player = new GameObject("OriginalCustomerPlayer");
        var vitals = player.AddComponent<ExistingGameVitals>();
        player.AddComponent<ExistingHealInput>();
        player.AddComponent<ExistingHealthDisplay>().Configure(vitals);
        Require(EditorSceneManager.SaveScene(scene, baselineScene), "independent_customer_scene_created");
        baselineHash = Hash(baselineScene);
        // Only a new scene copy is integrated; the baseline has no HPR components.
        string integrated = folder + "/WithOptionalHprAbility.unity";
        Require(EditorSceneManager.SaveScene(scene, integrated, true), "new_scene_copy_created");
        EditorSceneManager.OpenScene(integrated);
        player = GameObject.Find("OriginalCustomerPlayer");
        var effect = ScriptableObject.CreateInstance<AbilityEffectData>();
        effect.Id = "customer_heal_effect"; effect.EffectType = AbilityEffectType.Heal; effect.Value = 20;
        AssetDatabase.CreateAsset(effect, folder + "/OwnedHealEffect.asset");
        var ability = ScriptableObject.CreateInstance<AbilityData>();
        ability.Id = "customer_heal"; ability.Cost = 20; ability.Cooldown = 30; ability.Effects.Add(effect);
        AssetDatabase.CreateAsset(ability, folder + "/OwnedHealAbility.asset");
        MonoBehaviour resources;
        if (scenario == "shadow") resources = player.AddComponent<HprCustomerAbilityResourceBridge>();
        else
        {
            var adapter = player.AddComponent<HprExistingVitalsAdapter>();
            adapter.Configure(player.GetComponent<ExistingGameVitals>()); resources = adapter;
        }
        var runner = HprSelectedAbilityInstaller.AttachExplicitly(player, ability, resources);
        player.AddComponent<HprExistingInputBinding>().Configure(player.GetComponent<ExistingHealInput>(), runner, ability.Id);
        Require(EditorSceneManager.SaveScene(player.scene), "integration_scene_saved_explicitly");
        EditorSceneManager.OpenScene(integrated);
        player = GameObject.Find("OriginalCustomerPlayer");
        Require(player.GetComponent<HprExistingInputBinding>() != null && player.GetComponent<ExistingGameVitals>().Health == 40,
            "existing_health_and_bindings_survive_scene_reopen");
        Require(Hash(baselineScene) == baselineHash, "original_scene_bytes_unchanged_before_play");
        SessionState.SetString(StateKey + "root", root); SessionState.SetString(StateKey + "scenario", scenario);
        SessionState.SetString(StateKey + "scene", baselineScene); SessionState.SetString(StateKey + "hash", baselineHash);
        SessionState.SetInt(StateKey, 1); frames = 0; Subscribe(); EditorApplication.isPlaying = true;
    }
    private static void Subscribe()
    {
        if (subscribed) return; subscribed = true; EditorApplication.update += Step;
    }
    private static void Press()
    {
        InputSystem.QueueStateEvent(keyboard, new KeyboardState()); InputSystem.Update();
        InputSystem.QueueStateEvent(keyboard, new KeyboardState(Key.H)); InputSystem.Update();
        InputSystem.QueueStateEvent(keyboard, new KeyboardState()); InputSystem.Update();
    }
    private static void Step()
    {
        int phase = SessionState.GetInt(StateKey, 0); if (phase == 0) return;
        root = SessionState.GetString(StateKey + "root", ""); scenario = SessionState.GetString(StateKey + "scenario", "");
        baselineScene = SessionState.GetString(StateKey + "scene", ""); baselineHash = SessionState.GetString(StateKey + "hash", "");
        try
        {
            if (phase == 1)
            {
                if (!EditorApplication.isPlaying || ++frames < 30) return;
                var player = GameObject.Find("OriginalCustomerPlayer");
                var vitals = player.GetComponent<ExistingGameVitals>();
                var input = player.GetComponent<ExistingHealInput>();
                var binding = player.GetComponent<HprExistingInputBinding>();
                var runner = player.GetComponent<AbilityRunnerComponent>();
                var display = player.GetComponent<ExistingHealthDisplay>();
                Application.runInBackground = true;
                InputSystem.settings.backgroundBehavior = InputSettings.BackgroundBehavior.IgnoreFocus;
                InputSystem.settings.editorInputBehaviorInPlayMode = InputSettings.EditorInputBehaviorInPlayMode.AllDeviceInputAlwaysGoesToGameView;
                InputSystem.settings.updateMode = InputSettings.UpdateMode.ProcessEventsManually;
                keyboard = InputSystem.AddDevice<Keyboard>();
                int before = input.PerformedCount; Press();
                Debug.Log("WORKFLOW_INPUT_DIAGNOSTIC enabled=" + input.ActionEnabled + " active=" + input.isActiveAndEnabled + " inputBefore=" + before + " inputAfter=" + input.PerformedCount + " requests=" + binding.RequestCount + " successes=" + binding.SuccessCount);
                Require(input.PerformedCount == before + 1 && binding.RequestCount == 1, "queued_keyboard_event_reaches_existing_input_action_once");
                Require(binding.SuccessCount == 1, "input_callback_activates_packaged_runner");
                // This assertion MUST fail for the historical independent QA resource store.
                Require(vitals.Health == 60 && vitals.Stamina == 80, "authoritative_existing_health_and_stamina_changed");
                Require(display.DisplayedHealth == 60, "existing_hud_binding_observes_authoritative_health");
                Press();
                Require(binding.RequestCount == 2 && binding.SuccessCount == 1 && vitals.Health == 60 && vitals.Stamina == 80,
                    "cooldown_blocks_second_input_without_charging_again");
                binding.enabled = false; binding.enabled = true; binding.enabled = false; binding.enabled = true;
                int priorRequests = binding.RequestCount; Press();
                Require(binding.RequestCount == priorRequests + 1, "reenable_does_not_duplicate_input_subscription");
                var snapshot = runner.CaptureSnapshot();
                string save = Path.Combine(root, "customer-save.json");
                ExistingGameSave.SaveNew(save, vitals, JsonUtility.ToJson(snapshot));
                vitals.Restore(1, 1);
                string extension = ExistingGameSave.Load(save, vitals);
                runner.RestoreSnapshot(JsonUtility.FromJson<AbilityRuntimeSnapshot>(extension));
                Require(vitals.Health == 60 && vitals.Stamina == 80 && display.DisplayedHealth == 60,
                    "customer_save_disk_roundtrip_restores_existing_state");
                Require(!runner.TryActivate("customer_heal") && vitals.Stamina == 80,
                    "restored_extension_preserves_active_cooldown");
                // Detach this optional feature. Existing input remains enabled.
                binding.enabled = false;
                UnityEngine.Object.Destroy(binding); UnityEngine.Object.Destroy(runner);
                inputBeforeDetach = input.PerformedCount;
                SessionState.SetInt(StateKey, 2); frames = 0;
            }
            else if (phase == 2)
            {
                if (++frames < 8) return;
                var player = GameObject.Find("OriginalCustomerPlayer");
                var vitals = player.GetComponent<ExistingGameVitals>(); var input = player.GetComponent<ExistingHealInput>();
                Press();
                Require(input.PerformedCount == inputBeforeDetach + 1 && vitals.Health == 60 && vitals.Stamina == 80,
                    "detached_feature_keeps_existing_input_and_health_usable");
                Require(player.GetComponent<AbilityRunnerComponent>() == null && player.GetComponent<HprExistingInputBinding>() == null,
                    "only_optional_runner_and_input_binding_detached");
                InputSystem.RemoveDevice(keyboard); keyboard = null;
                SessionState.SetInt(StateKey, 3); EditorApplication.isPlaying = false;
            }
            else if (phase == 3 && !EditorApplication.isPlayingOrWillChangePlaymode)
            {
                Require(Hash(baselineScene) == baselineHash, "original_customer_scene_still_byte_identical_after_play");
                File.WriteAllLines(Path.Combine(root, "native-result.txt"), checks.ConvertAll(name => name + "=PASS"));
                Finish(0);
            }
        }
        catch (Exception error)
        {
            if (keyboard != null) { InputSystem.RemoveDevice(keyboard); keyboard = null; }
            File.WriteAllText(Path.Combine(root, "native-failure.txt"), string.Join("\n", checks) + "\n" + error);
            Debug.LogException(error); Finish(3);
        }
    }
    private static void Finish(int code)
    {
        SessionState.SetInt(StateKey, 0); EditorApplication.update -= Step; subscribed = false;
        EditorApplication.delayCall += () => EditorApplication.Exit(code);
    }
}
#endif
