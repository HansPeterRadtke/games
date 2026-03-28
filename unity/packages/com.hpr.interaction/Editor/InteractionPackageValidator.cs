#if UNITY_EDITOR
using System.Linq;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

public static class InteractionPackageValidator
{
    private const string ScenePath = "Packages/com.hpr.interaction/Demo/InteractionDemo.unity";

    public static void ValidateInBatch()
    {
        InteractionDemoSceneBuilder.BuildDemoScene();
        EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);

        var controller = SceneManager
            .GetActiveScene()
            .GetRootGameObjects()
            .Select(root => root.GetComponentInChildren<InteractionDemoController>(true))
            .FirstOrDefault(candidate => candidate != null);
        if (controller == null)
        {
            throw new System.InvalidOperationException("Interaction demo scene is missing InteractionDemoController.");
        }

        controller.ValidateDemo();
        Debug.Log("InteractionPackageValidator: OK");
    }
}
#endif
