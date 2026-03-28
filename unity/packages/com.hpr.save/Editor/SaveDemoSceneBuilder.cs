#if UNITY_EDITOR
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class SaveDemoSceneBuilder
{
    private const string ScenePath = "Packages/com.hpr.save/Demo/SaveDemo.unity";
    private const string TempSceneDirectory = "Assets/__GeneratedPackageDemos";
    private const string TempScenePath = "Assets/__GeneratedPackageDemos/SaveDemo.unity";

    [MenuItem("HPR/Save/Build Demo Scene")]
    public static void BuildDemoScene()
    {
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        var cameraGo = new GameObject("Main Camera");
        cameraGo.tag = "MainCamera";
        cameraGo.transform.position = new Vector3(0f, 2.5f, -7f);
        cameraGo.transform.rotation = Quaternion.Euler(14f, 0f, 0f);
        cameraGo.AddComponent<Camera>();

        var lightGo = new GameObject("Directional Light");
        lightGo.transform.rotation = Quaternion.Euler(50f, -30f, 0f);
        lightGo.AddComponent<Light>().type = LightType.Directional;

        var entityGo = GameObject.CreatePrimitive(PrimitiveType.Cube);
        entityGo.name = "SaveEntity";
        entityGo.transform.position = new Vector3(1f, 2f, 3f);
        var entity = entityGo.AddComponent<SaveDemoEntity>();

        var controllerGo = new GameObject("SaveDemoController");
        var controller = controllerGo.AddComponent<SaveDemoController>();
        var serialized = new SerializedObject(controller);
        serialized.FindProperty("entity").objectReferenceValue = entity;
        serialized.ApplyModifiedPropertiesWithoutUndo();

        Directory.CreateDirectory(Path.GetDirectoryName(TempScenePath) ?? "Assets");
        EditorSceneManager.SaveScene(scene, TempScenePath);
        AssetDatabase.Refresh();

        var sourceAbsolutePath = Path.GetFullPath(Path.Combine(Application.dataPath, "..", TempScenePath));
        var targetAbsolutePath = Path.GetFullPath(Path.Combine(Application.dataPath, "..", ScenePath));
        Directory.CreateDirectory(Path.GetDirectoryName(targetAbsolutePath) ?? Path.GetFullPath(Path.Combine(Application.dataPath, "..")));
        File.Copy(sourceAbsolutePath, targetAbsolutePath, true);

        var sourceMetaPath = $"{sourceAbsolutePath}.meta";
        var targetMetaPath = $"{targetAbsolutePath}.meta";
        if (!File.Exists(targetMetaPath) && File.Exists(sourceMetaPath))
        {
            File.Copy(sourceMetaPath, targetMetaPath, false);
        }

        AssetDatabase.DeleteAsset(TempScenePath);
        AssetDatabase.DeleteAsset(TempSceneDirectory);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log($"Save demo scene written to {ScenePath}");
    }
}
#endif
