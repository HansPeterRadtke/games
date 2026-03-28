#if UNITY_EDITOR
using System.Linq;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

public static class AiPackageValidator
{
    private const string ScenePath = "Packages/com.hpr.ai/Demo/AiDemo.unity";

    public static void ValidateInBatch()
    {
        AiDemoSceneBuilder.BuildDemoScene();
        EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);

        var controller = SceneManager
            .GetActiveScene()
            .GetRootGameObjects()
            .Select(root => root.GetComponentInChildren<AiDemoController>(true))
            .FirstOrDefault(candidate => candidate != null);
        if (controller == null)
        {
            throw new System.InvalidOperationException("AI demo scene is missing AiDemoController.");
        }

        controller.ValidateDemo();
        Debug.Log("AiPackageValidator: OK");
    }
}
#endif
