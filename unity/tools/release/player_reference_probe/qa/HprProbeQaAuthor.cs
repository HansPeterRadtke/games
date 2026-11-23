#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEngine;

// PRIVATE original author package creation. Never included in buyer archive.
public static class HprProbeQaAuthor
{
    public static void Run()
    {
        const string root="Assets/HPRPlayerReferenceProbe";
        const string safe="/data/var/marketplace-account-setup/unity-player-reference-probe-20261123-wave63/";
        var output=Environment.GetEnvironmentVariable("HPR_PLAYER_PROBE_PACKAGE")??"";
        if(!Application.isBatchMode || !Path.IsPathRooted(output) ||
            !output.StartsWith(safe,StringComparison.Ordinal) || File.Exists(output) ||
            !AssetDatabase.IsValidFolder(root))
            throw new InvalidOperationException("HPR_PLAYER_REFERENCE_AUTHOR_MISSING_OR_REPLAYED");
        AssetDatabase.ExportPackage(new[]{root},output,ExportPackageOptions.Recurse);
        if(!File.Exists(output) || new FileInfo(output).Length<100)
            throw new InvalidOperationException("HPR_PLAYER_REFERENCE_AUTHOR_ARCHIVE_MISSING");
        Debug.Log("HPR_PLAYER_REFERENCE_ORIGINAL_PACKAGE_AUTHOR_PASS archive_bytes="+
            new FileInfo(output).Length);
    }
}
#endif
