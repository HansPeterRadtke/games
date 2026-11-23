#if UNITY_EDITOR
using System;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using HPR.PlayerReferenceProbe;

// PRIVATE first-party correction of the visual labels from an already native-authored scene.
public static class HprProbeQaRefineLabelsV2
{
    const string ScenePath="Assets/HPRPlayerReferenceProbe/Demo/Scenes/HPR_Player_Reference_Probe_Demo.unity";
    private static void Require(bool ok,string why)
    {if(!ok)throw new InvalidOperationException("HPR_DEMO_LABEL_CORRECTION_FAILURE:"+why);}
    public static void Run()
    {
        const string safe="/data/var/marketplace-account-setup/unity-player-reference-probe-20261123-wave63/";
        var root=Environment.GetEnvironmentVariable("HPR_DEMO_REFINE_ROOT")??"";
        Require(Application.isBatchMode && root.StartsWith(safe,StringComparison.Ordinal),
            "private_first_party_author_scope");
        var scene=EditorSceneManager.OpenScene(ScenePath,OpenSceneMode.Single);
        Require(scene.isLoaded && scene.rootCount==13,"original_unchanged_first_party_scene");
        var labels=scene.GetRootGameObjects().SelectMany(x=>x.GetComponentsInChildren<TextMesh>(true)).ToArray();
        Require(labels.Length==5,"original_five_label_objects");
        var left=labels.SingleOrDefault(x=>x.text=="PREFAB ASSIGNED");
        var right=labels.SingleOrDefault(x=>x.text=="OPTIONAL FIELD EMPTY");
        Require(left!=null && right!=null,"original_overlong_labels_current");
        left.text="ASSIGNED";
        right.text="EMPTY";
        left.characterSize=.088f;
        right.characterSize=.088f;
        left.transform.position=new Vector3(-2.35f,-.95f,-1.9f);
        right.transform.position=new Vector3(2.35f,-.95f,-1.9f);
        left.gameObject.name="HPR Scene Label | ASSIGNED";
        right.gameObject.name="HPR Scene Label | EMPTY";
        var selected=scene.GetRootGameObjects().SelectMany(g=>g.GetComponentsInChildren<HprPlayerReferenceProbe>(true)).ToArray();
        Require(selected.Length==1 && selected[0].checks.Length==2 &&
            selected[0].checks.All(c=>c.source==null && c.resourcesPath.StartsWith("HPRSample/")),
            "sample_player_reference_cases_preserved_without_source_pinning");
        EditorUtility.SetDirty(left);
        EditorUtility.SetDirty(right);
        EditorSceneManager.MarkSceneDirty(scene);
        Require(EditorSceneManager.SaveScene(scene,ScenePath),"real_editor_save_scene");
        AssetDatabase.SaveAssets();
        Debug.Log("HPR_DEMO_LABELS_V2_ORIGINAL_UNITY_EDITOR_PASS scene="+ScenePath+
            " editor="+Application.unityVersion);
    }
}
#endif
