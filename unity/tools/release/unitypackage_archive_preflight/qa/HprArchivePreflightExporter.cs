#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEngine;
public static class HprArchivePreflightExporter
{
    public static void Run()
    {
        string destination = Environment.GetEnvironmentVariable("HPR_ARCHIVE_PREFLIGHT_EXPORT") ?? "";
        const string root = "Assets/HPRArchivePreflight";
        if (!Application.isBatchMode || !Path.IsPathRooted(destination) ||
            !destination.StartsWith("/data/var/marketplace-account-setup/unity-20261121-wave50/",StringComparison.Ordinal) ||
            !destination.EndsWith(".unitypackage",StringComparison.Ordinal) ||
            File.Exists(destination) || !AssetDatabase.IsValidFolder(root))
            throw new InvalidOperationException("New private buyer archive and real original vendor root required.");
        AssetDatabase.ExportPackage(root,destination,ExportPackageOptions.Recurse);
        if (!File.Exists(destination) || new FileInfo(destination).Length < 4000)
            throw new IOException("Unity did not export real buyer preflight archive.");
        Debug.Log("HPR_ARCHIVE_PREFLIGHT_REAL_EXPORT_PASS "+new FileInfo(destination).Length);
    }
}
#endif
