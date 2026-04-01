namespace HPR
{
    #if UNITY_EDITOR
    using System.Linq;
    using UnityEditor.SceneManagement;
    using UnityEngine;
    using UnityEngine.SceneManagement;

    public static class StatsPackageValidator
    {
        private const string ScenePath = "Packages/com.hpr.stats/Demo/StatsDemo.unity";

        public static void ValidateInBatch()
        {
            StatsDemoSceneBuilder.BuildDemoScene();
            EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);

            var controller = SceneManager
                .GetActiveScene()
                .GetRootGameObjects()
                .Select(root => root.GetComponentInChildren<StatsDemoController>(true))
                .FirstOrDefault(candidate => candidate != null);
            if (controller == null)
            {
                throw new System.InvalidOperationException("Stats demo scene is missing StatsDemoController.");
            }

            controller.ValidateDemo();
            Debug.Log("StatsPackageValidator: OK");
        }
    }
    #endif
}
