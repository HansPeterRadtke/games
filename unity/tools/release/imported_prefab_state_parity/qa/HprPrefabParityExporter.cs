#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEngine;

// PRIVATE native author export, never included in buyer archives.
public static class HprPrefabParityExporter
{
    public static void Run()
    {
        string output=Environment.GetEnvironmentVariable("HPR_PREFAB_PACKAGE_OUT")??"";
        const string safe="/data/var/marketplace-account-setup/unity-prefab-dependency-20261123-wave61/";
        if(!Application.isBatchMode || !Path.IsPathRooted(output) ||
            !output.StartsWith(safe,StringComparison.Ordinal) || File.Exists(output) ||
            !AssetDatabase.IsValidFolder("Assets/HPRImportedPrefabParity"))
            throw new InvalidOperationException("HPR_PREFAB_ORIGINAL_EXPORT_PRECONDITION_FAILURE");
        AssetDatabase.ExportPackage(new[]{"Assets/HPRImportedPrefabParity"},output,ExportPackageOptions.Recurse);
        if(!File.Exists(output) || new FileInfo(output).Length<100)
            throw new InvalidOperationException("HPR_PREFAB_ORIGINAL_EXPORT_MISSING");
        Debug.Log("HPR_PREFAB_PARITY_ORIGINAL_PACKAGE_EXPORT_PASS "+new FileInfo(output).Length);
    }
}
#endif
