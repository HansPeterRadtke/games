// Private, disposable Unity 6.6 package-free Play mode diagnostic.
// Investigates Editor SearchDatabase exception without installing HPR source.
#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

[InitializeOnLoad]
public static class HprPackageFreeSearchIndexerProbe
{
    private const string Session = "HPR_PACKAGE_FREE_EDITOR_PLAY_QA_20261101";
    private static int frames;
    private static bool registered;

    static HprPackageFreeSearchIndexerProbe()
    {
        if (SessionState.GetInt(Session, 0) > 0)
            Subscribe();
    }

    public static void Run()
    {
        string receipt = Environment.GetEnvironmentVariable("HPR_PACKAGE_FREE_PLAY_RECEIPT");
        if (string.IsNullOrWhiteSpace(receipt) || File.Exists(receipt))
            throw new InvalidOperationException("An unused private diagnostic receipt is required.");
        if (AssetDatabase.IsValidFolder("Assets/HPRGameplaySuite") ||
            Directory.Exists(Path.Combine(Application.dataPath, "HPRGameplaySuite")))
            throw new InvalidOperationException("Not a package-free project: HPR assets remain.");
        var scene = EditorSceneManager.OpenScene(
            "Assets/ExternalCustomerGame/Scenes/OriginalCustomerScene.unity",
            OpenSceneMode.Single);
        if (GameObject.Find("ExistingCustomerPlayer") == null)
            throw new InvalidOperationException("Original customer scene is invalid.");
        if (EditorApplication.isPlayingOrWillChangePlaymode ||
            SessionState.GetInt(Session, 0) != 0)
            throw new InvalidOperationException("Existing Play mode or previous QA run.");
        SessionState.SetInt(Session, 1);
        frames = 0;
        Subscribe();
        EditorApplication.isPlaying = true;
        Debug.Log("HPR_PACKAGE_FREE_SEARCH_QA_PLAY_ENTER_REQUESTED");
    }

    private static void Subscribe()
    {
        if (registered) return;
        registered = true;
        EditorApplication.update += OnUpdate;
    }

    private static void OnUpdate()
    {
        int phase = SessionState.GetInt(Session, 0);
        if (phase == 0) return;
        try
        {
            if (phase == 1)
            {
                if (!EditorApplication.isPlaying || ++frames < 40) return;
                if (GameObject.Find("ExistingCustomerPlayer") == null)
                    throw new InvalidOperationException("Package-free customer scene vanished.");
                File.WriteAllText(
                    Environment.GetEnvironmentVariable("HPR_PACKAGE_FREE_PLAY_RECEIPT"),
                    "vendor_root_absent=PASS\n" +
                    "unrelated_customer_scene_valid=PASS\n" +
                    "real_unity_editor_play_mode=PASS\n");
                Debug.Log("HPR_PACKAGE_FREE_EDITOR_PLAY_PASS");
                SessionState.SetInt(Session, 2);
                EditorApplication.isPlaying = false;
            }
            else if (phase == 2 && !EditorApplication.isPlayingOrWillChangePlaymode)
            {
                SessionState.SetInt(Session, 0);
                EditorApplication.update -= OnUpdate;
                registered = false;
                EditorApplication.delayCall += () => EditorApplication.Exit(0);
            }
        }
        catch (Exception problem)
        {
            Debug.LogException(problem);
            SessionState.SetInt(Session, 0);
            EditorApplication.update -= OnUpdate;
            registered = false;
            EditorApplication.Exit(3);
        }
    }
}
#endif
