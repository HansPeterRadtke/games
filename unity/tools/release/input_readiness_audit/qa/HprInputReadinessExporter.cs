#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEngine;

public static class HprInputReadinessExporter
{
    public static void Build()
    {
        string output = Environment.GetEnvironmentVariable("HPR_INPUT_PACKAGE_FILE");
        if (string.IsNullOrWhiteSpace(output) || !Path.IsPathRooted(output) ||
            File.Exists(output) || Directory.Exists(output))
            throw new InvalidOperationException("Fresh absolute output package required");
        const string root = "Assets/HPRInputReadiness";
        if (!AssetDatabase.IsValidFolder(root) ||
            !File.Exists(Path.Combine(Application.dataPath, "HPRInputReadiness/Editor/HprInputReadinessAudit.cs")))
            throw new InvalidOperationException("Product's original Editor source was not installed");
        AssetDatabase.ExportPackage(root, output, ExportPackageOptions.Recurse);
        if (!File.Exists(output) || new FileInfo(output).Length < 1024)
            throw new InvalidOperationException("Unity package export missing");
        Debug.Log("HPR_INPUT_READINESS_PACKAGE_EXPORTED " + new FileInfo(output).Length);
    }
}
#endif
