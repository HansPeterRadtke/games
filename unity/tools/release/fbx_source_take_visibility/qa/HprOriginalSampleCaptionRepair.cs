#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

// Private authoring QA: edits only two original first-party prefabs in a fresh
// disposable Unity project, preserving stable authored prefab/FBX GUIDs.
public static class HprOriginalSampleCaptionRepair
{
    private static void Require(bool okay,string name)
    { if(!okay)throw new InvalidOperationException("HPR_ORIGINAL_CAPTION_REPAIR_FAILURE:"+name); }

    private static string RepairOne(string name,string label)
    {
        string path="Assets/HPRFbxSourceTakes/Samples/Prefabs/"+name+".prefab";
        string originalGuid=AssetDatabase.AssetPathToGUID(path);
        Require(!String.IsNullOrEmpty(originalGuid),"original_native_prefab_guid_"+name);
        GameObject root=PrefabUtility.LoadPrefabContents(path);
        Require(root!=null,"actual_Unity_prefab_contents_loaded_"+name);
        try
        {
            TextMesh[] captions=root.GetComponentsInChildren<TextMesh>(true);
            Require(captions.Length==1,"exactly_one_original_caption_"+name);
            TextMesh caption=captions[0];
            caption.text=label;
            caption.characterSize=0.068f;
            caption.fontSize=48;
            caption.anchor=TextAnchor.MiddleCenter;
            caption.alignment=TextAlignment.Center;
            caption.transform.localPosition=new Vector3(0f,1.95f,0f);
            GameObject saved=PrefabUtility.SaveAsPrefabAsset(root,path);
            Require(saved!=null,"actual_Unity_prefab_saved_"+name);
        }
        finally{PrefabUtility.UnloadPrefabContents(root);}
        AssetDatabase.ImportAsset(path,ImportAssetOptions.ForceSynchronousImport);
        Require(AssetDatabase.AssetPathToGUID(path)==originalGuid,"prefab_GUID_unchanged_"+name);
        GameObject updated=AssetDatabase.LoadAssetAtPath<GameObject>(path);
        Require(updated!=null && updated.GetComponentsInChildren<TextMesh>(true).Length==1 &&
            updated.GetComponentsInChildren<TextMesh>(true)[0].text==label,
            "actual_Unity_prefab_new_label_persisted_"+name);
        string[] deps=AssetDatabase.GetDependencies(path,true);
        Require(deps.Any(x=>x.StartsWith("Assets/HPRFbxSourceTakes/Samples/HPRTwoTake",StringComparison.Ordinal)
                           && x.EndsWith(".fbx",StringComparison.OrdinalIgnoreCase)),
            "prefab_still_references_first_party_animated_FBX_"+name);
        return path+"|"+originalGuid+"|"+label.Replace('\n',' ');
    }

    public static void Run()
    {
        string path=Environment.GetEnvironmentVariable("HPR_ORIGINAL_CAPTION_REPAIR_QA_OUT")??"";
        Require(Application.isBatchMode && Path.IsPathRooted(path) &&
            path.StartsWith("/data/var/marketplace-account-setup/unity-20261122-wave55/",StringComparison.Ordinal) &&
            !File.Exists(path),"fresh_private_receipt");
        string a=RepairOne("OriginalAutoTwoTake","AUTO IMPORT\n2 takes available");
        string b=RepairOne("OriginalConfiguredMissingTake","CUSTOM IMPORT\n1 take unlisted");
        const string scene="Assets/HPRFbxSourceTakes/Samples/Scenes/SourceTakeVisibilityDemo.unity";
        var dependencies=AssetDatabase.GetDependencies(scene,true);
        Require(dependencies.Contains("Assets/HPRFbxSourceTakes/Samples/Prefabs/OriginalAutoTwoTake.prefab") &&
            dependencies.Contains("Assets/HPRFbxSourceTakes/Samples/Prefabs/OriginalConfiguredMissingTake.prefab"),
            "original_scene_still_references_same_prefab_GUIDs");
        using(var f=new FileStream(path,FileMode.CreateNew,FileAccess.Write,FileShare.None))
        using(var wr=new StreamWriter(f))
        {
            wr.WriteLine("unity_version="+Application.unityVersion);
            wr.WriteLine("healthy_original_prefab="+a);
            wr.WriteLine("warning_original_prefab="+b);
            wr.WriteLine("original_prefab_GUID_and_FBX_mesh_dependencies_preserved=PASS");
            wr.WriteLine("native_Unity_short_two_line_centered_labels=PASS");
            wr.WriteLine("scene_prefab_references_preserved=PASS");
        }
        Debug.Log("HPR_ORIGINAL_TWO_PREFAB_CAPTION_REPAIR_PASS");
    }
}
#endif
