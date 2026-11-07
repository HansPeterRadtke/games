// Private create-only Linux Player build; never part of the buyer archive.
#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

public static class LegacyInputPlayerBuilder
{
    public static void Build()
    {
#if ENABLE_LEGACY_INPUT_MANAGER && !ENABLE_INPUT_SYSTEM
        string output = Environment.GetEnvironmentVariable("HPR_INPUT_STANDALONE_EXE");
        const string scenePath = "Assets/HprLegacyInputQA/LegacyInputSmoke.unity";
        if (string.IsNullOrWhiteSpace(output) || !Path.IsPathRooted(output) ||
            !output.StartsWith("/data/var/marketplace-account-setup/", StringComparison.Ordinal) ||
            File.Exists(output) || Directory.Exists("Assets/HprLegacyInputQA"))
            throw new InvalidOperationException("Fresh private legacy project and output required");
        Directory.CreateDirectory("Assets/HprLegacyInputQA");
        Directory.CreateDirectory(Path.GetDirectoryName(output));
        Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        new GameObject("Private legacy Player smoke").AddComponent<LegacyInputPlayerProbe>();
        if (!EditorSceneManager.SaveScene(scene, scenePath)) throw new InvalidOperationException("Could not save private scene");
        BuildReport report = BuildPipeline.BuildPlayer(new BuildPlayerOptions {
            scenes = new[] { scenePath }, locationPathName = output,
            target = BuildTarget.StandaloneLinux64, options = BuildOptions.None });
        if (report.summary.result != BuildResult.Succeeded || !File.Exists(output))
            throw new InvalidOperationException("Legacy Player build failed: " + report.summary.result);
        Debug.Log("HPR_LEGACY_LINUX_STANDALONE_BUILD_PASS");
#else
        throw new InvalidOperationException("Legacy-only compile path required");
#endif
    }
}
#endif
