#if UNITY_EDITOR
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class StatsDemoSceneBuilder
{
    private const string ScenePath = "Packages/com.hpr.stats/Demo/StatsDemo.unity";
    private const string TempSceneDirectory = "Assets/__GeneratedPackageDemos";
    private const string TempScenePath = "Assets/__GeneratedPackageDemos/StatsDemo.unity";

    [MenuItem("HPR/Stats/Build Demo Scene")]
    public static void BuildDemoScene()
    {
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        var root = new GameObject("StatsDemoRoot");
        root.AddComponent<EventManager>();
        root.AddComponent<EventBusSourceAdapter>();

        var target = new GameObject("StatsTarget");
        target.transform.SetParent(root.transform);
        target.transform.position = Vector3.zero;
        var stats = target.AddComponent<ActorStatsComponent>();
        var statsSerialized = new SerializedObject(stats);
        statsSerialized.FindProperty("eventBusSourceBehaviour").objectReferenceValue = root.GetComponent<EventBusSourceAdapter>();
        statsSerialized.ApplyModifiedPropertiesWithoutUndo();

        var camera = new GameObject("Main Camera");
        camera.tag = "MainCamera";
        camera.transform.position = new Vector3(0f, 0f, -10f);
        camera.AddComponent<Camera>();

        var controllerGo = new GameObject("StatsDemoController");
        var controller = controllerGo.AddComponent<StatsDemoController>();
        var so = new SerializedObject(controller);
        so.FindProperty("targetStats").objectReferenceValue = target.GetComponent<ActorStatsComponent>();
        so.FindProperty("eventManager").objectReferenceValue = root.GetComponent<EventManager>();
        so.ApplyModifiedPropertiesWithoutUndo();

        Directory.CreateDirectory(Path.GetDirectoryName(TempScenePath) ?? "Assets");
        EditorSceneManager.SaveScene(scene, TempScenePath);
        AssetDatabase.Refresh();

        var sourceAbsolutePath = Path.GetFullPath(Path.Combine(Application.dataPath, "..", TempScenePath));
        var targetAbsolutePath = Path.GetFullPath(Path.Combine(Application.dataPath, "..", ScenePath));
        Directory.CreateDirectory(Path.GetDirectoryName(targetAbsolutePath) ?? Path.GetFullPath(Path.Combine(Application.dataPath, "..")));
        File.Copy(sourceAbsolutePath, targetAbsolutePath, true);

        var sourceMetaPath = $"{sourceAbsolutePath}.meta";
        var targetMetaPath = $"{targetAbsolutePath}.meta";
        if (File.Exists(sourceMetaPath))
        {
            File.Copy(sourceMetaPath, targetMetaPath, true);
        }

        AssetDatabase.DeleteAsset(TempScenePath);
        AssetDatabase.DeleteAsset(TempSceneDirectory);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log($"Stats demo scene written to {ScenePath}");
    }
}
#endif
