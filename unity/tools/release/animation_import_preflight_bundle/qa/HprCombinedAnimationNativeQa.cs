#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using System.Text;
using HPR.AnimationImportPreflight;
using HPR.FbxClipIdentity;
using HPR.FbxSourceTakeVisibility;
using UnityEditor;
using UnityEngine;

public static class HprCombinedAnimationNativeQa
{
    private static void Check(bool ok, string label)
    { if(!ok)throw new InvalidOperationException("HPR_COMBINED_ANIM_QA_FAIL:"+label); }
    private static string Receipt(string name)
    {
        string root=Environment.GetEnvironmentVariable("HPR_COMBINED_ANIM_QA_DIR")??"";
        Check(Application.isBatchMode && Path.IsPathRooted(root) && Directory.Exists(root) &&
            root.StartsWith("/data/var/marketplace-account-setup/unity-20261122-wave55/",StringComparison.Ordinal),
            "private_receipt_root");
        string path=Path.Combine(root,name);
        Check(!File.Exists(path),"create_only_receipt");return path;
    }
    private static void Write(string name, string data)
    {
        using(var f=new FileStream(Receipt(name),FileMode.CreateNew,FileAccess.Write,FileShare.None))
        using(var w=new StreamWriter(f,new UTF8Encoding(false)))w.Write(data);
    }

    private static void CheckMatchingCustomerPathsFailClosed()
    {
        var ids=new FbxClipIdentityReport { modelsChecked=1,
            models=new[] {new FbxClipIdentityModel {path="Assets/One.fbx"}} };
        var takes=new SourceTakeScanReport { modelsChecked=1,
            models=new[] {new SourceTakeModelResult {assetPath="Assets/One.fbx"}} };
        Check(HprAnimationImportScan.SameCustomerModels(ids,takes),
            "matching_original_customer_path_can_be_combined");
        takes.models[0].assetPath="Assets/Two.fbx";
        Check(!HprAnimationImportScan.SameCustomerModels(ids,takes),
            "equal_count_but_different_FBX_path_must_fail_closed");
        takes.models[0].assetPath="Assets/One.fbx";
        ids.modelsChecked=2;ids.models=new[] {
            new FbxClipIdentityModel {path="Assets/One.fbx"},
            new FbxClipIdentityModel {path="Assets/One.fbx"}};
        takes.modelsChecked=2;takes.models=new[] {
            new SourceTakeModelResult {assetPath="Assets/One.fbx"},
            new SourceTakeModelResult {assetPath="Assets/One.fbx"}};
        Check(!HprAnimationImportScan.SameCustomerModels(ids,takes),
            "duplicate_same_model_path_must_fail_closed");
    }

    public static void SamplesOnly()
    {
        CheckMatchingCustomerPathsFailClosed();
        Check(HprAnimationImportScan.BuildRows(null,true,"").Length==0,
            "missing_report_must_not_produce_findings_rows");
        Check((AssetImporter.GetAtPath(HprFbxClipIdentityAudit.ExampleFbxPath) as ModelImporter)!=null,
            "real_first_party_clip_ID_importer");
        Check((AssetImporter.GetAtPath(HprFbxSourceTakeAudit.ExampleFbxPath) as ModelImporter)!=null,
            "real_first_party_source_take_importer");
        Check((AssetImporter.GetAtPath(HprFbxSourceTakeAudit.ExampleOmittedTakeFbxPath) as ModelImporter)!=null,
            "real_first_party_deliberately_incomplete_importer");
        var sampleId = HprFbxClipIdentityAudit.ScanSingle(HprFbxClipIdentityAudit.ExampleFbxPath);
        var sampleHealthy = HprFbxSourceTakeAudit.ScanSingle(HprFbxSourceTakeAudit.ExampleFbxPath);
        var sampleWarning = HprFbxSourceTakeAudit.ScanSingle(HprFbxSourceTakeAudit.ExampleOmittedTakeFbxPath);
        Check(!sampleId.incomplete && sampleId.modelsChecked==1 &&
            sampleId.definiteDuplicateIds==0,"original_clip_id_sample_is_clean_and_real");
        Check(!sampleHealthy.incomplete && sampleHealthy.status=="NO_CUSTOMIZED_CLIP_LISTS_TO_COMPARE",
            "original_unmodified_source_take_sample_reports_auto_import");
        Check(!sampleWarning.incomplete && sampleWarning.sourceTakesMissing==1 &&
            sampleWarning.status=="POSSIBLY_UNEXPOSED_SOURCE_TAKES",
            "original_deliberate_missing_source_take_sample_flags_warning");
        var report=HprAnimationImportScan.ScanProject();
        Check(!report.incomplete && report.status=="NO_CUSTOMER_FBX_MODELS_SCANNED" &&
            report.customerModelsChecked==0 && report.repeatedClipIds==0 &&
            report.unreferencedSourceTakes==0 && report.clipIdentities.modelsChecked==0 &&
            report.sourceTakes.modelsChecked==0,
            "combined_buyer_sees_NO_custom_models_not_fake_clean");
        Check(HprAnimationImportScan.BuildRows(report,false,"").Length==0,
            "bundled_examples_excluded_from_results_browser");
        HprAnimationImportScan.ExportNew(report,Receipt("original-vendor-only-both-scans.json"));
        string file=Path.Combine(Environment.GetEnvironmentVariable("HPR_COMBINED_ANIM_QA_DIR"),
            "original-vendor-only-both-scans.json");
        bool refused=false;
        try{HprAnimationImportScan.ExportNew(report,file);}catch(IOException){refused=true;}
        Check(refused && File.ReadAllText(file).Contains("NO_CUSTOMER_FBX_MODELS_SCANNED"),
            "JSON_output_create_only_no_overwrite");
        Write("original-vendor-only-receipt.txt",
            "unity_version="+Application.unityVersion+"\n"+
            "combined_vendor_examples_excluded=PASS\n"+
            "bundled_clip_identity_and_source_take_samples_imported=PASS\n"+
            "original_healthy_and_warning_first_use_examples_validated=PASS\n"+
            "combined_two_scanners_identical_customer_paths_or_INCOMPLETE=PASS\n"+
            "combined_create_only_JSON_export=PASS\n");
        Debug.Log("HPR_COMBINED_ANIMATION_VENDOR_ONLY_NATIVE_PASS");
    }

    private const string Customer="Assets/HPRCombinedPrivateCustomer/OriginalTwoTake.fbx";
    public static void CustomerUnmodified()
    {
        var importer=AssetImporter.GetAtPath(Customer) as ModelImporter;
        Check(importer!=null && importer.defaultClipAnimations.Length==2 &&
            importer.clipAnimations.Length==0,
            "real_original_customer_Blender_two_take_imported");
        var report=HprAnimationImportScan.ScanProject();
        Check(!report.incomplete && report.customerModelsChecked==1 &&
            report.clipIdentities.modelsChecked==1 && report.sourceTakes.modelsChecked==1 &&
            report.status=="NO_TARGETED_FINDINGS_IN_INSPECTED_MODELS" &&
            report.repeatedClipIds==0 && report.unreferencedSourceTakes==0,
            "real_customer_project_both_analyses_no_target_findings");
        Check(HprAnimationImportScan.BuildRows(report,true,"").Length==0,
            "clean_customer_has_no_findings_only_rows");
        var allRows=HprAnimationImportScan.BuildRows(report,false,"ORIGINALTWO");
        Check(allRows.Length==1 && allRows[0].path==Customer &&
            allRows[0].missingSourceTakes==0,
            "all_results_search_case_insensitive_and_selects_real_customer");
        Check(HprAnimationImportScan.BuildRows(report,false,"does-not-exist").Length==0,
            "path_filter_rejects_unknown_models");
        Write("real-customer-original-receipt.txt",
            "unity_version="+Application.unityVersion+"\n"+
            "combined_real_customer_count=1\n"+
            "unmodified_real_original_Blender_FBX_both_scanners=PASS\n");
        Debug.Log("HPR_COMBINED_ANIMATION_CUSTOMER_HEALTHY_NATIVE_PASS");
    }

    public static void CustomerOneTakeMissing()
    {
        var importer=AssetImporter.GetAtPath(Customer) as ModelImporter;
        Check(importer!=null && importer.defaultClipAnimations.Length==2 &&
            importer.clipAnimations.Length==0,"private_fixture_untouched_before_customization");
        string absolute=Path.Combine(Directory.GetParent(Application.dataPath).FullName,Customer);
        string beforeSha=Hash(File.ReadAllBytes(absolute));
        // Private disposable fixture only: intentionally stores one custom clip.
        importer.clipAnimations=new[]{importer.defaultClipAnimations[0]};
        importer.SaveAndReimport();
        var report=HprAnimationImportScan.ScanProject();
        Check(!report.incomplete && report.customerModelsChecked==1 &&
            report.clipIdentities.modelsChecked==1 && report.sourceTakes.modelsChecked==1 &&
            report.repeatedClipIds==0 && report.unreferencedSourceTakes==1 &&
            report.status=="POTENTIAL_ANIMATION_IMPORT_ISSUES",
            "combined_warning_when_real_customer_custom_clips_omit_source_take");
        var findings=HprAnimationImportScan.BuildRows(report,true,"originaltwotake");
        Check(findings.Length==1 && findings[0].path==Customer &&
            findings[0].missingSourceTakes==1 && findings[0].repeatedClipIds==0 &&
            findings[0].missingSourceTakeNames.Length==1,
            "read_only_combined_results_browser_locates_real_customer_issue");
        Check(HprAnimationImportScan.BuildRows(report,true,"wrong-prefix").Length==0,
            "results_browser_filters_real_warning_by_path");
        Check(Hash(File.ReadAllBytes(absolute))==beforeSha,"private_customer_source_FBX_untouched");
        HprAnimationImportScan.ExportNew(report,Receipt("combined-original-customer-warning.json"));
        Write("combined-original-customer-warning.txt",
            "unity_version="+Application.unityVersion+"\n"+
            "source_fbx_sha256="+beforeSha+"\n"+
            "real_combined_customer_warning_detected=PASS\n"+
            "no_missing_customer_source_FBX_bytes=PASS\n");
        Debug.Log("HPR_COMBINED_ANIMATION_CUSTOMER_WARNING_NATIVE_PASS");
    }

    private static string Hash(byte[] bytes)
    {
        using(var sha=System.Security.Cryptography.SHA256.Create())
            return BitConverter.ToString(sha.ComputeHash(bytes)).Replace("-","");
    }
}
#endif
