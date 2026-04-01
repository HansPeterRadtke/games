namespace HPR
{
    #if UNITY_EDITOR
    using System.IO;
    using UnityEditor;
    using UnityEditor.SceneManagement;
    using UnityEngine;

    public static class EventBusDemoSceneBuilder
    {
        private const string ScenePath = "Packages/com.hpr.eventbus/Demo/EventBusDemo.unity";
        private const string TempSceneDirectory = "Assets/__GeneratedPackageDemos";
        private const string TempScenePath = "Assets/__GeneratedPackageDemos/EventBusDemo.unity";

        [MenuItem("Tools/HPR/EventBus/Build Demo Scene")]
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
            Debug.Log($"Event bus demo scene written to {ScenePath}");
        }
    }
    #endif
}
