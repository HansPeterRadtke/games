#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

// PRIVATE source authoring tool. Creates only original first-party prefab and
// demonstration scene assets inside a brand-new disposable author project.
// The source-only QA utility itself must never ship in a buyer archive.
public static class HprFbxDemoSceneAuthor
{
    private const string Root = "Assets/HPRFbxSourceTakes/Samples";
    private static GameObject Model(string path)
    {
        var asset=AssetDatabase.LoadAssetAtPath<GameObject>(path);
        if(asset==null)throw new InvalidOperationException("Original imported Unity FBX missing: "+path);
        return asset;
    }
    private static string Prefab(string modelPath, string name, string caption)
    {
        string path=Root+"/Prefabs/"+name+".prefab";
        if(File.Exists(Path.Combine(Directory.GetParent(Application.dataPath).FullName,path)))
            throw new IOException("Original vendor prefab already exists; refuse overwrite");
        var root=new GameObject(name);
        try
        {
            var model=(GameObject)PrefabUtility.InstantiatePrefab(Model(modelPath));
            if(model==null)throw new InvalidOperationException("Original imported model instance missing");
            model.name="Original Blender Animated Cube";
            model.transform.SetParent(root.transform,false);
            model.transform.localPosition=Vector3.zero;
            model.transform.localRotation=Quaternion.identity;
            var guide=new GameObject("Read Me - "+caption);
            guide.transform.SetParent(root.transform,false);
            guide.transform.localPosition=new Vector3(0,1.95f,0);
            var label=guide.AddComponent<TextMesh>();
            label.text=caption; label.anchor=TextAnchor.MiddleCenter;
            label.alignment=TextAlignment.Center;label.characterSize=0.068f;
            label.fontSize=48;
            var result=PrefabUtility.SaveAsPrefabAsset(root,path);
            if(result==null) throw new InvalidOperationException("PrefabUtility did not create original prefab");
            return path;
        }
        finally{UnityEngine.Object.DestroyImmediate(root);}
    }
    public static void Generate()
    {
        string receipt=Environment.GetEnvironmentVariable("HPR_SOURCE_TAKE_DEMO_AUTHOR_RECEIPT") ?? "";
        if(!Application.isBatchMode || !Path.IsPathRooted(receipt) ||
           !receipt.StartsWith("/data/var/marketplace-account-setup/unity-20261122-wave55/",StringComparison.Ordinal) ||
           !receipt.EndsWith(".txt",StringComparison.Ordinal) || File.Exists(receipt))
            throw new InvalidOperationException("New original private Unity demo author receipt required.");
        if(!AssetDatabase.IsValidFolder(Root) || !AssetDatabase.LoadMainAssetAtPath(Root+"/HPRTwoTakeCube.fbx"))
            throw new InvalidOperationException("Fresh original two-take Blender project source not installed");
        if(!AssetDatabase.IsValidFolder(Root+"/Prefabs"))
            AssetDatabase.CreateFolder(Root,"Prefabs");
        if(!AssetDatabase.IsValidFolder(Root+"/Scenes"))
            AssetDatabase.CreateFolder(Root,"Scenes");
        string healthy=Prefab(Root+"/HPRTwoTakeCube.fbx","OriginalAutoTwoTake","AUTO IMPORT\n2 takes available");
        string warning=Prefab(Root+"/HPRTwoTakeCustomMissing.fbx","OriginalConfiguredMissingTake",
            "CUSTOM IMPORT\n1 take unlisted");
        const string sceneFile = Root+"/Scenes/SourceTakeVisibilityDemo.unity";
        var absoluteScene=Path.Combine(Directory.GetParent(Application.dataPath).FullName,sceneFile);
        if(File.Exists(absoluteScene))throw new IOException("Refusing to replace any existing demo scene");
        var scene=EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
        var cameraObj=new GameObject("Main Camera - Original FBX Demo");
        cameraObj.tag="MainCamera";
        var camera=cameraObj.AddComponent<Camera>();
        camera.clearFlags=CameraClearFlags.Skybox;
        camera.fieldOfView=54f;camera.nearClipPlane=0.3f;camera.farClipPlane=200f;
        cameraObj.transform.position=new Vector3(0,3f,-9f);
        cameraObj.transform.rotation=Quaternion.LookRotation(new Vector3(0,0.5f,0)-cameraObj.transform.position);
        var lightObj=new GameObject("Key Light");
        var lamp=lightObj.AddComponent<Light>();
        lamp.type=LightType.Directional;lamp.intensity=1.0f;
        lightObj.transform.rotation=Quaternion.Euler(55f,-25f,0f);
        var floor=GameObject.CreatePrimitive(PrimitiveType.Plane);
        floor.name="Neutral Ground - Demonstration Only";
        floor.transform.localScale=new Vector3(1.0f,1f,0.7f);
        floor.transform.position=new Vector3(0,-1,0);
        var a=PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(healthy)) as GameObject;
        var b=PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(warning)) as GameObject;
        if(a==null || b==null)throw new InvalidOperationException("Original demo prefabs missing");
        a.transform.position=new Vector3(-2.2f,0,0);b.transform.position=new Vector3(2.2f,0,0);
        if(!EditorSceneManager.SaveScene(scene,sceneFile,false))
            throw new IOException("Unity did not save original FBX source take demonstration scene");
        AssetDatabase.SaveAssets();AssetDatabase.Refresh();
        using(var file=new FileStream(receipt,FileMode.CreateNew,FileAccess.Write,FileShare.None))
        using(var writer=new StreamWriter(file))
        {
            writer.WriteLine("unity_version="+Application.unityVersion);
            foreach(var path in new[]{healthy,warning,sceneFile})
            {
                string guid=AssetDatabase.AssetPathToGUID(path);
                if(string.IsNullOrEmpty(guid))throw new InvalidOperationException("Missing authored Unity GUID for "+path);
                writer.WriteLine("original_asset="+path+"|"+guid);
            }
            writer.WriteLine("camera_and_key_light_and_two_model_prefab_instances=PASS");
            writer.WriteLine("source_take_EditorUI_itself_not_shown_in_the_demo_scene=TRUE");
        }
        Debug.Log("HPR_ORIGINAL_UNITY_SOURCE_TAKE_DEMO_CREATED");
    }
}
#endif
