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
        const string safe="/data/var/marketplace-account-setup/unity-prefab-state-parity-20261122-wave59/";
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
            result.inputs.Length==3 && result.valuesCaptured>=45 && result.schema==1 &&
            result.unsupportedComponents==0 &&
            result.values.Any(v=>v.key.EndsWith("/sharedMesh")) &&
            result.values.Any(v=>v.key.EndsWith("/text")),
            "native_three_original_first_party_prefabs_loaded");
        Require(result.values.Any(x=>x.key.EndsWith("Transform/position")) &&
            result.values.All(x=>x.value!=null),"original_imported_transform_and_component_values");
        var canceled=HprPrefabStateScan.Scan(originals,(i,n)=>true);
        Require(canceled.incomplete && canceled.failureReason.Contains("Canceled"),
            "native_cancel_is_incomplete_not_clean");
        var clone=JsonUtility.FromJson<HprPrefabReceipt>(JsonUtility.ToJson(result));
        clone.unityVersion="synthetic-other-editor-QA";
        var same=HprPrefabStateCompare.Compare(result,clone);
        Require(same.status=="MATCHED_COVERED_IMPORTED_PREFAB_VALUES" &&
            same.changedValueKeys.Length==0,"same_original_input_no_fake_difference");
        clone.values[0].value=clone.values[0].value+"-synthetic-change";
        var changed=HprPrefabStateCompare.Compare(result,clone);
        Require(changed.status=="REVIEW_IMPORTED_PREFAB_VALUE_DIFFERENCES" &&
            changed.changedValueKeys.Length==1 && changed.sourceDifferences.Length==0,
            "same_source_original_value_modified_in_memory_detected");
        var sourceChanged=JsonUtility.FromJson<HprPrefabReceipt>(JsonUtility.ToJson(result));
        sourceChanged.unityVersion="synthetic-other-source-QA";
        sourceChanged.inputs[0].sourceSha256=new string('0',64);
        if(sourceChanged.inputs[0].sourceSha256==result.inputs[0].sourceSha256)
            sourceChanged.inputs[0].sourceSha256=new string('1',64);
        var compared=HprPrefabStateCompare.Compare(result,sourceChanged);
        Require(compared.status=="SOURCE_BYTES_DIFFER_NO_EDITOR_INFERENCE" &&
            compared.sourceDifferences.Length==1,
            "different_original_source_cannot_implicate_Unity_engine");
        HprPrefabStateScan.ExportNew(result,destination);
        bool blocked=false;
        try{HprPrefabStateScan.ExportNew(result,destination);}catch(IOException){blocked=true;}
        Require(blocked,"create_only_refuses_original_overwrite");
        Debug.Log("HPR_PREFAB_STATE_PARITY_NATIVE_PASS "+Application.unityVersion+
            " real_prefabs="+result.inputs.Length+" captured_values="+result.valuesCaptured+
            " uncovered_component_types="+result.unsupportedComponents);
    }
}
#endif
