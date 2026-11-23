#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using HPR.ImportedPrefabParity;

// PRIVATE genuine buyer QA. Synthetic negative copies are modified only in memory.
public static class HprPrefabParityNativeQa
{
    private static void Require(bool yes,string rule)
    {if(!yes)throw new InvalidOperationException("HPR_PREFAB_NATIVE_QA_FAILURE:"+rule);}
    public static void Run()
    {
        string destination=Environment.GetEnvironmentVariable("HPR_PREFAB_NATIVE_RECEIPT")??"";
        const string safe="/data/var/marketplace-account-setup/unity-prefab-dependency-20261123-wave61/";
        Require(Application.isBatchMode && Path.IsPathRooted(destination) &&
            destination.StartsWith(safe,StringComparison.Ordinal) && !File.Exists(destination),
            "private_create_only_scoped_receipt");
        string originals="Assets/HPRFbxClipIdentity/Samples/Prefabs/OriginalMotionTeachingPrefab.prefab;"+
            "Assets/HPRFbxSourceTakes/Samples/Prefabs/OriginalAutoTwoTake.prefab;"+
            "Assets/HPRFbxSourceTakes/Samples/Prefabs/OriginalConfiguredMissingTake.prefab";
        Require(HprPrefabStateScan.ValidatePaths(originals.Replace(';','\n')).Length==3,
            "original_multiline_editor_paths_validate_as_distinct_prefabs");
        var result=HprPrefabStateScan.Scan(originals);
        Require(!result.incomplete && result.status=="CAPTURED_COVERED_PREFAB_VALUES" &&
            result.inputs.Length==3 && result.valuesCaptured>=45 && result.schema==2 &&
            result.dependencies.Length>=1 &&
            result.unsupportedComponents==0 &&
            result.values.Any(v=>v.key.EndsWith("/sharedMesh")) &&
            result.values.Any(v=>v.key.EndsWith("/text")),
            "native_three_original_first_party_prefabs_loaded");
        Require(result.values.Any(x=>x.key.EndsWith("Transform/position")) &&
            result.values.All(x=>x.value!=null),"original_imported_transform_and_component_values");
        var canceled=HprPrefabStateScan.Scan(originals,(i,n)=>true);
        Require(canceled.incomplete && canceled.failureReason.Contains("Canceled"),
            "native_cancel_is_incomplete_not_clean");
        // Native evidence keeps any unverified built-in/package dependency warning.
        // Synthetic field-difference controls deliberately use two *copies* with
        // those paths removed; they are not presented as real buyer clean evidence.
        var clean=JsonUtility.FromJson<HprPrefabReceipt>(JsonUtility.ToJson(result));
        clean.unverifiedDependencyPaths=new string[0];
        var clone=JsonUtility.FromJson<HprPrefabReceipt>(JsonUtility.ToJson(clean));
        clone.unityVersion="synthetic-other-editor-QA";
        var same=HprPrefabStateCompare.Compare(clean,clone);
        Require(same.status=="MATCHED_COVERED_IMPORTED_PREFAB_VALUES" &&
            same.changedValueKeys.Length==0,"same_original_input_no_fake_difference");
        clone.values[0].value=clone.values[0].value+"-synthetic-change";
        var changed=HprPrefabStateCompare.Compare(clean,clone);
        Require(changed.status=="REVIEW_IMPORTED_PREFAB_VALUE_DIFFERENCES" &&
            changed.changedValueKeys.Length==1 && changed.sourceDifferences.Length==0,
            "same_source_original_value_modified_in_memory_detected");
        // Deliberately modify only an isolated copy of the referenced original FBX
        // metadata fingerprint; the prefab itself and loaded properties remain intact.
        var dependencyChanged=JsonUtility.FromJson<HprPrefabReceipt>(JsonUtility.ToJson(clean));
        dependencyChanged.unityVersion="synthetic-other-editor-referenced-dependency-QA";
        dependencyChanged.dependencies[0].sourceSha256=new string('0',64);
        if(dependencyChanged.dependencies[0].sourceSha256==result.dependencies[0].sourceSha256)
            dependencyChanged.dependencies[0].sourceSha256=new string('1',64);
        var dependencyReview=HprPrefabStateCompare.Compare(clean,dependencyChanged);
        Require(dependencyReview.status=="DEPENDENCY_INPUTS_DIFFER_NO_EDITOR_INFERENCE" &&
            dependencyReview.dependencyDifferences.Length==1 &&
            dependencyReview.sourceDifferences.Length==0 &&
            dependencyReview.changedValueKeys.Length==0,
            "same_prefab_but_modified_referenced_source_must_not_pass_clean");
        var metaChanged=JsonUtility.FromJson<HprPrefabReceipt>(JsonUtility.ToJson(clean));
        metaChanged.unityVersion="synthetic-other-editor-dependency-meta-QA";
        metaChanged.dependencies[0].metaSha256=new string('0',64);
        if(metaChanged.dependencies[0].metaSha256==result.dependencies[0].metaSha256)
            metaChanged.dependencies[0].metaSha256=new string('1',64);
        var metaReview=HprPrefabStateCompare.Compare(clean,metaChanged);
        Require(metaReview.status=="DEPENDENCY_INPUTS_DIFFER_NO_EDITOR_INFERENCE" &&
            metaReview.dependencyDifferences.Length==1,
            "same_prefab_but_modified_dependency_importer_meta_must_not_pass_clean");
        var unknownChanged=JsonUtility.FromJson<HprPrefabReceipt>(JsonUtility.ToJson(clean));
        unknownChanged.unityVersion="synthetic-other-editor-unverified-dependency-QA";
        unknownChanged.unverifiedDependencyPaths=new[]{"Packages/com.vendor.sample/Unknown.asset"};
        var unknownReview=HprPrefabStateCompare.Compare(clean,unknownChanged);
        Require(unknownReview.status=="DEPENDENCIES_UNVERIFIED_NO_EDITOR_INFERENCE" &&
            unknownReview.unverifiedDependencyPaths.Length>0,
            "unverified_package_dependency_must_not_pass_clean");
        var oldVersion=JsonUtility.FromJson<HprPrefabReceipt>(JsonUtility.ToJson(clean));
        oldVersion.schema=1;
        bool oldRejected=false;
        try{HprPrefabStateCompare.Compare(clean,oldVersion);}
        catch(ArgumentException){oldRejected=true;}
        Require(oldRejected,"old_receipt_without_dependency_evidence_rejected");
        var sourceChanged=JsonUtility.FromJson<HprPrefabReceipt>(JsonUtility.ToJson(clean));
        sourceChanged.unityVersion="synthetic-other-source-QA";
        sourceChanged.inputs[0].sourceSha256=new string('0',64);
        if(sourceChanged.inputs[0].sourceSha256==result.inputs[0].sourceSha256)
            sourceChanged.inputs[0].sourceSha256=new string('1',64);
        var compared=HprPrefabStateCompare.Compare(clean,sourceChanged);
        Require(compared.status=="SOURCE_BYTES_DIFFER_NO_EDITOR_INFERENCE" &&
            compared.sourceDifferences.Length==1,
            "different_original_source_cannot_implicate_Unity_engine");
        HprPrefabStateScan.ExportNew(result,destination);
        bool blocked=false;
        try{HprPrefabStateScan.ExportNew(result,destination);}catch(IOException){blocked=true;}
        Require(blocked,"create_only_refuses_original_overwrite");
        Debug.Log("HPR_PREFAB_STATE_PARITY_NATIVE_PASS "+Application.unityVersion+
            " real_prefabs="+result.inputs.Length+" captured_values="+result.valuesCaptured+
            " hashed_dependencies="+result.dependencies.Length+
            " unverified_dependencies="+result.unverifiedDependencyPaths.Length+
            " uncovered_component_types="+result.unsupportedComponents);
    }
}
#endif
