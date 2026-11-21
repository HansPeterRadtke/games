#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEngine;

// PRIVATE release exporter, never included in buyer .unitypackage.
public static class HprPackageBoundaryExporter
{
    public static void Run()
    {
        string output = Environment.GetEnvironmentVariable("HPR_BOUNDARY_RELEASE_OUT");
        if (!Application.isBatchMode || string.IsNullOrWhiteSpace(output) ||
            !Path.IsPathRooted(output) || File.Exists(output) || Directory.Exists(output) ||
            !output.StartsWith("/data/var/marketplace-account-setup/unity-20261121-afternoon/", StringComparison.Ordinal) ||
            !output.EndsWith(".unitypackage", StringComparison.Ordinal))
            throw new InvalidOperationException("Export requires a NEW protected release .unitypackage file");
        if (!AssetDatabase.IsValidFolder("Assets/HPRPackageBoundary"))
            throw new InvalidOperationException("Missing authored buyer package folder");
        AssetDatabase.ExportPackage("Assets/HPRPackageBoundary", output, ExportPackageOptions.Recurse);
        if (!File.Exists(output) || new FileInfo(output).Length < 4000)
            throw new InvalidOperationException("No nontrivial release archive created");
        Debug.Log("HPR_BOUNDARY_RELEASE_EXPORT_PASS " + new FileInfo(output).Length + " bytes");
    }
}
#endif
