#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEngine;
// Private QA exporter. Never shipped in a retail archive.
public static class HprFbxSourceTakeExporter
{
    public static void Run()
    {
        string target=Environment.GetEnvironmentVariable("HPR_SOURCE_TAKE_PACKAGE_OUT") ?? "";
        if (!Application.isBatchMode || !Path.IsPathRooted(target) ||
            !target.StartsWith("/data/var/marketplace-account-setup/unity-20261122-wave54/",StringComparison.Ordinal) ||
            !target.EndsWith(".unitypackage",StringComparison.Ordinal) || File.Exists(target))
            throw new InvalidOperationException("Fresh package export path required");
        const string source="Assets/HPRFbxSourceTakes";
        if(!AssetDatabase.IsValidFolder(source) ||
            AssetDatabase.LoadMainAssetAtPath(source+"/Samples/HPRTwoTakeCube.fbx")==null ||
            AssetDatabase.LoadMainAssetAtPath(source+"/Editor/HprFbxSourceTakeAudit.cs")==null)
            throw new InvalidOperationException("Original product and sample not imported");
        AssetDatabase.ExportPackage(source,target,ExportPackageOptions.Recurse);
        if(!File.Exists(target) || new FileInfo(target).Length<5000)
            throw new IOException("Unity did not write original candidate archive");
        Debug.Log("HPR_SOURCE_TAKE_EXPORT_PASS "+new FileInfo(target).Length);
    }
}
#endif
