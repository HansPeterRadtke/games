namespace HPR
{
    #if UNITY_EDITOR
    using System.Linq;
    using UnityEditor.SceneManagement;
    using UnityEngine;
    using UnityEngine.SceneManagement;

    public static class InventoryPackageValidator
    {
        private const string ScenePath = "Packages/com.hpr.inventory/Demo/InventoryDemo.unity";

        public static void ValidateInBatch()
        {
            InventoryDemoSceneBuilder.BuildDemoScene();
            EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);

            var controller = SceneManager
                .GetActiveScene()
                .GetRootGameObjects()
                .Select(root => root.GetComponentInChildren<InventoryDemoController>(true))
                .FirstOrDefault(candidate => candidate != null);
            if (controller == null)
            {
                throw new System.InvalidOperationException("Inventory demo scene is missing InventoryDemoController.");
            }

            controller.ValidateDemo();
            Debug.Log("InventoryPackageValidator: OK");
        }
    }
    #endif
}
