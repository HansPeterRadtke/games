#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEngine;

public static class HprFbxClipIdentityExporter
{
    public static void Run()
    {
        string path=Environment.GetEnvironmentVariable("HPR_FBX_ID_ARCHIVE_OUT");
        if (!Application.isBatchMode || string.IsNullOrWhiteSpace(path) ||
            !Path.IsPathRooted(path) ||
            !path.StartsWith("/data/var/marketplace-account-setup/unity-20261121-evening/",StringComparison.Ordinal) ||
            !path.EndsWith(".unitypackage",StringComparison.Ordinal) ||
            File.Exists(path) || Directory.Exists(path))
            throw new InvalidOperationException("A new private absolute Unity archive location is required.");
        const string root="Assets/HPRFbxClipIdentity";
        if (!AssetDatabase.IsValidFolder(root))
            throw new InvalidOperationException("Missing authored buyer source folder");
        AssetDatabase.ExportPackage(root,path,ExportPackageOptions.Recurse);
        if (!File.Exists(path) || new FileInfo(path).Length < 3500)
            throw new IOException("Unity did not create the expected nontrivial export");
        Debug.Log("HPR_FBX_CLIP_IDENTITY_EXPORT_PASS " + new FileInfo(path).Length);
    }
}
#endif
