#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEngine;

// Owner-only private QA exporter; NOT included in the finished buyer archive.
public static class HprPublisherVersionMatrixExporter
{
    public static void Run()
    {
        string target=Environment.GetEnvironmentVariable("HPR_MATRIX_PACKAGE_OUT")??"";
        if(!Application.isBatchMode || !Path.IsPathRooted(target) ||
            !target.StartsWith("/data/var/marketplace-account-setup/",StringComparison.Ordinal) ||
            File.Exists(target) ||
            !AssetDatabase.IsValidFolder("Assets/HPRPublisherVersionMatrix"))
            throw new InvalidOperationException("HPR_MATRIX_PACKAGE_EXPORT_PRECONDITION_FAIL");
        AssetDatabase.ExportPackage(new[]{"Assets/HPRPublisherVersionMatrix"},target,
            ExportPackageOptions.Recurse);
        if(!File.Exists(target) || new FileInfo(target).Length<100)
            throw new InvalidOperationException("HPR_MATRIX_PACKAGE_EXPORT_MISSING");
        Debug.Log("HPR_PUBLISHER_VERSION_MATRIX_PACKAGE_EXPORT_PASS "+
            new FileInfo(target).Length);
    }
}
#endif
