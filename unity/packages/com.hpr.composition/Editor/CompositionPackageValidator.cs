namespace HPR
{
    #if UNITY_EDITOR
    using System.Linq;
    using UnityEditor.SceneManagement;
    using UnityEngine;
    using UnityEngine.SceneManagement;

    public static class CompositionPackageValidator
    {
        private const string ScenePath = "Packages/com.hpr.composition/Demo/CompositionDemo.unity";

        public static void ValidateInBatch()
        {
            CompositionDemoSceneBuilder.BuildDemoScene();
            EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);

            var controller = SceneManager
                .GetActiveScene()
                .GetRootGameObjects()
                .Select(root => root.GetComponentInChildren<CompositionDemoController>(true))
                .FirstOrDefault(candidate => candidate != null);
            if (controller == null)
            {
                throw new System.InvalidOperationException("Composition demo scene is missing CompositionDemoController.");
            }

            controller.ValidateDemo();
            Debug.Log("CompositionPackageValidator: OK");
        }
    }
    #endif
}
