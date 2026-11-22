#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

// Private actual Unity validation for the original first-party three-root
// importer tools. This QA code is never exported to a customer package.
public static class HprOriginalAnimationGeometryQa
{
    private static void Check(bool condition,string name)
    { if(!condition)throw new InvalidOperationException("HPR_ORIGINAL_ANIMATION_GEOMETRY_QA_FAILURE: "+name); }

    private static void InspectModel(string source,string prefabPath,int takes,int custom)
    {
        var model=AssetDatabase.LoadAssetAtPath<GameObject>(source);
        var importer=AssetImporter.GetAtPath(source) as ModelImporter;
        Check(model!=null && importer!=null && importer.importAnimation,"original_fbx_asset_and_importer_"+source);
        Check(importer.defaultClipAnimations!=null && importer.defaultClipAnimations.Length==takes &&
              importer.clipAnimations!=null && importer.clipAnimations.Length==custom,
              "correct_source_take_configuration_"+source);
        var originalMesh=model.GetComponentsInChildren<MeshFilter>(true);
        Check(originalMesh.Length>0,"original_mesh_present_"+source);
        foreach(var mesh in originalMesh)
        {
            Check(mesh.sharedMesh!=null && mesh.sharedMesh.vertexCount>=8,
                "original_mesh_geometry_"+source);
            Check(Quaternion.Angle(mesh.transform.localRotation,Quaternion.identity)<0.05f,
                "identity_orientation_"+source);
            var s=mesh.transform.localScale;
            Check(Mathf.Abs(s.x-1f)<0.01f && Mathf.Abs(s.y-1f)<0.01f && Mathf.Abs(s.z-1f)<0.01f,
                "unit_model_scale_"+source);
        }
        var prefab=AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath);
        Check(prefab!=null,"Unity_authored_original_prefab_imported_"+prefabPath);
        var copyMeshes=prefab.GetComponentsInChildren<MeshFilter>(true);
        Check(copyMeshes.Length>=1 && copyMeshes.All(m=>m.sharedMesh!=null && m.sharedMesh.vertexCount>=8),
            "original_prefab_meshes_resolve_"+prefabPath);
        var dependencies=AssetDatabase.GetDependencies(prefabPath,true);
        Check(dependencies.Contains(source),"prefab_dependencies_include_own_FBX_"+prefabPath);
    }

    public static void Run()
    {
        string dest=Environment.GetEnvironmentVariable("HPR_ORIGINAL_ANIM_GEOMETRY_QA_OUT")??"";
        Check(Application.isBatchMode && Path.IsPathRooted(dest) &&
            dest.StartsWith("/data/var/marketplace-account-setup/unity-20261122-wave55/",StringComparison.Ordinal) &&
            !File.Exists(dest),"fresh_private_QA_path");
        InspectModel("Assets/HPRFbxClipIdentity/Samples/OriginalMotion.fbx",
            "Assets/HPRFbxClipIdentity/Samples/Prefabs/OriginalMotionTeachingPrefab.prefab",1,0);
        InspectModel("Assets/HPRFbxSourceTakes/Samples/HPRTwoTakeCube.fbx",
            "Assets/HPRFbxSourceTakes/Samples/Prefabs/OriginalAutoTwoTake.prefab",2,0);
        InspectModel("Assets/HPRFbxSourceTakes/Samples/HPRTwoTakeCustomMissing.fbx",
            "Assets/HPRFbxSourceTakes/Samples/Prefabs/OriginalConfiguredMissingTake.prefab",2,1);
        const string scene="Assets/HPRFbxSourceTakes/Samples/Scenes/SourceTakeVisibilityDemo.unity";
        Check(AssetDatabase.LoadAssetAtPath<SceneAsset>(scene)!=null,"original_demo_scene_imported");
        string[] deps=AssetDatabase.GetDependencies(scene,true);
        Check(deps.Contains("Assets/HPRFbxSourceTakes/Samples/Prefabs/OriginalAutoTwoTake.prefab") &&
            deps.Contains("Assets/HPRFbxSourceTakes/Samples/Prefabs/OriginalConfiguredMissingTake.prefab"),
            "real_scene_has_both_paired_original_model_prefabs");
        using(var stream=new FileStream(dest,FileMode.CreateNew,FileAccess.Write,FileShare.None))
        using(var writer=new StreamWriter(stream))
        {
            writer.WriteLine("unity_version="+Application.unityVersion);
            writer.WriteLine("original_clip_id_sample_identity_rotation_and_unit_scale=PASS");
            writer.WriteLine("original_source_take_healthy_sample_identity_rotation_and_unit_scale=PASS");
            writer.WriteLine("original_source_take_warning_sample_identity_rotation_and_unit_scale=PASS");
            writer.WriteLine("original_three_native_Unity_prefabs_have_real_FBX_mesh_references=PASS");
            writer.WriteLine("original_demo_scene_references_original_two_source_take_prefabs=PASS");
            writer.WriteLine("this_is_native_batch_mode_not_graphical_EditorWindow_QA=TRUE");
        }
        Debug.Log("HPR_ORIGINAL_COMBINED_GEOMETRY_QA_PASS");
    }
}
#endif
