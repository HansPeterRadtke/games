#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using HPR.FbxClipIdentity;
using UnityEditor;
using UnityEngine;

// Private buyer-only acceptance test, never shipped to the customer archive.
public static class HprFbxSampleOnlyQa
{
    private static void Check(bool condition, string label)
    { if (!condition) throw new InvalidOperationException("HPR_FBX_SAMPLE_ONLY_QA_FAILURE: " + label); }

    private static string Sha(byte[] bytes)
    {
        using (var h = SHA256.Create())
            return BitConverter.ToString(h.ComputeHash(bytes)).Replace("-", "");
    }

    public static void Run()
    {
        string evidence = Environment.GetEnvironmentVariable("HPR_FBX_SAMPLE_ONLY_QA_OUT");
        Check(Application.isBatchMode && !string.IsNullOrWhiteSpace(evidence) &&
            Path.IsPathRooted(evidence) &&
            evidence.StartsWith("/data/var/marketplace-account-setup/unity-20261121-evening/",
                StringComparison.Ordinal) &&
            !Directory.Exists(evidence) && !File.Exists(evidence),
            "new_private_sample_only_evidence_required");
        string root = Directory.GetParent(Application.dataPath).FullName;
        string model = HprFbxClipIdentityAudit.ExampleFbxPath;
        Check(AssetImporter.GetAtPath(model) is ModelImporter,
            "actual_shipped_sample_imported_with_model_importer");
        string[] customerModels = AssetDatabase.GetAllAssetPaths().Where(p =>
            p.StartsWith("Assets/", StringComparison.Ordinal) &&
            p.EndsWith(".fbx", StringComparison.OrdinalIgnoreCase)).ToArray();
        Check(customerModels.Length == 1 && customerModels[0] == model,
            "independent_buyer_project_contains_only_shipped_fbx_sample");
        string path = Path.Combine(root, model);
        byte[] originalModel = File.ReadAllBytes(path);
        byte[] originalMeta = File.ReadAllBytes(path + ".meta");
        var demo = HprFbxClipIdentityAudit.ScanSingle(model);
        Check(!demo.incomplete && demo.modelsChecked == 1 &&
            demo.models[0].modelClipCount >= 1 && demo.definiteDuplicateIds == 0 &&
            demo.status == "NO_DUPLICATE_IDS_IN_CHECKED_MODELS",
            "explicit_one_click_sample_scan_still_valid");
        var ownProject = HprFbxClipIdentityAudit.ScanAssets();
        Check(!ownProject.incomplete && ownProject.modelsChecked == 0 &&
            ownProject.status == "NO_FBX_MODELS_SCANNED" &&
            ownProject.models != null && ownProject.models.Length == 0,
            "project_scan_must_not_report_bundled_sample_as_customer_model");
        Check(Sha(originalModel) == Sha(File.ReadAllBytes(path)) &&
            Sha(originalMeta) == Sha(File.ReadAllBytes(path + ".meta")),
            "source_fbx_and_import_metadata_unchanged_by_both_scan_modes");
        Directory.CreateDirectory(evidence);
        string receipt = Path.Combine(evidence, "sample-only-receipt.txt");
        using (var stream = new FileStream(receipt, FileMode.CreateNew, FileAccess.Write, FileShare.None))
        using (var writer = new StreamWriter(stream))
        {
            writer.WriteLine("real_shipped_sample_imported=PASS");
            writer.WriteLine("explicit_sample_scan_has_animation=PASS");
            writer.WriteLine("sample_only_project_scan_reports_no_customer_fbx=PASS");
            writer.WriteLine("sample_fbx_and_meta_unchanged=PASS");
            writer.WriteLine("unity_version=" + Application.unityVersion);
        }
        Debug.Log("HPR_FBX_SAMPLE_ONLY_QA_PASS " + Application.unityVersion);
    }
}
#endif
