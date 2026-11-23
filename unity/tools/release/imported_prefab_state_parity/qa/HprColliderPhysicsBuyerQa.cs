#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using HPR.ImportedPrefabParity;

// PRIVATE real Editor imported-archive scan; actual first-party physics fields.
public static class HprColliderPhysicsBuyerQa
{
    public const string Prefab="Assets/HPRColliderOriginal/CapsuleAndController.prefab";
    private static void Require(bool condition,string msg)
    {if(!condition)throw new InvalidOperationException("HPR_COLLIDER_BUYER_FAIL:"+msg);}
    public static void Run()
    {
        const string safe="/data/var/marketplace-account-setup/unity-player-reference-probe-20261123-wave63/";
        string output=Environment.GetEnvironmentVariable("HPR_COLLIDER_BUYER_REPORT")??"";
        Require(Application.isBatchMode && Path.IsPathRooted(output) &&
            output.StartsWith(safe,StringComparison.Ordinal) && !File.Exists(output),
            "private_create_only_receipt");
        var asset=AssetDatabase.LoadAssetAtPath<GameObject>(Prefab);
        Require(asset!=null && PrefabUtility.GetPrefabAssetType(asset)==PrefabAssetType.Regular,
            "real_independently_installed_original_first_party_physics_prefab");
        GameObject loaded=null;
        try
        {
            loaded=PrefabUtility.LoadPrefabContents(Prefab);
            Require(loaded!=null,"real_prefab_loaded_in_isolated_scene");
            var capsule=loaded.GetComponent<CapsuleCollider>();
            var controller=loaded.GetComponentInChildren<CharacterController>(true);
            Require(capsule!=null && controller!=null,"actual_capsule_and_controller_components");
            Require(Mathf.Abs(capsule.radius-.67f)<.00001f &&
                Mathf.Abs(capsule.height-2.75f)<.00001f && capsule.direction==2 &&
                Mathf.Abs(controller.radius-.41f)<.00001f &&
                Mathf.Abs(controller.height-1.85f)<.00001f &&
                Mathf.Abs(controller.slopeLimit-46f)<.00001f &&
                Mathf.Abs(controller.stepOffset-.24f)<.00001f &&
                Mathf.Abs(controller.skinWidth-.04f)<.00001f,
                "actual_imported_source_physics_dimensions_match_original");
        }
        finally{if(loaded!=null)PrefabUtility.UnloadPrefabContents(loaded);}
        var report=HprPrefabStateScan.Scan(Prefab);
        Require(!report.incomplete && report.inputs.Length==1 &&
            report.unsupportedComponents==0 && report.unverifiedDependencyPaths.Length==0,
            "new_native_collider_geometry_covered_no_unknowns");
        var capsuleFields=report.values.Where(v=>v.key.Contains("CapsuleCollider")).ToArray();
        var charFields=report.values.Where(v=>v.key.Contains("CharacterController")).ToArray();
        Require(capsuleFields.Any(v=>v.key.EndsWith("/height") && v.value=="2.75") &&
            capsuleFields.Any(v=>v.key.EndsWith("/radius") && v.value=="0.67") &&
            capsuleFields.Any(v=>v.key.EndsWith("/direction") && v.value=="2") &&
            charFields.Any(v=>v.key.EndsWith("/height") && v.value=="1.85") &&
            charFields.Any(v=>v.key.EndsWith("/slopeLimit") && v.value=="46") &&
            charFields.Any(v=>v.key.EndsWith("/stepOffset") && v.value=="0.24"),
            "new_shape_fields_native_snapshotted_not_silently_ignored");
        var changed=JsonUtility.FromJson<HprPrefabReceipt>(JsonUtility.ToJson(report));
        changed.unityVersion="synthetic-different-editor-capsule-height-QA";
        var field=changed.values.Single(v=>v.key.Contains("CapsuleCollider") &&
            v.key.EndsWith("/height"));
        field.value="3.5";
        var result=HprPrefabStateCompare.Compare(report,changed);
        Require(result.status=="REVIEW_IMPORTED_PREFAB_VALUE_DIFFERENCES" &&
            result.changedValueKeys.Length==1 &&
            result.changedValueKeys[0].EndsWith("/height"),
            "changed_capsule_geometry_must_be_detected_instead_of_silent_clean");
        HprPrefabStateScan.ExportNew(report,output);
        Debug.Log("HPR_COLLIDER_PHYSICS_BUYER_NATIVE_PASS "+Application.unityVersion+
            " covered_values="+report.valuesCaptured+
            " capsule_fields="+capsuleFields.Length+" character_fields="+charFields.Length+
            " changed_capsule_height_detected=TRUE");
    }
}
#endif
