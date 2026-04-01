namespace HPR
{
    #if UNITY_EDITOR
    using System.Linq;
    using UnityEditor.SceneManagement;
    using UnityEngine;
    using UnityEngine.SceneManagement;

    public static class SavePackageValidator
    {
        private const string ScenePath = "Packages/com.hpr.save/Demo/SaveDemo.unity";

        public static void ValidateInBatch()
        {
            SaveDemoSceneBuilder.BuildDemoScene();
            EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);

            var controller = SceneManager
                .GetActiveScene()
                .GetRootGameObjects()
                .Select(root => root.GetComponentInChildren<SaveDemoController>(true))
                .FirstOrDefault(candidate => candidate != null);
            if (controller == null)
            {
                throw new System.InvalidOperationException("Save demo scene is missing SaveDemoController.");
            }

            controller.ValidateDemo();
            Debug.Log("SavePackageValidator: OK");
        }
    }
    #endif
}
