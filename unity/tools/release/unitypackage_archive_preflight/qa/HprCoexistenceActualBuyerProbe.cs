#if UNITY_EDITOR
using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using UnityEditor;
using UnityEngine;
// PRIVATE actual disposable customer import probe. Results are observations,
// not a guarantee that Unity handles all independent package collisions alike.
public static class HprCoexistenceActualBuyerProbe
{
    public static void Run()
    {
        string destination=Environment.GetEnvironmentVariable("HPR_COEXISTENCE_REAL_IMPORT_RECEIPT");
        if (!Application.isBatchMode || string.IsNullOrEmpty(destination) ||
            !Path.IsPathRooted(destination) ||
            !destination.StartsWith("/data/var/marketplace-account-setup/unity-20261121-wave52/",StringComparison.Ordinal) ||
            !destination.EndsWith(".txt",StringComparison.Ordinal) || File.Exists(destination))
            throw new InvalidOperationException("Fresh private real-buyer coexistence observation required.");
        string basePath="Assets/HPRUpgradeExample/";
        string oldPath=basePath+"Example.txt";
        string newPath=basePath+"ExampleMoved.txt";
        string readme=basePath+"README.md";
        string oldGuid=AssetDatabase.AssetPathToGUID(oldPath);
        string movedGuid=AssetDatabase.AssetPathToGUID(newPath);
        string readmeGuid=AssetDatabase.AssetPathToGUID(readme);
        string referenceGuid=Environment.GetEnvironmentVariable("HPR_COEXISTENCE_EXPECTED_SHARED_GUID") ?? "";
        string referencePath=AssetDatabase.GUIDToAssetPath(referenceGuid);
        using (var output=new FileStream(destination,FileMode.CreateNew,FileAccess.Write,FileShare.None))
        using (var writer=new StreamWriter(output,new UTF8Encoding(false)))
        {
            writer.WriteLine("evidence=actual_native_Editor_AssetDatabase_after_two_independent_real_Unity_exports_imported_sequentially");
            writer.WriteLine("unity_version="+Application.unityVersion);
            writer.WriteLine("baseline_path_asset_exists="+(AssetDatabase.LoadMainAssetAtPath(oldPath)!=null));
            writer.WriteLine("moved_path_asset_exists="+(AssetDatabase.LoadMainAssetAtPath(newPath)!=null));
            writer.WriteLine("baseline_asset_guid="+oldGuid);
            writer.WriteLine("moved_asset_guid="+movedGuid);
            writer.WriteLine("readme_asset_guid="+readmeGuid);
            writer.WriteLine("original_reference_guid="+referenceGuid);
            writer.WriteLine("actual_reference_guid_resolves_to="+referencePath);
            writer.WriteLine("both_paths_present="+(!string.IsNullOrEmpty(oldGuid) && !string.IsNullOrEmpty(movedGuid)));
            writer.WriteLine("same_guid_returned_by_editor="+(!string.IsNullOrEmpty(oldGuid) && oldGuid==movedGuid));
            writer.WriteLine("interpretation=OBSERVATION_ONLY; no GUI dialog clicked, no compatibility success inferred");
        }
        Debug.Log("HPR_COEXISTENCE_REAL_DISPOSABLE_BUYER_OBSERVATION_SAVED");
    }
}
#endif
