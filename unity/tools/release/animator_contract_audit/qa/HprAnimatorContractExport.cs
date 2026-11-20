#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEngine;

public static class HprAnimatorContractExport
{
    public static void Run()
    {
        string destination = Environment.GetEnvironmentVariable("HPR_ANIM_PACKAGE_OUT");
        if (!Application.isBatchMode || string.IsNullOrWhiteSpace(destination) ||
            !Path.IsPathRooted(destination) || File.Exists(destination) || Directory.Exists(destination))
            throw new InvalidOperationException("Private fresh absolute package destination required");
        const string root = "Assets/HPRAnimatorContract";
        if (!AssetDatabase.IsValidFolder(root) ||
            !File.Exists(Path.Combine(Application.dataPath, "HPRAnimatorContract/Editor/HprAnimatorContractAudit.cs")))
            throw new InvalidOperationException("Original product root not installed");
        AssetDatabase.ExportPackage(root, destination, ExportPackageOptions.Recurse);
        if (!File.Exists(destination) || new FileInfo(destination).Length < 1000)
            throw new InvalidOperationException("Unity package missing or too small");
        Debug.Log("HPR_ANIMATOR_CONTRACT_EXPORTED " + new FileInfo(destination).Length);
    }
}
#endif
