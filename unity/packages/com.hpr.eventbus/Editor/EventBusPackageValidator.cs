namespace HPR
{
    #if UNITY_EDITOR
    using System.Linq;
    using UnityEditor.SceneManagement;
    using UnityEngine;
    using UnityEngine.SceneManagement;

    public static class EventBusPackageValidator
    {
        private const string ScenePath = "Packages/com.hpr.eventbus/Demo/EventBusDemo.unity";

        public static void ValidateInBatch()
        {
            EventBusDemoSceneBuilder.BuildDemoScene();
            EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);

            var roots = SceneManager.GetActiveScene().GetRootGameObjects();
            var eventManager = roots
                .Select(root => root.GetComponentInChildren<EventManager>(true))
                .FirstOrDefault(candidate => candidate != null);
            var controller = roots
                .Select(root => root.GetComponentInChildren<EventBusDemoController>(true))
                .FirstOrDefault(candidate => candidate != null);
            if (eventManager == null)
            {
                throw new System.InvalidOperationException("Event bus demo scene is missing EventManager.");
            }

            if (controller == null)
            {
                throw new System.InvalidOperationException("Event bus demo scene is missing EventBusDemoController.");
            }

            controller.EnsureSubscriptions();
            controller.PublishPing();
            controller.PublishStatus();

            if (controller.PingCount != 1)
            {
                throw new System.InvalidOperationException($"Expected one ping event, got {controller.PingCount}.");
            }

            if (controller.StatusCount != 1)
            {
                throw new System.InvalidOperationException($"Expected one status event, got {controller.StatusCount}.");
            }

            if (controller.Entries.Count < 2)
            {
                throw new System.InvalidOperationException("Event bus demo did not record the published events.");
            }

            Debug.Log("EventBusPackageValidator: OK");
        }
    }
    #endif
}
