#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEngine;

// PRIVATE fixed-scope export; never included in the buyer package.
public static class HprProjectPreflightExporter
{
    public static void Run()
    {
        string output = Environment.GetEnvironmentVariable("HPR_PREFLIGHT_BUNDLE_OUT");
        if (!Application.isBatchMode || string.IsNullOrWhiteSpace(output) ||
            !Path.IsPathRooted(output) || File.Exists(output) || Directory.Exists(output))
            throw new InvalidOperationException("Fresh absolute private bundle output required");
        string[] roots = { "Assets/HPRInputReadiness", "Assets/HPRAnimatorContract",
                           "Assets/HPRProjectPreflight" };
        foreach (string root in roots)
            if (!AssetDatabase.IsValidFolder(root))
                throw new InvalidOperationException("Expected original editor product missing: " + root);
        AssetDatabase.ExportPackage(roots, output, ExportPackageOptions.Recurse);
        if (!File.Exists(output) || new FileInfo(output).Length < 2000)
            throw new InvalidOperationException("Export did not produce the expected combined package");
        Debug.Log("HPR_PROJECT_PREFLIGHT_BUNDLE_EXPORTED " + new FileInfo(output).Length);
    }
}
#endif
