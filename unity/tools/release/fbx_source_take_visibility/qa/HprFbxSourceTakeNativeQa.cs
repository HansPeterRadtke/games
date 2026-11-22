#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using System.Text;
using HPR.FbxSourceTakeVisibility;
using UnityEditor;
using UnityEngine;
// Owner-private first-party actual Unity importer acceptance, never buyer content.
public static class HprFbxSourceTakeNativeQa
{
    private static void Check(bool truth, string message)
    { if (!truth) throw new InvalidOperationException("HPR_TAKE_VISIBILITY_QA_FAILURE:"+message); }
    // Only the private duplicate FBX under Assets/PrivateSourceTakes/ may be
    // modified; it must never affect the source/retail sample or buyer data.
    private const string PrivateAsset = "Assets/HPRPrivateSourceTakes/OriginalTwoTake.fbx";
    private static string PrivateProof(string name)
    {
        string root=Environment.GetEnvironmentVariable("HPR_SOURCE_TAKE_CUSTOM_QA_DIR") ?? "";
        Check(Application.isBatchMode && Path.IsPathRooted(root) && Directory.Exists(root) &&
            root.StartsWith("/data/var/marketplace-account-setup/unity-20261122-wave54/",StringComparison.Ordinal),
            "private_custom_qa_folder");
        string destination=Path.Combine(root,name);
        Check(!File.Exists(destination),"private_custom_qa_create_only");
        return destination;
    }
    private static string SourceSha(string path)
    {
        using(var h=System.Security.Cryptography.SHA256.Create())
            return BitConverter.ToString(h.ComputeHash(File.ReadAllBytes(path))).Replace("-","");
    }
    public static void CustomizePrivate()
    {
        var importer=AssetImporter.GetAtPath(PrivateAsset) as ModelImporter;
        Check(importer!=null,"private_fixture_in_buyer_project");
        var source=importer.defaultClipAnimations;
        Check(source!=null && source.Length==2 && source[0]!=null && source[1]!=null &&
            source[0].takeName!=source[1].takeName,"two_distinct_source_takes_exist");
        Check(importer.clipAnimations!=null && importer.clipAnimations.Length==0,
            "private_fixture_initially_automatic");
        string path=Path.GetFullPath(Path.Combine(Directory.GetParent(Application.dataPath).FullName,PrivateAsset));
        string before=SourceSha(path);
        // This is the only intentional importer edit, strictly private fixture.
        importer.clipAnimations=new[] {source[0]};
        importer.SaveAndReimport();
        var changed=AssetImporter.GetAtPath(PrivateAsset) as ModelImporter;
        Check(changed!=null && changed.clipAnimations!=null && changed.clipAnimations.Length==1,
            "real_custom_split_clip_persisted");
        Check(SourceSha(path)==before,"private_source_fbx_bytes_preserved");
        using(var file=new FileStream(PrivateProof("private-customization-receipt.txt"),FileMode.CreateNew,FileAccess.Write,FileShare.None))
        using(var writer=new StreamWriter(file,new UTF8Encoding(false)))
        {
            writer.WriteLine("unity_version="+Application.unityVersion);
            writer.WriteLine("source_sha256="+before);
            writer.WriteLine("original_two_source_names="+string.Join(";",source.Select(x=>x.takeName)));
            writer.WriteLine("stored_custom_take_name="+changed.clipAnimations[0].takeName);
            writer.WriteLine("test_only_importer_change=PRIVATE_FIXTURE_NOT_VENDOR");
        }
        Debug.Log("HPR_SOURCE_TAKE_PRIVATE_CUSTOMIZATION_PASS");
    }
    public static void AuditCustomized()
    {
        var importer=AssetImporter.GetAtPath(PrivateAsset) as ModelImporter;
        Check(importer!=null && importer.defaultClipAnimations.Length==2 &&
            importer.clipAnimations.Length==1,"persistent_real_modified_custom_clips");
        var result=HprFbxSourceTakeAudit.ScanSingle(PrivateAsset);
        Check(!result.incomplete && result.status=="POSSIBLY_UNEXPOSED_SOURCE_TAKES" &&
            result.modelsWithMissingSourceTakes==1 && result.sourceTakesMissing==1 &&
            result.models[0].customClipCount==1 &&
            result.models[0].missingSourceTakes.Length==1 &&
            result.models[0].status=="SOURCE_TAKES_NOT_IN_CUSTOM_LIST",
            "real_missing_source_take_discovered_by_original_scanner");
        var all=HprFbxSourceTakeAudit.ScanAssets();
        Check(!all.incomplete && all.modelsChecked==1 &&
            all.modelsWithMissingSourceTakes==1 && all.sourceTakesMissing==1,
            "project_scan_filters_sample_and_warns_private_customer_model");
        string absolute=Path.GetFullPath(Path.Combine(Directory.GetParent(Application.dataPath).FullName,PrivateAsset));
        string sourceSha=SourceSha(absolute);
        string beforeReport=Path.Combine(Environment.GetEnvironmentVariable("HPR_SOURCE_TAKE_CUSTOM_QA_DIR"),
            "private-customization-receipt.txt");
        Check(File.Exists(beforeReport) && File.ReadAllText(beforeReport).Contains(sourceSha),
            "real_private_source_unchanged_since_customization");
        using(var file=new FileStream(PrivateProof("private-source-take-audit.txt"),FileMode.CreateNew,FileAccess.Write,FileShare.None))
        using(var writer=new StreamWriter(file,new UTF8Encoding(false)))
        {
            writer.WriteLine("unity_version="+Application.unityVersion);
            writer.WriteLine("scan_status="+result.status);
            writer.WriteLine("missed_source_take="+result.models[0].missingSourceTakes[0]);
            writer.WriteLine("private_source_sha256="+sourceSha);
            writer.WriteLine("private_custom_omission_flagged=PASS");
            writer.WriteLine("real_project_sample_excluded=PASS");
        }
        var json=new SourceTakeScanReport
        {
            status=result.status,modelsChecked=result.modelsChecked,
            sourceTakesMissing=result.sourceTakesMissing,
            modelsWithMissingSourceTakes=result.modelsWithMissingSourceTakes,
            models=result.models,incomplete=false,unityVersion=Application.unityVersion,
            limitation=result.limitation
        };
        string newFile=PrivateProof("original-source-take-review.json");
        HprFbxSourceTakeAudit.ExportNew(json,newFile);
        bool overwriteBlocked=false;
        try {HprFbxSourceTakeAudit.ExportNew(json,newFile);}
        catch(IOException) {overwriteBlocked=true;}
        Check(overwriteBlocked && File.ReadAllText(newFile).Contains("SOURCE_TAKES_NOT_IN_CUSTOM_LIST"),
            "create_only_report_cannot_overwrite");
        Debug.Log("HPR_SOURCE_TAKE_REAL_CUSTOMIZED_AUDIT_PASS");
    }

    private const string ChangedSourceAsset = "Assets/HPRPrivateSourceChange/Source.fbx";
    public static void PrepareActualSourceChange()
    {
        string target=PrivateProof("source-change-before.txt");
        var importer=AssetImporter.GetAtPath(ChangedSourceAsset) as ModelImporter;
        Check(importer!=null && importer.importAnimation,"actual_original_one_take_source_imported");
        var sources=importer.defaultClipAnimations;
        Check(sources!=null && sources.Length==1 && sources[0]!=null &&
            sources[0].takeName.Contains("HPR_Original_Sway"),
            "first_original_Blender_source_contains_one_real_take");
        Check(importer.clipAnimations!=null && importer.clipAnimations.Length==0,
            "first_original_source_auto_mode");
        string source=Path.GetFullPath(Path.Combine(Directory.GetParent(Application.dataPath).FullName,
            ChangedSourceAsset));
        string before=SourceSha(source);
        string identity=AssetDatabase.AssetPathToGUID(ChangedSourceAsset);
        // This is the only intentional customer-like action and is confined
        // to a NEW disposable project and the test-only FBX under HPRPrivate.
        importer.clipAnimations=new[]{sources[0]};
        importer.SaveAndReimport();
        var refreshed=AssetImporter.GetAtPath(ChangedSourceAsset) as ModelImporter;
        Check(refreshed!=null && refreshed.clipAnimations.Length==1 &&
            refreshed.clipAnimations[0].takeName==sources[0].takeName &&
            AssetDatabase.AssetPathToGUID(ChangedSourceAsset)==identity &&
            SourceSha(source)==before,
            "first_one_take_importer_customization_persisted_without_source_changes");
        using(var output=new FileStream(target,FileMode.CreateNew,FileAccess.Write,FileShare.None))
        using(var w=new StreamWriter(output,new UTF8Encoding(false)))
        {
            w.WriteLine("unity_version="+Application.unityVersion);
            w.WriteLine("original_source_sha256="+before);
            w.WriteLine("original_fbx_guid="+identity);
            w.WriteLine("first_source_take="+sources[0].takeName);
            w.WriteLine("saved_custom_take="+refreshed.clipAnimations[0].takeName);
            w.WriteLine("first_original_unity_import_and_manual_split=PASS");
        }
        Debug.Log("HPR_ACTUAL_ONE_TAKE_CUSTOMIZED_BEFORE_SOURCE_UPDATE_PASS");
    }

    public static void AuditActualSourceChange()
    {
        string target=PrivateProof("source-change-after.txt");
        string old=Path.Combine(Environment.GetEnvironmentVariable("HPR_SOURCE_TAKE_CUSTOM_QA_DIR"),
            "source-change-before.txt");
        Check(File.Exists(old),"old_actual_original_source_change_receipt_exists");
        string oldReceipt=File.ReadAllText(old);
        Check(oldReceipt.Contains("first_original_unity_import_and_manual_split=PASS"),
            "actual_initial_manual_clip_customization_recorded");
        // Refreshes only owner-created disposable private cloned FBX; does
        // NOT touch the retail original model or a user's actual project.
        AssetDatabase.ImportAsset(ChangedSourceAsset,ImportAssetOptions.ForceSynchronousImport |
            ImportAssetOptions.ForceUpdate);
        var importer=AssetImporter.GetAtPath(ChangedSourceAsset) as ModelImporter;
        Check(importer!=null && importer.importAnimation,"same_source_fbx_reimported_after_original_Blender_update");
        var defaults=importer.defaultClipAnimations;
        var customized=importer.clipAnimations;
        Check(defaults!=null && defaults.Length==2 && customized!=null && customized.Length==1,
            "actual_second_original_Blender_source_two_actions_existing_custom_clip_list_retained");
        string guid=AssetDatabase.AssetPathToGUID(ChangedSourceAsset);
        Check(oldReceipt.Contains("original_fbx_guid="+guid),
            "same_imported_asset_guid_retained_across_real_source_update");
        var report=HprFbxSourceTakeAudit.ScanSingle(ChangedSourceAsset);
        Check(!report.incomplete && report.status=="POSSIBLY_UNEXPOSED_SOURCE_TAKES" &&
            report.sourceTakesMissing==1 && report.modelsWithMissingSourceTakes==1 &&
            report.models[0].missingSourceTakes.Length==1 &&
            report.models[0].missingSourceTakes[0].Contains("HPR_Original_Hop"),
            "after_real_Blender_reexport_new_source_take_not_in_custom_clip_detected");
        var all=HprFbxSourceTakeAudit.ScanAssets();
        Check(!all.incomplete && all.modelsChecked==1 && all.sourceTakesMissing==1,
            "real_buyer_project_scan_source_update_flags_missing_take");
        string source=Path.GetFullPath(Path.Combine(Directory.GetParent(Application.dataPath).FullName,
            ChangedSourceAsset));
        using(var output=new FileStream(target,FileMode.CreateNew,FileAccess.Write,FileShare.None))
        using(var w=new StreamWriter(output,new UTF8Encoding(false)))
        {
            w.WriteLine("unity_version="+Application.unityVersion);
            w.WriteLine("source_sha256_after_original_Blender_update="+SourceSha(source));
            w.WriteLine("guid_unchanged="+guid);
            w.WriteLine("real_current_source_takes="+string.Join(";",defaults.Select(x=>x.takeName)));
            w.WriteLine("real_saved_custom_clip="+customized[0].takeName);
            w.WriteLine("detected_added_missing_take="+report.models[0].missingSourceTakes[0]);
            w.WriteLine("original_one_to_two_take_source_change_diagnostic=PASS");
        }
        Debug.Log("HPR_ACTUAL_FBX_SOURCE_UPDATE_VISIBILITY_PASS");
    }

    public static void Probe()
    {
        string path=Environment.GetEnvironmentVariable("HPR_SOURCE_TAKE_QA_OUT") ?? "";
        Check(Application.isBatchMode && Path.IsPathRooted(path) &&
            path.StartsWith("/data/var/marketplace-account-setup/unity-20261122-wave54/",StringComparison.Ordinal) &&
            !File.Exists(path), "private_new_QA_out");
        const string demo=HprFbxSourceTakeAudit.ExampleFbxPath;
        var importer=AssetImporter.GetAtPath(demo) as ModelImporter;
        Check(importer!=null,"original_Unity_ModelImporter");
        var source=importer.defaultClipAnimations;
        var customized=importer.clipAnimations;
        Check(source!=null && customized!=null,"actual_Unity_take_arrays");
        string[] names=source.Select(t=>t==null ? "<NULL>" : t.takeName).ToArray();
        var result=HprFbxSourceTakeAudit.ScanSingle(demo);
        const string expectedNegative=HprFbxSourceTakeAudit.ExampleOmittedTakeFbxPath;
        var negativeImporter=AssetImporter.GetAtPath(expectedNegative) as ModelImporter;
        Check(negativeImporter!=null && negativeImporter.defaultClipAnimations.Length==2 &&
            negativeImporter.clipAnimations.Length==1,
            "included_second_original_sample_has_real_persisted_missing_source_take");
        var negativeReport=HprFbxSourceTakeAudit.ScanSingle(expectedNegative);
        Check(!negativeReport.incomplete && negativeReport.sourceTakesMissing==1 &&
            negativeReport.modelsWithMissingSourceTakes==1 &&
            negativeReport.status=="POSSIBLY_UNEXPOSED_SOURCE_TAKES" &&
            negativeReport.models[0].missingSourceTakes.Length==1,
            "included_deliberately_missing_source_take_detected_by_actual_Unity_import");
        string authorRoot=Directory.GetParent(Application.dataPath).FullName;
        string healthyPath=Path.Combine(authorRoot,demo);
        string negativePath=Path.Combine(authorRoot,expectedNegative);
        Check(SourceSha(healthyPath)==SourceSha(negativePath),
            "included_positive_and_negative_FBX_use_exact_same_first_party_Blender_source");
        string healthyId=AssetDatabase.AssetPathToGUID(demo);
        string negativeId=AssetDatabase.AssetPathToGUID(expectedNegative);
        Check(!string.IsNullOrEmpty(healthyId) && !string.IsNullOrEmpty(negativeId) && healthyId!=negativeId,
            "original_two_sample_FBX_guids_unique");
        // Validate actual Unity-authored prefab and scene references in the
        // isolated buyer project, not only their filenames in a TAR archive.
        const string prefabA="Assets/HPRFbxSourceTakes/Samples/Prefabs/OriginalAutoTwoTake.prefab";
        const string prefabB="Assets/HPRFbxSourceTakes/Samples/Prefabs/OriginalConfiguredMissingTake.prefab";
        const string demoScene="Assets/HPRFbxSourceTakes/Samples/Scenes/SourceTakeVisibilityDemo.unity";
        var modelA=AssetDatabase.LoadAssetAtPath<GameObject>(prefabA);
        var modelB=AssetDatabase.LoadAssetAtPath<GameObject>(prefabB);
        var sceneAsset=AssetDatabase.LoadAssetAtPath<SceneAsset>(demoScene);
        Check(modelA!=null && modelB!=null && sceneAsset!=null,
            "demo_scene_and_both_prefabs_imported_and_resolve");
        string[] deps=AssetDatabase.GetDependencies(demoScene,true);
        Check(deps.Contains(prefabA) && deps.Contains(prefabB) &&
            deps.Contains(demo) && deps.Contains(expectedNegative),
            "genuine_demo_scene_references_both_original_prefabs_and_FBX_sources");
        var project=HprFbxSourceTakeAudit.ScanAssets();
        Check(!project.incomplete && project.modelsChecked==0 &&
            project.status=="NO_CUSTOMER_FBX_MODELS_SCANNED", "demo_not_counted_as_customer_project");
        Check(!result.incomplete && result.modelsChecked==1, "original_demo_scans_readonly");
        var duplicate=HprFbxSourceTakeAudit.Compare(demo,
            new[]{"Walk","Jump"},new[]{"Walk"},true);
        Check(!duplicate.incomplete && duplicate.status=="SOURCE_TAKES_NOT_IN_CUSTOM_LIST" &&
            duplicate.missingSourceTakes.Length==1 && duplicate.missingSourceTakes[0]=="Jump",
            "pure_reference_source_take_omission_detected");
        var split=HprFbxSourceTakeAudit.Compare(demo,
            new[]{"Walk","Jump"},new[]{"Walk","Walk","Jump"},true);
        Check(split.status=="ALL_SOURCE_TAKE_NAMES_REFERENCED" &&
            split.missingSourceTakeCount==0,"normal_split_clip_duplicate_take_not_false_positive");
        var empty=HprFbxSourceTakeAudit.Compare(demo,
            new[]{"Walk","Jump"},new string[0],false);
        Check(empty.status=="DEFAULT_SOURCE_TAKES_ACTIVE" &&
            empty.missingSourceTakeCount==0,"empty_custom_list_defaults_not_false_positive");
        Check(HprFbxSourceTakeAudit.Compare(demo,new[]{"Walk","Walk"},
            new[]{"Walk"},true).incomplete,"ambiguous_duplicate_take_fails_closed");
        Check(HprFbxSourceTakeAudit.Compare(demo,new string[0],
            new string[0],false).status=="NO_SOURCE_TAKES",
            "no_source_animation_is_not_positive_pass");
        Check(HprFbxSourceTakeAudit.Compare(demo,new[]{"Walk"},
            new string[0],false,false).status=="ANIMATION_IMPORT_DISABLED",
            "disabled_animation_import_is_not_positive_pass");
        Check(HprFbxSourceTakeAudit.ScanSingle("Assets/../escape.fbx").incomplete,
            "traversal_rejected");
        var oversize=Enumerable.Range(0,HprFbxSourceTakeAudit.MaxTakesPerModel+1)
            .Select(i=>"Name"+i).ToArray();
        Check(HprFbxSourceTakeAudit.Compare(demo,oversize,oversize,true).incomplete,
            "oversized_take_list_fails_closed");
        Check(HprFbxSourceTakeAudit.Classify(new SourceTakeScanReport
            {modelsChecked=1,models=new SourceTakeModelResult[0]})=="INCOMPLETE",
            "unmatched_scan_count_fails_closed");
        using(var file=new FileStream(path,FileMode.CreateNew,FileAccess.Write,FileShare.None))
        using(var writer=new StreamWriter(file,new UTF8Encoding(false)))
        {
            writer.WriteLine("unity_version="+Application.unityVersion);
            writer.WriteLine("original_source_take_count="+names.Length);
            writer.WriteLine("original_source_take_names="+string.Join(";",names));
            writer.WriteLine("original_custom_clip_count="+customized.Length);
            writer.WriteLine("original_example_status="+result.status);
            writer.WriteLine("second_deliberate_source_omission_status="+negativeReport.status);
            writer.WriteLine("second_deliberate_missing_take="+negativeReport.models[0].missingSourceTakes[0]);
            writer.WriteLine("distinct_original_sample_guids="+healthyId+";"+negativeId);
            writer.WriteLine("real_importer_report_status="+project.status);
            writer.WriteLine("original_Unity_demo_prefabs_and_scene_dependencies=PASS");
            writer.WriteLine("reference_omission_detected=PASS");
            writer.WriteLine("default_auto_mode_no_false_warning=PASS");
            writer.WriteLine("normal_split_clip_not_false_warning=PASS");
            writer.WriteLine("ambiguous_missing_oversized_invalid_fail_closed=PASS");
        }
        Debug.Log("HPR_SOURCE_TAKE_PROBE_SUCCESS "+string.Join(";",names));
    }
}
#endif
