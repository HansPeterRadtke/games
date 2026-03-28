#if UNITY_EDITOR
using System.Linq;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

public static class WorldPackageValidator
{
    private const string ScenePath = "Packages/com.hpr.world/Demo/WorldDemo.unity";

    public static void ValidateInBatch()
    {
        WorldDemoSceneBuilder.BuildDemoScene();
        EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);

        var controller = SceneManager
            .GetActiveScene()
            .GetRootGameObjects()
            .Select(root => root.GetComponentInChildren<WorldDemoController>(true))
            .FirstOrDefault(candidate => candidate != null);
        if (controller == null)
        {
            throw new System.InvalidOperationException("World demo scene is missing WorldDemoController.");
        }

        controller.ValidateDemo();
        Debug.Log("WorldPackageValidator: OK");
    }
}
#endif
