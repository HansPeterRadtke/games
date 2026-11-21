#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using HPR.ArchivePreflight;
using UnityEditor;
using UnityEngine;

// Private independent compatibility test on an actual larger first-party
// product export; never included in the customer candidate archive.
public static class HprArchivePreflightLargeRealQa
{
    private static void Require(bool value,string reason)
    { if (!value) throw new InvalidOperationException("HPR_ARCHIVE_LARGE_REAL_QA_FAIL: "+reason); }
    private static string Hash(string source)
    {
        using (var stream = File.OpenRead(source))
        using (var sha = SHA256.Create())
            return BitConverter.ToString(sha.ComputeHash(stream)).Replace("-", "");
    }
    public static void Run()
    {
        string source = Environment.GetEnvironmentVariable("HPR_ARCHIVE_LARGE_REAL_INPUT") ?? "";
        string evidence=Environment.GetEnvironmentVariable("HPR_ARCHIVE_LARGE_REAL_OUT") ?? "";
        Require(Application.isBatchMode && File.Exists(source) &&
            source.StartsWith("/data/var/marketplace-account-setup/unity-20261121-production/",StringComparison.Ordinal) &&
            evidence.StartsWith("/data/var/marketplace-account-setup/unity-20261121-wave51/",StringComparison.Ordinal) &&
            Path.IsPathRooted(evidence) && !Directory.Exists(evidence) && !File.Exists(evidence),
            "first_party_real_flagship_archive_and_new_scoped_output_required");
        string before=Hash(source);
        var inspected=HprUnitypackageArchiveReader.Inspect(source);
        Debug.Log("HPR_ARCHIVE_LARGE_REAL_SCAN status="+inspected.status+
            " count="+inspected.pathsChecked+" reason="+inspected.reason);
        Require(inspected.status=="READABLE_STRICT_ARCHIVE" && inspected.pathsChecked==161 &&
            inspected.assets.Length==161 && inspected.assets.All(a=>a.guid.Length==32 &&
                !string.IsNullOrWhiteSpace(a.assetPath) && a.importerHash.Length==64),
            "real_161_asset_Gameplay_Suite_archive_parses_completely");
        var exact=HprUnitypackageArchiveReader.Compare(inspected,inspected);
        Require(!exact.incomplete && exact.status=="IDENTICAL_ASSET_IDENTITIES_AND_BYTES" &&
            exact.legacyAssets==161 && exact.updatedAssets==161 &&
            exact.replacedGuids==0 && exact.removedPaths==0 && exact.sourceChanges==0 &&
            exact.importerChanges==0 && exact.movedPaths==0 && exact.addedPaths==0,
            "self_comparison_of_real_large_archive_is_identical");
        Require(Hash(source)==before,"original_large_archive_changed_while_scanning");
        Directory.CreateDirectory(evidence);
        using (var output=new FileStream(Path.Combine(evidence,"large-real-receipt.txt"),
            FileMode.CreateNew,FileAccess.Write,FileShare.None))
        using (var writer=new StreamWriter(output,new UTF8Encoding(false)))
        {
            writer.WriteLine("first_party_real_161_asset_archive_strict_read=PASS");
            writer.WriteLine("full_identity_and_source_self_comparison=PASS");
            writer.WriteLine("real_large_original_archive_unchanged=PASS");
            writer.WriteLine("unity_version="+Application.unityVersion);
            writer.WriteLine("archive_sha256="+before);
        }
        Debug.Log("HPR_ARCHIVE_LARGE_REAL_NATIVE_PASS "+Application.unityVersion);
    }
}
#endif
