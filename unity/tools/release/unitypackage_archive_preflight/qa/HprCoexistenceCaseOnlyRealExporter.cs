#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
// Private QA only: original Unity package with a case-only path difference
// and a distinct meta GUID, exposing a false negative in case-sensitive scans.
public static class HprCoexistenceCaseOnlyRealExporter
{
    public static void Run()
    {
        const string ownerRoot = "/data/var/marketplace-account-setup/unity-20261121-wave52/real-case-only-path-fixture/";
        string target=Environment.GetEnvironmentVariable("HPR_COEXISTENCE_CASE_EXPORT") ?? "";
        if (!Application.isBatchMode || !Path.IsPathRooted(target) ||
            !target.StartsWith(ownerRoot,StringComparison.Ordinal) ||
            !target.EndsWith(".unitypackage",StringComparison.Ordinal) ||
            File.Exists(target) || !AssetDatabase.IsValidFolder("Assets/HPRUpgradeExample"))
            throw new InvalidOperationException("Fresh original case-only Unity source and destination required.");
        string root=Path.Combine(Directory.GetParent(Application.dataPath).FullName,"Assets/HPRUpgradeExample");
        string[] raw=Directory.GetFiles(root,"*",SearchOption.TopDirectoryOnly)
            .Where(path=>!path.EndsWith(".meta",StringComparison.OrdinalIgnoreCase)).Select(Path.GetFileName).ToArray();
        if (raw.Length!=2 || !raw.Contains("example.TXT",StringComparer.Ordinal) ||
            !raw.Contains("README.md",StringComparer.Ordinal) ||
            AssetDatabase.LoadMainAssetAtPath("Assets/HPRUpgradeExample/example.TXT")==null)
            throw new InvalidOperationException("Actual Unity source must contain only original renamed-case file and README.");
        AssetDatabase.ExportPackage("Assets/HPRUpgradeExample",target,ExportPackageOptions.Recurse);
        if (!File.Exists(target) || new FileInfo(target).Length<300)
            throw new IOException("Unity failed to export case-only source fixture.");
        Debug.Log("HPR_REAL_CASE_ONLY_PATH_EXPORTED "+
            AssetDatabase.AssetPathToGUID("Assets/HPRUpgradeExample/example.TXT"));
    }
}
#endif
