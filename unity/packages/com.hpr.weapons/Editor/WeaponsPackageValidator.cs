namespace HPR
{
    #if UNITY_EDITOR
    using System.Linq;
    using UnityEditor.SceneManagement;
    using UnityEngine;
    using UnityEngine.SceneManagement;

    public static class WeaponsPackageValidator
    {
        private const string ScenePath = "Packages/com.hpr.weapons/Demo/WeaponsDemo.unity";

        public static void ValidateInBatch()
        {
            WeaponsDemoSceneBuilder.BuildDemoScene();
            EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);

            var controller = SceneManager
                .GetActiveScene()
                .GetRootGameObjects()
                .Select(root => root.GetComponentInChildren<WeaponsDemoController>(true))
                .FirstOrDefault(candidate => candidate != null);
            if (controller == null)
            {
                throw new System.InvalidOperationException("Weapons demo scene is missing WeaponsDemoController.");
            }

            controller.ValidateDemo();
            Debug.Log("WeaponsPackageValidator: OK");
        }
    }
    #endif
}
