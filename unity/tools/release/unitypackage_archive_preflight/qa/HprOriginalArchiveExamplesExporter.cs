#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEngine;

// Private author-only exporter, NOT included in any buyer archive.
public static class HprOriginalArchiveExamplesExporter
{
    public static void Run()
    {
        string dest=Environment.GetEnvironmentVariable("HPR_ORIGINAL_EXAMPLE_OUTPUT")??"";
        string ownPrefix="/data/var/marketplace-account-setup/unity-20261121-wave51/original-archive-sample-authoring/";
        if (!Application.isBatchMode || !Path.IsPathRooted(dest) ||
            !dest.StartsWith(ownPrefix,StringComparison.Ordinal) ||
            !dest.EndsWith(".unitypackage",StringComparison.OrdinalIgnoreCase) ||
            File.Exists(dest) || !AssetDatabase.IsValidFolder("Assets/HPRUpgradeExample"))
            throw new InvalidOperationException("First-party fresh demo project and new private archive destination required.");
        var fullRoot=Path.Combine(Directory.GetParent(Application.dataPath).FullName,
            "Assets/HPRUpgradeExample");
        string[] files=Directory.GetFiles(fullRoot,"*",SearchOption.TopDirectoryOnly);
        int originalAssets=0;
        foreach (string name in files)
        {
            if (name.EndsWith(".meta",StringComparison.Ordinal)) continue;
            string assetPath="Assets/HPRUpgradeExample/"+Path.GetFileName(name);
            if (Path.GetFileName(name)!="README.md" && Path.GetFileName(name)!="Example.txt" &&
                Path.GetFileName(name)!="ADDED_NOTICE.txt")
                throw new InvalidOperationException("Unexpected first-party training sample asset name: "+assetPath);
            if (AssetDatabase.LoadMainAssetAtPath(assetPath)==null)
                throw new InvalidOperationException("Sample source was not actually imported by Unity: "+assetPath);
            if (!File.Exists(name+".meta"))
                throw new InvalidOperationException("Sample metadata missing: "+assetPath);
            originalAssets++;
        }
        if (originalAssets<2 || originalAssets>3)
            throw new InvalidOperationException("Expected two or three real first-party example files.");
        AssetDatabase.ExportPackage("Assets/HPRUpgradeExample",dest,ExportPackageOptions.Recurse);
        if (!File.Exists(dest) || new FileInfo(dest).Length<280)
            throw new IOException("Unity failed to export training archive.");
        Debug.Log("HPR_FIRST_PARTY_TRAINING_EXAMPLE_EXPORTED "+new FileInfo(dest).Length);
    }
}
#endif
