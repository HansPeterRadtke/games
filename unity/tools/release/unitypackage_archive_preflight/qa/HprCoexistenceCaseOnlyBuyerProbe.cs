#if UNITY_EDITOR
using System;
using System.IO;
using System.Text;
using System.Linq;
using UnityEditor;
using UnityEngine;
// Private disposable-buyer observation only; never ships in a buyer archive.
public static class HprCoexistenceCaseOnlyBuyerProbe
{
    public static void Run()
    {
        string destination=Environment.GetEnvironmentVariable("HPR_CASE_ONLY_REAL_OBSERVATION") ?? "";
        if (!Application.isBatchMode || !Path.IsPathRooted(destination) ||
            !destination.StartsWith("/data/var/marketplace-account-setup/unity-20261121-wave52/",StringComparison.Ordinal) ||
            !destination.EndsWith(".txt",StringComparison.Ordinal) || File.Exists(destination))
            throw new InvalidOperationException("New private case-only project observation required.");
        const string basePath="Assets/HPRUpgradeExample/";
        string first=basePath+"Example.txt";
        string other=basePath+"example.TXT";
        string firstGuid=AssetDatabase.AssetPathToGUID(first);
        string foldedGuid=AssetDatabase.AssetPathToGUID(other);
        string directory=Path.Combine(Directory.GetParent(Application.dataPath).FullName,basePath);
        bool firstPhysical=File.Exists(Path.Combine(directory,"Example.txt"));
        bool secondPhysical=File.Exists(Path.Combine(directory,"example.TXT"));
        string[] assetPaths=AssetDatabase.GetAllAssetPaths()
            .Where(p=>p.StartsWith(basePath,StringComparison.OrdinalIgnoreCase))
            .OrderBy(p=>p,StringComparer.Ordinal).ToArray();
        using (var file=new FileStream(destination,FileMode.CreateNew,FileAccess.Write,FileShare.None))
        using (var output=new StreamWriter(file,new UTF8Encoding(false)))
        {
            output.WriteLine("actual_unity_editor="+Application.unityVersion);
            output.WriteLine("input_mode=two_sequential_original_Unity_exported_packages");
            output.WriteLine("first_physical_path_exists="+firstPhysical);
            output.WriteLine("case_only_physical_path_exists="+secondPhysical);
            output.WriteLine("assetdatabase_first_path_guid="+firstGuid);
            output.WriteLine("assetdatabase_case_only_lookup_guid="+foldedGuid);
            output.WriteLine("assetdatabase_paths_reported="+string.Join(";",assetPaths));
            output.WriteLine("assetdatabase_lookups_same="+(!string.IsNullOrEmpty(firstGuid) && firstGuid==foldedGuid));
            output.WriteLine("observation_only=TRUE; do_not_infer_cross_platform_success");
        }
        Debug.Log("HPR_CASE_ONLY_REAL_BUYER_OBSERVATION_SAVED");
    }
}
#endif
