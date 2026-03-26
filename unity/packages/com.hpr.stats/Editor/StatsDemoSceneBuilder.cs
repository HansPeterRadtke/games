#if UNITY_EDITOR
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class StatsDemoSceneBuilder
{
    private const string ScenePath = "Packages/com.hpr.stats/Demo/StatsDemo.unity";

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
        target.AddComponent<ActorStatsComponent>();

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

        EditorSceneManager.SaveScene(scene, ScenePath);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log($"Stats demo scene written to {ScenePath}");
    }
}
#endif
