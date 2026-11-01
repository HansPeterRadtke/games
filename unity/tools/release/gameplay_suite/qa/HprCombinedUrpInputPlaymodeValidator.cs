// Private real-Unity acceptance: imported HPR arena in a project using both
// URP and new-input-only handling. Never distributed in any buyer archive.
#if UNITY_EDITOR && ENABLE_INPUT_SYSTEM
using System;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.SceneManagement;

[InitializeOnLoad]
public static class HprCombinedUrpInputPlaymodeValidator
{
    private const string StateKey = "HPR_COMBINED_URP_NEW_INPUT_20261101";
    private static bool subscribed;
    private static int frames;

    static HprCombinedUrpInputPlaymodeValidator()
    {
        if (SessionState.GetInt(StateKey, 0) > 0)
            Subscribe();
    }

    public static void Run()
    {
        string inputReceipt = RequireReceipt("HPR_NEW_INPUT_GAME_UPDATE_RECEIPT");
        string combinedReceipt = RequireReceipt("HPR_COMBINED_URP_INPUT_RECEIPT");
        if (File.Exists(inputReceipt) || File.Exists(inputReceipt + ".FAILED") ||
            File.Exists(combinedReceipt))
            throw new InvalidOperationException("Use fresh private input and combined receipts.");
        if (EditorApplication.isPlayingOrWillChangePlaymode ||
            SessionState.GetInt(StateKey, 0) != 0)
            throw new InvalidOperationException("A separate Unity Play mode process is already active.");

        if (!(GraphicsSettings.currentRenderPipeline is UniversalRenderPipelineAsset))
            throw new InvalidOperationException("Active customer project does not use actual URP.");

        Scene scene = EditorSceneManager.OpenScene(
            "Assets/HPRGameplaySuite/Demo/GameplaySuiteShowcase.unity", OpenSceneMode.Single);
        var camera = Camera.main;
        if (camera == null)
            throw new InvalidOperationException("Imported HPR buyer scene has no active camera.");
        var probeRoot = new GameObject("HPR disposable combined URP + New Input test");
        probeRoot.AddComponent<HprSuiteInputGameplayProbe>();
        // The game owner's scene/scene asset are not saved or exported.
        SessionState.SetInt(StateKey, 1);
        frames = 0;
        Subscribe();
        EditorApplication.isPlaying = true;
        Debug.Log("HPR_COMBINED_URP_NEW_INPUT_PLAY_ENTER_REQUESTED");
    }

    private static string RequireReceipt(string variable)
    {
        string value = Environment.GetEnvironmentVariable(variable);
        if (string.IsNullOrWhiteSpace(value))
            throw new InvalidOperationException("Missing private QA output environment: " + variable);
        return value;
    }

    private static void Subscribe()
    {
        if (subscribed)
            return;
        subscribed = true;
        EditorApplication.update += OnUpdate;
    }

    private static void OnUpdate()
    {
        int phase = SessionState.GetInt(StateKey, 0);
        if (phase == 0)
            return;
        try
        {
            if (phase == 1)
            {
                if (!EditorApplication.isPlaying)
                    return;
                if (++frames > 400)
                    throw new TimeoutException("Actual combined URP/input probe exceeded 400 Editor update frames.");
                string inputReceipt = RequireReceipt("HPR_NEW_INPUT_GAME_UPDATE_RECEIPT");
                if (File.Exists(inputReceipt + ".FAILED"))
                    throw new InvalidOperationException(
                        "Actual new input gameplay Update failed: " +
                        File.ReadAllText(inputReceipt + ".FAILED"));
                if (!File.Exists(inputReceipt))
                    return;
                string observed = File.ReadAllText(inputReceipt);
                if (!observed.Contains("new_input_only_real_game_update=PASS") ||
                    !observed.Contains("key_press_and_frame_transition=PASS") ||
                    !observed.Contains("keyboard_modifiers_and_numpad=PASS") ||
                    !observed.Contains("key_release=PASS"))
                    throw new InvalidOperationException("New Input System report is incomplete.");

                if (!(GraphicsSettings.currentRenderPipeline is UniversalRenderPipelineAsset))
                    throw new InvalidOperationException("URP pipeline vanished during gameplay.");
                if (Camera.main == null)
                    throw new InvalidOperationException("Imported arena camera vanished in Play mode.");

                File.WriteAllText(RequireReceipt("HPR_COMBINED_URP_INPUT_RECEIPT"),
                    "actual_unity_6000_6_editor_playmode=PASS\n" +
                    "active_urp_17_pipeline=PASS\n" +
                    "real_imported_buyer_arena_camera=PASS\n" +
                    "new_input_only_keyboard_down_up_and_modifiers=PASS\n" +
                    "no_buyer_scene_save_or_project_setting_changes_requested=PASS\n");
                Debug.Log("HPR_COMBINED_URP_NEW_INPUT_ACCEPTANCE_PASS");
                SessionState.SetInt(StateKey, 2);
                EditorApplication.isPlaying = false;
            }
            else if (phase == 2 && !EditorApplication.isPlayingOrWillChangePlaymode)
            {
                SessionState.SetInt(StateKey, 0);
                EditorApplication.update -= OnUpdate;
                subscribed = false;
                EditorApplication.delayCall += () => EditorApplication.Exit(0);
            }
        }
        catch (Exception error)
        {
            Debug.LogException(error);
            SessionState.SetInt(StateKey, 0);
            EditorApplication.update -= OnUpdate;
            subscribed = false;
            EditorApplication.Exit(3);
        }
    }
}
#endif
