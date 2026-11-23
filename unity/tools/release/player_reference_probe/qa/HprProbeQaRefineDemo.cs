#if UNITY_EDITOR
using System;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using HPR.PlayerReferenceProbe;

// PRIVATE visual correction of the original first-party scene. Preserve original archive and GUIDs.
public static class HprProbeQaRefineDemo
{
    const string Demo="Assets/HPRPlayerReferenceProbe/Demo/Scenes/HPR_Player_Reference_Probe_Demo.unity";
    private static void Require(bool good,string reason)
    {if(!good)throw new InvalidOperationException("HPR_FIRST_PARTY_DEMO_REFINEMENT_FAIL:"+reason);}
    private static void Change(TextMesh mesh,string content,Vector3 position,float scale)
    {
        mesh.text=content;
        mesh.characterSize=scale;
        mesh.transform.position=position;
        EditorUtility.SetDirty(mesh);
    }
    public static void Run()
    {
        const string safe="/data/var/marketplace-account-setup/unity-player-reference-probe-20261123-wave63/";
        string root=Environment.GetEnvironmentVariable("HPR_DEMO_REFINE_ROOT")??"";
        Require(Application.isBatchMode && root.StartsWith(safe,StringComparison.Ordinal) &&
            AssetDatabase.LoadAssetAtPath<SceneAsset>(Demo)!=null,
            "original_first_party_scene_imported_not_synthetic");
        var scene=EditorSceneManager.OpenScene(Demo,OpenSceneMode.Single);
        Require(scene.rootCount==13,"expected_original_scene_layout_not_independent_customer_content");
        var all=scene.GetRootGameObjects().SelectMany(go=>go.GetComponentsInChildren<TextMesh>(true)).ToArray();
        Require(all.Length==5,"five_original_TextMesh_label_assets_not_extra_content");
        foreach(var mesh in all)
        {
            switch(mesh.text)
            {
                case "PLAYER REFERENCE PROBE":
                    Change(mesh,"PLAYER REFERENCE PROBE",new Vector3(0f,3.22f,0f),.090f);break;
                case "REAL UNITY EDITOR  /  BUILT PLAYER":
                    Change(mesh,"EDITOR REFERENCES  /  BUILT PLAYER REFERENCES",
                        new Vector3(0f,2.72f,0f),.057f);break;
                case "ASSIGNED":
                    Change(mesh,"PREFAB ASSIGNED",new Vector3(-2.35f,-.95f,-1.9f),.076f);break;
                case "INTENTIONALLY EMPTY":
                    Change(mesh,"OPTIONAL FIELD EMPTY",new Vector3(2.35f,-.95f,-1.9f),.067f);break;
                case "Open Tools  >  HPR  >  Player Reference Probe":
                    Change(mesh,"SELECT PROBE IN HIERARCHY  /  TOOLS  /  HPR",
                        new Vector3(0f,-1.74f,-1.9f),.050f);break;
                default: throw new InvalidOperationException("Unexpected first-party sample label: "+mesh.text);
            }
        }
        var probe=scene.GetRootGameObjects()
            .SelectMany(go=>go.GetComponentsInChildren<HprPlayerReferenceProbe>(true)).SingleOrDefault();
        Require(probe!=null && probe.checks.Length==2 &&
            probe.checks.All(v=>v.source==null),
            "original_source_preserves_non_pinning_two_case_probes");
        EditorSceneManager.MarkSceneDirty(scene);
        Require(EditorSceneManager.SaveScene(scene,Demo),"revised_actual_unity_scene_saved");
        AssetDatabase.SaveAssets();
        Debug.Log("HPR_FIRST_PARTY_DEMO_REAL_NATIVE_LAYOUT_REFINEMENT_PASS "+
            Application.unityVersion+" root_objects="+scene.rootCount);
    }
}
#endif
