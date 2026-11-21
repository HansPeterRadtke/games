#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEngine;
// Private QA exporter; no customer package exposure. Exports one first-party
// path-moved, GUID-preserved text asset for coexistence collision acceptance.
public static class HprCoexistenceMovedRealExporter
{
    public static void Run()
    {
        const string basePath = "/data/var/marketplace-account-setup/unity-20261121-wave52/real-moved-guid-fixture/";
        string target = Environment.GetEnvironmentVariable("HPR_COEXISTENCE_MOVED_EXPORT");
        if (!Application.isBatchMode || string.IsNullOrEmpty(target) ||
            !target.StartsWith(basePath, StringComparison.Ordinal) ||
            !Path.IsPathRooted(target) || !target.EndsWith(".unitypackage", StringComparison.Ordinal) ||
            File.Exists(target) || !AssetDatabase.IsValidFolder("Assets/HPRUpgradeExample"))
            throw new InvalidOperationException("Use a genuinely fresh first-party moved-path QA archive.");
        string oldPath = "Assets/HPRUpgradeExample/Example.txt";
        string newPath = "Assets/HPRUpgradeExample/ExampleMoved.txt";
        if (AssetDatabase.LoadMainAssetAtPath(oldPath)!=null ||
            AssetDatabase.LoadMainAssetAtPath(newPath)==null ||
            AssetDatabase.LoadMainAssetAtPath("Assets/HPRUpgradeExample/README.md")==null ||
            string.IsNullOrEmpty(AssetDatabase.AssetPathToGUID(newPath)))
            throw new InvalidOperationException("Actual Unity moved-path fixture not imported correctly.");
        AssetDatabase.ExportPackage("Assets/HPRUpgradeExample", target, ExportPackageOptions.Recurse);
        if (!File.Exists(target) || new FileInfo(target).Length < 350)
            throw new IOException("Unity did not create the original moved-path .unitypackage");
        Debug.Log("HPR_REAL_MOVED_GUID_EXPORTED "+AssetDatabase.AssetPathToGUID(newPath));
    }
}
#endif
