// Private Unity test-only Editor player builder. No customer or marketplace state.
#if UNITY_EDITOR && ENABLE_INPUT_SYSTEM
using System;
using System.IO;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

public static class HprSuiteNewInputStandaloneBuilder
{
    public static void Build()
    {
        const string scenePath = "Assets/HprInputQA/HprInputStandaloneScene.unity";
        string output = Environment.GetEnvironmentVariable("HPR_INPUT_STANDALONE_EXE");
        if (string.IsNullOrWhiteSpace(output) || !Path.IsPathRooted(output) ||
            !output.StartsWith("/data/var/marketplace-account-setup/", StringComparison.Ordinal) ||
            File.Exists(output))
            throw new InvalidOperationException("Need fresh, approved private Linux player output path");
        if (AssetDatabase.LoadAssetAtPath<SceneAsset>(scenePath) != null)
            throw new InvalidOperationException("Refusing to regenerate an existing QA scene");

        Directory.CreateDirectory("Assets/HprInputQA");
        Directory.CreateDirectory(Path.GetDirectoryName(output));
        Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        new GameObject("Disposable HPR New Input Real Player Probe")
            .AddComponent<HprSuiteInputGameplayProbe>();
        if (!EditorSceneManager.SaveScene(scene, scenePath))
            throw new InvalidOperationException("Could not save a private input QA test scene");
        var options = new BuildPlayerOptions
        {
            scenes = new[] { scenePath },
            locationPathName = output,
            target = BuildTarget.StandaloneLinux64,
            options = BuildOptions.None
        };
        BuildReport result = BuildPipeline.BuildPlayer(options);
        if (result.summary.result != BuildResult.Succeeded ||
            !File.Exists(output))
            throw new InvalidOperationException("Standalone input player build failed: " +
                result.summary.result + " / " + result.summary.totalErrors);
        Debug.Log("HPR_NEW_INPUT_LINUX_STANDALONE_BUILD_PASS output=" + output);
    }
}
#else
#if UNITY_EDITOR
public static class HprSuiteNewInputStandaloneBuilder
{
    public static void Build() { throw new System.InvalidOperationException(
        "Input System compile path is disabled"); }
}
#endif
#endif
