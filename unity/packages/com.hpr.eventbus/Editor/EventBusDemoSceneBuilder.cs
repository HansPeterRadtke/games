#if UNITY_EDITOR
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class EventBusDemoSceneBuilder
{
    private const string ScenePath = "Packages/com.hpr.eventbus/Demo/EventBusDemo.unity";

    [MenuItem("HPR/EventBus/Build Demo Scene")]
    public static void BuildDemoScene()
    {
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        var root = new GameObject("EventBusDemoRoot");
        var eventManager = root.AddComponent<EventManager>();
        root.AddComponent<EventBusSourceAdapter>();

        var cameraGo = new GameObject("Main Camera");
        cameraGo.tag = "MainCamera";
        cameraGo.transform.position = new Vector3(0f, 0f, -10f);
        cameraGo.AddComponent<Camera>();

        var controllerGo = new GameObject("EventBusDemoController");
        var controller = controllerGo.AddComponent<EventBusDemoController>();
        var so = new SerializedObject(controller);
        so.FindProperty("eventManager").objectReferenceValue = eventManager;
        so.ApplyModifiedPropertiesWithoutUndo();

        EditorSceneManager.SaveScene(scene, ScenePath);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log($"Event bus demo scene written to {ScenePath}");
    }
}
#endif
