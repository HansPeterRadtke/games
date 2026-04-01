namespace HPR
{
    #if UNITY_EDITOR
    using System.IO;
    using UnityEditor;
    using UnityEditor.SceneManagement;
    using UnityEngine;

    public static class CompositionDemoSceneBuilder
    {
        private const string ScenePath = "Packages/com.hpr.composition/Demo/CompositionDemo.unity";
        private const string TempSceneDirectory = "Assets/__GeneratedPackageDemos";
        private const string TempScenePath = "Assets/__GeneratedPackageDemos/CompositionDemo.unity";

        [MenuItem("Tools/HPR/Composition/Build Demo Scene")]
        public static void BuildDemoScene()
        {
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            var cameraGo = new GameObject("Main Camera");
            cameraGo.tag = "MainCamera";
            cameraGo.transform.position = new Vector3(0f, 0f, -10f);
            cameraGo.AddComponent<Camera>();

            var root = new GameObject("CompositionDemoRoot");
            root.AddComponent<CompositionDemoController>();

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
            Debug.Log($"Composition demo scene written to {ScenePath}");
        }
    }
    #endif
}
