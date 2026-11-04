// Private QA authoring in a disposable project, never a customer migration.
#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEngine;

public static class NativeBuildSettingsFixture
{
    [Serializable]
    private sealed class Receipt
    {
        public string engineVersion;
        public string scenePath;
        public string sceneGuid;
        public bool nativeSceneAssetLoaded;
        public int configuredScenes;
        public bool configuredEnabled;
    }
    public static void Run()
    {
        string root = Environment.GetEnvironmentVariable("HPR_SETTINGS_FIXTURE_OUTPUT");
        if (string.IsNullOrEmpty(root) || !Directory.Exists(root)) throw new InvalidOperationException("Private output required");
        string receipt = Path.Combine(root, "native-settings.json");
        if (File.Exists(receipt)) throw new InvalidOperationException("Do not replay a completed fixture");
        const string scene = "Assets/HPRGameplaySuite/Demo/GameplaySuiteShowcase.unity";
        if (AssetDatabase.LoadAssetAtPath<SceneAsset>(scene) == null) throw new InvalidOperationException("Actual imported scene required");
        string guid = AssetDatabase.AssetPathToGUID(scene);
        if (string.IsNullOrEmpty(guid)) throw new InvalidOperationException("Native scene GUID required");
        EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(scene, true) };
        var configured = EditorBuildSettings.scenes;
        if (configured.Length != 1 || configured[0].path != scene || !configured[0].enabled)
            throw new InvalidOperationException("Native build-scene selection did not persist in memory");
        File.WriteAllText(receipt, JsonUtility.ToJson(new Receipt
        {
            engineVersion = Application.unityVersion, scenePath = scene, sceneGuid = guid,
            nativeSceneAssetLoaded = true, configuredScenes = configured.Length, configuredEnabled = configured[0].enabled
        }, true));
    }
}
#endif
