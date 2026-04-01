namespace HPR
{
    #if UNITY_EDITOR
    using System.Linq;
    using UnityEditor.SceneManagement;
    using UnityEngine;
    using UnityEngine.SceneManagement;

    public static class AbilitiesPackageValidator
    {
        private const string ScenePath = "Packages/com.hpr.abilities/Demo/AbilitiesDemo.unity";

        public static void ValidateInBatch()
        {
            AbilitiesDemoSceneBuilder.BuildDemoScene();
            EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);

            var controller = SceneManager
                .GetActiveScene()
                .GetRootGameObjects()
                .Select(root => root.GetComponentInChildren<AbilitiesDemoController>(true))
                .FirstOrDefault(candidate => candidate != null);
            if (controller == null)
            {
                throw new System.InvalidOperationException("Abilities demo scene is missing AbilitiesDemoController.");
            }

            controller.ValidateDemo();
            Debug.Log("AbilitiesPackageValidator: OK");
        }
    }
    #endif
}
