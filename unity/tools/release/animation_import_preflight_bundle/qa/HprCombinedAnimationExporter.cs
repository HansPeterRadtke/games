#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEngine;

public static class HprCombinedAnimationExporter
{
    public static void Run()
    {
        string dest=Environment.GetEnvironmentVariable("HPR_COMBINED_ANIM_PACKAGE_OUT")??"";
        if(!Application.isBatchMode || !Path.IsPathRooted(dest) ||
           !dest.StartsWith("/data/var/marketplace-account-setup/unity-20261122-wave55/",StringComparison.Ordinal) ||
           !dest.EndsWith(".unitypackage",StringComparison.OrdinalIgnoreCase) || File.Exists(dest))
            throw new InvalidOperationException("Fresh private candidate package path required");
        string[] roots={"Assets/HPRFbxClipIdentity","Assets/HPRFbxSourceTakes","Assets/HPRAnimationImportPreflight"};
        foreach(string root in roots)
            if(!AssetDatabase.IsValidFolder(root))
                throw new InvalidOperationException("First-party source root missing: "+root);
        AssetDatabase.ExportPackage(roots,dest,ExportPackageOptions.Recurse);
        if(!File.Exists(dest) || new FileInfo(dest).Length<10000)
            throw new InvalidOperationException("Official Unity package export did not succeed");
        Debug.Log("HPR_COMBINED_ANIMATION_NATIVE_EXPORT_PASS "+new FileInfo(dest).Length);
    }
}
#endif
