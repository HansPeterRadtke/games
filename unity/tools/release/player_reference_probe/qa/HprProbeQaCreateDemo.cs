#if UNITY_EDITOR
using System;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using HPR.PlayerReferenceProbe;
using HPR.PlayerReferenceProbe.Demo;

// Original first-party Unity-authored sample assets. PRIVATE author utility, excluded from retail.
public static class HprProbeQaCreateDemo
{
    const string Root="Assets/HPRPlayerReferenceProbe/Demo";
    const string Materials=Root+"/Materials";
    const string ResourcesFolder=Root+"/Resources/HPRSample";
    const string Scenes=Root+"/Scenes";
    public const string ScenePath=Scenes+"/HPR_Player_Reference_Probe_Demo.unity";

    private static void Require(bool okay,string message)
    {if(!okay)throw new InvalidOperationException("HPR_DEMO_AUTHOR_FAIL:"+message);}
    private static void MakeFolder(string parent,string name)
    {
        string folder=parent+"/"+name;
        if(!AssetDatabase.IsValidFolder(folder))
            AssetDatabase.CreateFolder(parent,name);
        Require(AssetDatabase.IsValidFolder(folder),"original_folder_"+name);
    }
    private static Material MakeMaterial(string name,Color color,float metallic=0f)
    {
        var shader=Shader.Find("Standard");
        if(shader==null)shader=Shader.Find("Universal Render Pipeline/Lit");
        Require(shader!=null,"built_in_lit_shader_present");
        var mat=new Material(shader){name=name};
        if(mat.HasProperty("_Color"))mat.SetColor("_Color",color);
        if(mat.HasProperty("_BaseColor"))mat.SetColor("_BaseColor",color);
        if(mat.HasProperty("_Metallic"))mat.SetFloat("_Metallic",metallic);
        AssetDatabase.CreateAsset(mat,Materials+"/"+name+".mat");
        return mat;
    }
    private static GameObject Box(string name,Vector3 pos,Vector3 size,Material mat)
    {
        var obj=GameObject.CreatePrimitive(PrimitiveType.Cube);
        obj.name=name;
        obj.transform.position=pos;
        obj.transform.localScale=size;
        obj.GetComponent<MeshRenderer>().sharedMaterial=mat;
        return obj;
    }
    private static void Text(string content,Vector3 at,float scale,Color color)
    {
        var label=new GameObject("HPR Scene Label | "+content.Replace('\n',' '));
        label.transform.position=at;
        label.transform.rotation=Quaternion.Euler(0f,0f,0f);
        var text=label.AddComponent<TextMesh>();
        text.text=content;
        text.anchor=TextAnchor.MiddleCenter;
        text.alignment=TextAlignment.Center;
        text.fontSize=72;
        text.characterSize=scale;
        text.color=color;
    }

    public static void Run()
    {
        const string safe="/data/var/marketplace-account-setup/unity-player-reference-probe-20261123-wave63/";
        string output=Environment.GetEnvironmentVariable("HPR_DEMO_AUTHOR_ROOT")??"";
        Require(Application.isBatchMode && output.StartsWith(safe,StringComparison.Ordinal) &&
            AssetDatabase.IsValidFolder(Root) && !AssetDatabase.IsValidFolder(Scenes) &&
            AssetDatabase.LoadAssetAtPath<SceneAsset>(ScenePath)==null,
            "fresh_private_original_author_only");

        MakeFolder(Root,"Materials");
        MakeFolder(Root,"Resources");
        MakeFolder(Root+"/Resources","HPRSample");
        MakeFolder(Root,"Scenes");

        var stage=MakeMaterial("HPR_Stage",new Color(.08f,.12f,.20f),.1f);
        var stand=MakeMaterial("HPR_Stand",new Color(.20f,.30f,.40f),.32f);
        var blue=MakeMaterial("HPR_Assigned_Reference",new Color(.13f,.78f,.83f),.18f);
        var amber=MakeMaterial("HPR_Intentional_Empty",new Color(.92f,.52f,.15f),.14f);

        var prefabObject=Box("HPR_Original_Demo_Prefab",Vector3.zero,
            new Vector3(.7f,.7f,.7f),blue);
        var prefab=PrefabUtility.SaveAsPrefabAsset(prefabObject,
            ResourcesFolder+"/HPR_Demo_Reference.prefab");
        Require(prefab!=null,"original_primitive_prefab_saved_to_Resources");
        UnityEngine.Object.DestroyImmediate(prefabObject);

        var assigned=ScriptableObject.CreateInstance<HprPlayerReferenceDemoItem>();
        assigned.name="HPR_Assigned_Demo_Item";
        assigned.itemPrefab=prefab;assigned.label="Assigned reference";
        AssetDatabase.CreateAsset(assigned,ResourcesFolder+"/AssignedItem.asset");
        var optional=ScriptableObject.CreateInstance<HprPlayerReferenceDemoItem>();
        optional.name="HPR_Intentionally_Empty_Demo_Item";
        optional.itemPrefab=null;optional.label="Intentionally empty";
        AssetDatabase.CreateAsset(optional,ResourcesFolder+"/OptionalItem.asset");
        EditorUtility.SetDirty(assigned);
        EditorUtility.SetDirty(optional);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
        Require(AssetDatabase.LoadAssetAtPath<HprPlayerReferenceDemoItem>(
            ResourcesFolder+"/AssignedItem.asset")?.itemPrefab!=null,
            "saved_ScriptableObject_references_original_prefab");

        var scene=EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
        var cameraGO=new GameObject("HPR Demo Camera");
        var camera=cameraGO.AddComponent<Camera>();
        camera.clearFlags=CameraClearFlags.SolidColor;
        camera.backgroundColor=new Color(.055f,.095f,.145f);
        camera.orthographic=true;
        camera.orthographicSize=4.05f;
        camera.nearClipPlane=.2f;
        camera.farClipPlane=100f;
        cameraGO.tag="MainCamera";
        cameraGO.transform.position=new Vector3(0f,3.3f,-12.5f);
        cameraGO.transform.LookAt(new Vector3(0f,.65f,0f));
        var lightGO=new GameObject("HPR Original Key Light");
        var light=lightGO.AddComponent<Light>();
        light.type=LightType.Directional;
        light.intensity=1.35f;
        light.shadows=LightShadows.Soft;
        lightGO.transform.rotation=Quaternion.Euler(45f,-33f,0f);

        Box("HPR Demo Stage — geometry only",new Vector3(0f,-.26f,0f),
            new Vector3(10f,.2f,3.7f),stage);
        Box("HPR Working Sample Pedestal",new Vector3(-2.35f,.12f,.0f),
            new Vector3(2.7f,.54f,2.25f),stand);
        Box("HPR Empty Sample Pedestal",new Vector3(2.35f,.12f,.0f),
            new Vector3(2.7f,.54f,2.25f),stand);
        Box("HPR Assigned Cube — real referenced prefab",new Vector3(-2.35f,1.25f,0f),
            new Vector3(1.4f,1.4f,1.4f),blue);
        Box("HPR Empty Place Indicator",new Vector3(2.35f,.65f,.0f),
            new Vector3(.90f,.12f,.90f),amber);
        Text("PLAYER REFERENCE PROBE",new Vector3(0f,3.22f,0f),.090f,Color.white);
        Text("EDITOR REFERENCES  /  BUILT PLAYER REFERENCES",new Vector3(0f,2.72f,0f),.057f,
            new Color(.78f,.84f,.92f));
        Text("ASSIGNED",new Vector3(-2.35f,-.95f,-1.9f),.088f,Color.white);
        Text("EMPTY",new Vector3(2.35f,-.95f,-1.9f),.088f,Color.white);
        Text("SELECT PROBE IN HIERARCHY  /  TOOLS  /  HPR",new Vector3(0f,-1.74f,-1.9f),.050f,
            new Color(.72f,.83f,.89f));

        var inspectorGO=new GameObject("HPR | Reference Probe (select me)");
        var inspector=inspectorGO.AddComponent<HprPlayerReferenceProbe>();
        inspector.checks=new[]{
            new HprReferenceCase{id="demo-assigned",source=null,
                resourcesPath="HPRSample/AssignedItem",fieldName="itemPrefab"},
            new HprReferenceCase{id="demo-intentionally-empty",source=null,
                resourcesPath="HPRSample/OptionalItem",fieldName="itemPrefab"}
        };
        inspector.writePrivateLocalReport=true;
        Require(EditorSceneManager.SaveScene(scene,ScenePath),"original_demo_scene_saved");
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
        Require(AssetDatabase.LoadAssetAtPath<SceneAsset>(ScenePath)!=null,
            "serialized_original_demo_scene_imported");
        Require(AssetDatabase.LoadAssetAtPath<GameObject>(ResourcesFolder+"/HPR_Demo_Reference.prefab")!=null,
            "saved_first_party_prefab_exists");
        Debug.Log("HPR_PLAYER_REFERENCE_ORIGINAL_DEMO_AUTHOR_PASS objects="+
            scene.rootCount+" unity="+Application.unityVersion);
    }
}
#endif
