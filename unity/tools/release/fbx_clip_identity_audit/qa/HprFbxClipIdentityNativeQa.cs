#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using HPR.FbxClipIdentity;
using UnityEditor;
using UnityEngine;

// PRIVATE QA fixture. It is not inside the buyer archive.
public static class HprFbxClipIdentityNativeQa
{
    private static void Check(bool okay, string name)
    { if (!okay) throw new InvalidOperationException("HPR_FBX_ID_QA_FAILURE: " + name); }

    private static string Hash(byte[] bytes)
    {
        using (var alg = SHA256.Create())
            return BitConverter.ToString(alg.ComputeHash(bytes)).Replace("-", "");
    }

    public static void Run()
    {
        string outDir = Environment.GetEnvironmentVariable("HPR_FBX_ID_QA_OUT");
        Check(Application.isBatchMode && !string.IsNullOrWhiteSpace(outDir) &&
            Path.IsPathRooted(outDir) && outDir.StartsWith(
                "/data/var/marketplace-account-setup/unity-20261121-evening/", StringComparison.Ordinal) &&
            !File.Exists(outDir) && !Directory.Exists(outDir), "new_private_qa_location");
        Directory.CreateDirectory(outDir);
        const string imported = "Assets/HPRFbxIdentityPrivateFixture/OriginalMotion.fbx";
        var importer = AssetImporter.GetAtPath(imported) as ModelImporter;
        Check(importer != null, "genuine_model_importer");
        string absolute = Path.Combine(Directory.GetParent(Application.dataPath).FullName, imported);
        byte[] beforeSource = File.ReadAllBytes(absolute);
        byte[] beforeMeta = File.ReadAllBytes(absolute + ".meta");
        var real = HprFbxClipIdentityAudit.ScanOne(imported);
        Check(real != null && !real.incomplete && real.modelClipCount >= 1,
            "real_blender_animation_imported_and_checked");
        Check(real.duplicateClipIds == 0, "original_model_has_no_duplicate_clip_ids");
        string sampleAsset = HprFbxClipIdentityAudit.ExampleFbxPath;
        var sampleImporter = AssetImporter.GetAtPath(sampleAsset) as ModelImporter;
        Check(sampleImporter != null, "sample_model_is_original_blender_animation");
        string sampleAbsolute = Path.Combine(Directory.GetParent(Application.dataPath).FullName,
            sampleAsset);
        byte[] sampleOriginal = File.ReadAllBytes(sampleAbsolute);
        byte[] sampleSettings = File.ReadAllBytes(sampleAbsolute + ".meta");
        Check(Hash(sampleOriginal) == Hash(beforeSource),
            "bundled_sample_matches_first_party_source_exactly");
        var sampleReport = HprFbxClipIdentityAudit.ScanSingle(sampleAsset);
        Check(sampleReport.modelsChecked == 1 && !sampleReport.incomplete &&
            sampleReport.models[0].modelClipCount >= 1 &&
            sampleReport.models[0].duplicateClipIds == 0 &&
            sampleReport.status == "NO_DUPLICATE_IDS_IN_CHECKED_MODELS",
            "sample_one_click_source_scan");
        var singleReport = HprFbxClipIdentityAudit.ScanSingle(imported);
        Check(singleReport.modelsChecked == 1 && !singleReport.incomplete &&
            singleReport.models[0].modelClipCount >= 1 &&
            singleReport.models[0].duplicateClipIds == 0,
            "selected_model_single_scan");
        var invalidSingle = HprFbxClipIdentityAudit.ScanSingle("Assets/BadFolder/file.txt");
        Check(invalidSingle.incomplete && invalidSingle.status == "INCOMPLETE",
            "invalid_selected_model_fails_closed");
        var noAnimation = new FbxClipIdentityReport
        {
            modelsChecked = 1, models = new[] { new FbxClipIdentityModel
            { path = "Assets/StaticNoAnimation.fbx", modelClipCount = 0,
                incomplete = false, duplicateClipIds = 0 } }
        };
        Check(HprFbxClipIdentityAudit.Classify(noAnimation) ==
            "NO_ANIMATION_CLIPS_IN_CHECKED_MODELS",
            "clipless_scan_not_misreported_clean");
        var realMeta = HprFbxClipIdentityAudit.AnalyzeMetaText(imported,
            File.ReadAllText(absolute + ".meta"));
        Check(!realMeta.incomplete && realMeta.duplicateClipIds == 0,
            "exact_original_importer_meta_parsed");
        string testMeta = "fileFormatVersion: 2\nguid: 44444444444444444444444444444444\nModelImporter:\n" +
            "  internalIDToNameTable:\n" +
            "  - first:\n      74: 744242\n    second: DanceA\n" +
            "  - first:\n      74: 744242\n    second: DanceB\n" +
            "  externalObjects: {}\n  animations:\n    clipAnimations: []\n";
        var duplicated = HprFbxClipIdentityAudit.AnalyzeMetaText(imported, testMeta);
        Check(duplicated.status == "DUPLICATE_CLIP_IDS" &&
            duplicated.duplicateClipIds == 1 && duplicated.clipIdEntries == 2 &&
            duplicated.findings.Any(f => f.rule == "DUPLICATE_ANIMATION_CLIP_LOCAL_ID"),
            "deliberate_duplicate_animation_id_detected");
        string customMeta = "fileFormatVersion: 2\nguid: 33333333333333333333333333333333\nModelImporter:\n" +
            "  internalIDToNameTable: []\n  externalObjects: {}\n  animations:\n" +
            "    clipAnimations:\n" +
            "    - serializedVersion: 16\n      name: TakeOne\n      takeName: Take\n      internalID: -77665544\n" +
            "    - serializedVersion: 16\n      name: TakeTwo\n      takeName: Take\n      internalID: -77665544\n" +
            "    isReadable: 0\n";
        var customDuplicate = HprFbxClipIdentityAudit.AnalyzeMetaText(imported, customMeta);
        Check(!customDuplicate.incomplete && customDuplicate.duplicateClipIds == 1 &&
            customDuplicate.configuredClipEntries == 2 &&
            customDuplicate.findings.Any(f => f.rule == "DUPLICATE_CONFIGURED_CLIP_INTERNAL_ID"),
            "two_custom_clip_animation_ids_detected");
        var zeroPlaceholder = HprFbxClipIdentityAudit.AnalyzeMetaText(imported,
            customMeta.Replace("-77665544", "0"));
        Check(zeroPlaceholder.incomplete && zeroPlaceholder.status == "INCOMPLETE" &&
            zeroPlaceholder.findings.Any(f => f.rule == "REPEATED_ZERO_CLIP_ID"),
            "repeated_zero_custom_clip_ids_trigger_manual_review");
        var uniqueCustom = HprFbxClipIdentityAudit.AnalyzeMetaText(imported,
            customMeta.Replace("      name: TakeTwo\n      takeName: Take\n      internalID: -77665544",
                               "      name: TakeTwo\n      takeName: Take\n      internalID: -88776655"));
        Check(!uniqueCustom.incomplete && uniqueCustom.duplicateClipIds == 0 &&
            uniqueCustom.configuredClipEntries == 2,
            "different_custom_clip_ids_not_wrongly_flagged");
        var unrelated = HprFbxClipIdentityAudit.AnalyzeMetaText(imported,
            testMeta.Replace("74: 744242", "43: 744242"));
        Check(!unrelated.incomplete && unrelated.duplicateClipIds == 0,
            "non_animation_class_id_not_false_positive");
        var malformed = HprFbxClipIdentityAudit.AnalyzeMetaText(imported,
            testMeta.Replace("      74: 744242\n", ""));
        Check(malformed.incomplete && malformed.status == "INCOMPLETE",
            "malformed_metadata_fails_closed");
        Check(HprFbxClipIdentityAudit.AnalyzeMetaText("Assets/../escaped.fbx",testMeta).incomplete,
            "path_traversal_rejected");
        Check(HprFbxClipIdentityAudit.AnalyzeMetaText(imported, "not importer yaml").incomplete,
            "unrecognized_metadata_fails_closed");
        var report = HprFbxClipIdentityAudit.ScanAssets();
        Check(!report.incomplete && report.modelsChecked >= 1 &&
            report.status == "NO_DUPLICATE_IDS_IN_CHECKED_MODELS" &&
            report.models.Any(m => m.path == imported && m.modelClipCount >= 1),
            "real_project_model_scan");
        var empty = new FbxClipIdentityReport
        {
            modelsChecked = 0, models = new FbxClipIdentityModel[0], incomplete = false
        };
        Check(HprFbxClipIdentityAudit.Classify(empty) == "NO_FBX_MODELS_SCANNED",
            "empty_project_does_not_claim_a_clean_fbx_scan");
        Check(HprFbxClipIdentityAudit.Classify(null) == "INCOMPLETE" &&
              HprFbxClipIdentityAudit.Classify(new FbxClipIdentityReport
              { modelsChecked = 2, models = new FbxClipIdentityModel[0] }) == "INCOMPLETE",
            "malformed_combined_report_fails_closed");
        var stopped = HprFbxClipIdentityAudit.ScanAssets((at,total) => true);
        Check(stopped.incomplete && stopped.modelsChecked == 0 && stopped.status == "INCOMPLETE",
            "cancelled_project_scan_not_reported_clean");
        string newFile = Path.Combine(outDir, "fbx-identity-report.json");
        HprFbxClipIdentityAudit.ExportNew(report, newFile);
        string reportText = File.ReadAllText(newFile);
        Check(reportText.Contains("OriginalMotion.fbx") && reportText.Contains("unityVersion"),
            "machine_report_contains_real_model");
        bool overwriteBlocked = false;
        try { HprFbxClipIdentityAudit.ExportNew(report,newFile); }
        catch (IOException) { overwriteBlocked = true; }
        Check(overwriteBlocked && File.ReadAllText(newFile) == reportText,
            "existing_report_never_overwritten");
        Check(Hash(beforeSource) == Hash(File.ReadAllBytes(absolute)) &&
              Hash(beforeMeta) == Hash(File.ReadAllBytes(absolute + ".meta")),
            "original_fbx_and_meta_untouched");
        Check(Hash(sampleOriginal) == Hash(File.ReadAllBytes(sampleAbsolute)) &&
              Hash(sampleSettings) == Hash(File.ReadAllBytes(sampleAbsolute + ".meta")),
            "bundled_first_party_fbx_and_meta_untouched");
        // For testing importer YAML, intentionally create a SECOND original
        // animated FBX in this disposable project and configure split clips.
        // Original user/fixture FBX bytes and metadata above were NOT changed.
        const string customPath = "Assets/HPRFbxIdentityPrivateCustom/SplitMotion.fbx";
        Check(!AssetDatabase.IsValidFolder("Assets/HPRFbxIdentityPrivateCustom"),
            "fresh_disposable_custom_clip_fixture_only");
        AssetDatabase.CreateFolder("Assets", "HPRFbxIdentityPrivateCustom");
        Check(AssetDatabase.CopyAsset(imported, customPath), "copy_original_fbx_to_disposable_custom_fixture");
        var customImporter = AssetImporter.GetAtPath(customPath) as ModelImporter;
        Check(customImporter != null && customImporter.defaultClipAnimations != null &&
            customImporter.defaultClipAnimations.Length > 0,
            "actual_default_clips_available_for_split_fixture");
        var defaults = customImporter.defaultClipAnimations[0];
        var firstPart = new ModelImporterClipAnimation
        { name = "HPR_SplitA", takeName = defaults.takeName,
          firstFrame = defaults.firstFrame, lastFrame = defaults.firstFrame + 8 };
        var secondPart = new ModelImporterClipAnimation
        { name = "HPR_SplitB", takeName = defaults.takeName,
          firstFrame = defaults.firstFrame + 9, lastFrame = defaults.lastFrame };
        customImporter.clipAnimations = new[] { firstPart, secondPart };
        customImporter.SaveAndReimport();
        string customMetaOnDisk = File.ReadAllText(Path.Combine(
            Directory.GetParent(Application.dataPath).FullName, customPath + ".meta"));
        Check(customMetaOnDisk.Contains("clipAnimations:") &&
              customMetaOnDisk.Contains("internalID:"),
              "real_model_importer_wrote_custom_clip_ids");
        var customReal = HprFbxClipIdentityAudit.ScanOne(customPath);
        Check(customReal.configuredClipEntries == 2 && customReal.modelClipCount >= 2,
            "genuine_unity_split_animation_clip_id_scan");
        Check(customReal.duplicateClipIds == 0 || customReal.incomplete,
            "real_split_clip_model_not_misreported_as_clean_on_collision");
        Check(Hash(beforeSource) == Hash(File.ReadAllBytes(absolute)) &&
              Hash(beforeMeta) == Hash(File.ReadAllBytes(absolute + ".meta")),
            "original_model_remains_untouched_after_separate_custom_clip_fixture");
        File.WriteAllText(Path.Combine(outDir,"native-receipt.txt"),
            "real_original_blender_fbx_import=PASS\n" +
            "real_model_anim_clip_count=PASS\n" +
            "real_unmodified_meta_parsed=PASS\n" +
            "synthetic_duplicate_clip_id_detected=PASS\n" +
            "custom_clip_animation_duplicate_detected=PASS\n" +
            "zero_placeholder_review_not_false_clean=PASS\n" +
            "unique_custom_clip_id_not_false_positive=PASS\n" +
            "real_unity_custom_split_clip_importer=PASS\n" +
            "nonclip_id_is_not_false_positive=PASS\n" +
            "malformed_meta_fails_closed=PASS\n" +
            "traversal_and_unexpected_metadata_rejected=PASS\n" +
            "all_project_fbx_scanned=PASS\n" +
            "empty_project_is_not_claimed_clean=PASS\n" +
            "mismatched_report_is_not_claimed_clean=PASS\n" +
            "cancelled_scan_fails_closed=PASS\n" +
            "create_only_machine_report=PASS\n" +
            "source_and_import_settings_unchanged=PASS\n" +
            "bundled_original_animation_imported=PASS\n" +
            "bundled_original_bytes_stable=PASS\n" +
            "sample_and_selected_single_scan=PASS\n" +
            "clipless_fbx_does_not_look_clean=PASS\n" +
            "unity_version=" + Application.unityVersion + "\n");
        Debug.Log("HPR_FBX_CLIP_IDENTITY_NATIVE_PASS " + Application.unityVersion +
                  " clips=" + real.modelClipCount + " table=" + real.idEntries);
    }
}
#endif
