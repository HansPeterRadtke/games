// Private fresh-process save/ability test. Never included in the buyer archive.
#if UNITY_EDITOR && ENABLE_INPUT_SYSTEM
using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Security.Cryptography;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.LowLevel;
using HPR;
using ExistingGameWorkflow;

public static class HprColdRestartValidator
{
    [Serializable] private sealed class ProcessObservation
    {
        public int processId;
        public string editorVersion, scene, sourceSaveHash;
        public float restoredCooldownSeconds, elapsedGameSeconds;
        public bool actualFreshEditorProcess, physicalInputTested;
    }
    private static double startup;
    private static string root, scenePath, savePath, sceneHash, saveHash;
    private static int phase, frames;
    private static float restoredAt, restoredRemaining;
    private static Keyboard keyboard;
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
    public static void RunAfterStartup()
    {
        startup = EditorApplication.timeSinceStartup;
        EditorApplication.update += StartWhenIdle;
    }
    private static void StartWhenIdle()
    {
        if (EditorApplication.timeSinceStartup - startup < 20 || EditorApplication.isCompiling || EditorApplication.isUpdating) return;
        EditorApplication.update -= StartWhenIdle;
        try
        {
            root = Environment.GetEnvironmentVariable("HPR_WORKFLOW_RECEIPT_ROOT");
            scenePath = Environment.GetEnvironmentVariable("HPR_WORKFLOW_COLD_SCENE");
            savePath = Environment.GetEnvironmentVariable("HPR_WORKFLOW_COLD_SAVE");
            if (!Directory.Exists(root) || !File.Exists(savePath) || !File.Exists(scenePath) ||
                EditorApplication.isPlayingOrWillChangePlaymode || !EditorSettings.enterPlayModeOptionsEnabled ||
                (EditorSettings.enterPlayModeOptions & EnterPlayModeOptions.DisableDomainReload) == 0)
                throw new InvalidOperationException("Unused, reload-disabled fresh-process test required");
            checks.Clear(); sceneHash = Hash(scenePath); saveHash = Hash(savePath);
            EditorSceneManager.OpenScene(scenePath, OpenSceneMode.Single);
            var actor = GameObject.Find("OriginalCustomerPlayer");
            Require(actor != null && actor.GetComponent<AbilityRunnerComponent>() != null &&
                actor.GetComponent<HprExistingInputBinding>() != null && actor.GetComponent<HprExistingVitalsAdapter>() != null,
                "cold_scene_reopened_with_original_player_and_bindings");
            phase = 1; frames = 0;
            EditorApplication.update += Tick;
            EditorApplication.isPlaying = true;
        }
        catch (Exception error) { Fail(error); }
    }
    private static void Press()
    {
        InputSystem.QueueStateEvent(keyboard, new KeyboardState()); InputSystem.Update();
        InputSystem.QueueStateEvent(keyboard, new KeyboardState(Key.H)); InputSystem.Update();
        InputSystem.QueueStateEvent(keyboard, new KeyboardState()); InputSystem.Update();
    }
    private static void Tick()
    {
        try
        {
            if (phase == 1)
            {
                if (!EditorApplication.isPlaying || ++frames < 30) return;
                var actor = GameObject.Find("OriginalCustomerPlayer");
                var vitals = actor.GetComponent<ExistingGameVitals>();
                var display = actor.GetComponent<ExistingHealthDisplay>();
                var input = actor.GetComponent<ExistingHealInput>();
                var binding = actor.GetComponent<HprExistingInputBinding>();
                var runner = actor.GetComponent<AbilityRunnerComponent>();
                Require(vitals.Health == 40 && vitals.Stamina == 100 && binding.RequestCount == 0 &&
                    binding.SuccessCount == 0 && input.ActionEnabled,
                    "cold_process_starts_from_serialized_baseline");
                string extension = ExistingGameSave.Load(savePath, vitals);
                var snapshot = JsonUtility.FromJson<AbilityRuntimeSnapshot>(extension);
                if (!runner.TryValidateSnapshot(snapshot, out string error)) throw new InvalidDataException(error);
                restoredRemaining = snapshot.Cooldowns.Single(x => x.AbilityId == "customer_heal").Remaining;
                if (restoredRemaining < 1 || restoredRemaining > 35) throw new InvalidDataException("Expected active bounded fixture cooldown");
                runner.RestoreSnapshot(snapshot); restoredAt = Time.time;
                Require(vitals.Health == 60 && vitals.Stamina == 80,
                    "saved_customer_state_restored_after_process_restart");
                Require(display.DisplayedHealth == 60, "existing_hud_tracks_cold_restored_health");
                float currentRemaining = runner.CaptureSnapshot().Cooldowns.Single(x => x.AbilityId == "customer_heal").Remaining;
                Require(currentRemaining > restoredRemaining - 1 && currentRemaining <= restoredRemaining + 0.01f,
                    "restored_cooldown_remains_relative_to_new_game_clock");
                Application.runInBackground = true;
                InputSystem.settings.backgroundBehavior = InputSettings.BackgroundBehavior.IgnoreFocus;
                InputSystem.settings.editorInputBehaviorInPlayMode = InputSettings.EditorInputBehaviorInPlayMode.AllDeviceInputAlwaysGoesToGameView;
                InputSystem.settings.updateMode = InputSettings.UpdateMode.ProcessEventsManually;
                keyboard = InputSystem.AddDevice<Keyboard>();
                int before = input.PerformedCount; Press();
                Require(input.PerformedCount == before + 1 && binding.RequestCount == 1 && binding.SuccessCount == 0,
                    "queued_existing_input_reaches_restored_runner_once");
                Require(vitals.Health == 60 && vitals.Stamina == 80,
                    "restored_cooldown_rejects_without_charging");
                var invalid = new AbilityRuntimeSnapshot();
                invalid.UnlockedIds.Add("customer_heal");
                invalid.Cooldowns.Add(new AbilityCooldownSnapshot { AbilityId = "customer_heal", Remaining = float.NaN });
                bool rejected = !runner.TryValidateSnapshot(invalid, out string reason) && !string.IsNullOrWhiteSpace(reason);
                bool threw = false;
                try { runner.RestoreSnapshot(invalid); } catch (ArgumentException) { threw = true; }
                Require(rejected && threw && vitals.Health == 60 && vitals.Stamina == 80 &&
                    runner.CaptureSnapshot().Cooldowns.Single(x => x.AbilityId == "customer_heal").Remaining > restoredRemaining - 1,
                    "invalid_snapshot_preserves_customer_state_and_cooldown");
                Require(Hash(savePath) == saveHash && Hash(scenePath) == sceneHash,
                    "source_save_and_scene_unchanged_before_cooldown_wait");
                phase = 2;
            }
            else if (phase == 2)
            {
                if (Time.time - restoredAt < restoredRemaining + 0.2f) return;
                var actor = GameObject.Find("OriginalCustomerPlayer");
                var runner = actor.GetComponent<AbilityRunnerComponent>();
                var input = actor.GetComponent<ExistingHealInput>();
                var binding = actor.GetComponent<HprExistingInputBinding>();
                var vitals = actor.GetComponent<ExistingGameVitals>();
                Require(runner.CaptureSnapshot().Cooldowns.All(x => x.AbilityId != "customer_heal"),
                    "saved_cooldown_naturally_expires_on_new_process_clock");
                int before = input.PerformedCount; Press();
                Require(input.PerformedCount == before + 1 && binding.RequestCount == 2 && binding.SuccessCount == 1,
                    "existing_input_activates_after_cold_restore_expiry");
                Require(vitals.Health == 80 && vitals.Stamina == 60 && actor.GetComponent<ExistingHealthDisplay>().DisplayedHealth == 80,
                    "authoritative_vitals_and_hud_update_after_expiry");
                var observation = new ProcessObservation { processId = System.Diagnostics.Process.GetCurrentProcess().Id,
                    editorVersion = Application.unityVersion, scene = scenePath, sourceSaveHash = saveHash,
                    restoredCooldownSeconds = restoredRemaining, elapsedGameSeconds = Time.time - restoredAt,
                    actualFreshEditorProcess = true, physicalInputTested = false };
                File.WriteAllText(Path.Combine(root, "cold-process-observation.json"), JsonUtility.ToJson(observation, true));
                Require(observation.processId > 0, "fresh_process_observation_recorded");
                InputSystem.RemoveDevice(keyboard); keyboard = null;
                phase = 3; EditorApplication.isPlaying = false;
            }
            else if (phase == 3 && !EditorApplication.isPlayingOrWillChangePlaymode)
            {
                Require(Hash(savePath) == saveHash, "source_save_unchanged_after_cold_play");
                Require(Hash(scenePath) == sceneHash, "integrated_scene_unchanged_after_cold_play");
                File.WriteAllLines(Path.Combine(root, "native-cold-result.txt"), checks.ConvertAll(x => x + "=PASS"));
                EditorApplication.update -= Tick; EditorApplication.Exit(0);
            }
        }
        catch (Exception error) { Fail(error); }
    }
    private static void Fail(Exception error)
    {
        if (keyboard != null) { InputSystem.RemoveDevice(keyboard); keyboard = null; }
        if (Directory.Exists(root)) File.WriteAllText(Path.Combine(root, "native-cold-failure.txt"), string.Join("\n", checks) + "\n" + error);
        Debug.LogException(error); EditorApplication.update -= Tick; EditorApplication.Exit(3);
    }
}
#endif
