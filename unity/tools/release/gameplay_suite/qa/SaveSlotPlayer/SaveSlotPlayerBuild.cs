// Stage in Assets/Editor of a disposable project only.
using System;
using System.IO;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

public static class SaveSlotPlayerBuild
{
    public static void Run()
    {
        const string showcase = "Assets/HPRGameplaySuite/Demo/GameplaySuiteShowcase.unity";
        string target = Environment.GetEnvironmentVariable("HPR_SAVE_PLAYER_BINARY");
        if (string.IsNullOrEmpty(target) || !Path.IsPathRooted(target) ||
            File.Exists(target) || Directory.Exists(target))
            throw new InvalidOperationException("A new absolute Player output path is required");
        if (!AssetDatabase.LoadAssetAtPath<SceneAsset>(showcase))
            throw new InvalidOperationException("The imported showcase scene is missing");

        BuildReport report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
        {
            scenes = new[] { showcase },
            locationPathName = target,
            target = BuildTarget.StandaloneLinux64,
            options = BuildOptions.None
        });
        if (report.summary.result != BuildResult.Succeeded || !File.Exists(target))
            throw new InvalidOperationException($"Player build failed with {report.summary.totalErrors} errors");
        Debug.Log("HPR_SAVE_PLAYER_BUILD_PASS");
    }
}
