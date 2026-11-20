using System;
using System.IO;
using System.Linq;
using HPR;
using HPR.GameplaySuite.Experimental;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace HPR.Qa.RunnerDependency
{
    // Stage the buyer fixture outside Editor and this verifier inside Editor in a fresh QA project.
    public static class RunnerDependencyVerifier
    {
        private const string ScenePath = "Assets/HprRunnerDependencyFixture.unity";

        private static void Check(bool condition, string message)
        {
            if (!condition)
                throw new InvalidOperationException(message);
        }

        public static void Run()
        {
            Check(Application.isBatchMode && !File.Exists(ScenePath) && !File.Exists(ScenePath + ".meta"),
                "Use a fresh batch QA project with an unused fixture scene path.");
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var guarded = new GameObject("Customer caster");
            var customer = guarded.AddComponent<BuyerCastingController>();
            customer.enabled = false;
            var requiredRunner = guarded.GetComponent<AbilityRunnerComponent>();
            Check(requiredRunner != null && guarded.GetComponent<BoxCollider>() != null &&
                guarded.GetComponent<Rigidbody>() != null, "Unity did not install the inherited requirements.");

            var free = new GameObject("Player with independent components");
            var collider = free.AddComponent<BoxCollider>();
            var optionalRunner = free.AddComponent<AbilityRunnerComponent>();
            var serialized = new SerializedObject(optionalRunner);
            serialized.FindProperty("effectOrigin").objectReferenceValue = guarded.transform;
            Check(serialized.ApplyModifiedPropertiesWithoutUndo(), "Runner configuration did not apply.");
            Check(EditorSceneManager.SaveScene(scene, ScenePath), "Could not save the fixture.");
            var saved = File.ReadAllBytes(ScenePath);

            int group = Undo.GetCurrentGroup();
            string reason = HprSelectedAbilityInstaller.ValidateRemoval(guarded);
            Check(reason != null && reason.Contains(nameof(BuyerCastingController)),
                "Preview did not identify the dependent customer controller.");
            try
            {
                HprSelectedAbilityInstaller.RemoveExplicitly(guarded);
                throw new InvalidOperationException("Explicit removal accepted a required runner.");
            }
            catch (ArgumentException error)
            {
                Check(error.Message == reason, "The explicit action and preview disagree.");
            }
            Check(guarded.GetComponent<AbilityRunnerComponent>() == requiredRunner &&
                guarded.GetComponent<BuyerCastingController>() == customer && !customer.enabled,
                "Refused removal changed a buyer component.");
            Check(!scene.isDirty && Undo.GetCurrentGroup() == group, "Refused removal dirtied the scene or changed Undo.");

            Check(HprSelectedAbilityInstaller.ValidateRemoval(free) == null, "Independent runner was blocked.");
            Check(HprSelectedAbilityInstaller.RemoveExplicitly(free) && free.GetComponent<AbilityRunnerComponent>() == null &&
                free.GetComponent<BoxCollider>() == collider, "Regular removal changed the wrong components.");
            Undo.PerformUndo();
            var restored = free.GetComponent<AbilityRunnerComponent>();
            Check(restored != null && restored.EffectOrigin == guarded.transform, "Undo lost the runner configuration.");
            Undo.PerformRedo();
            Check(free.GetComponent<AbilityRunnerComponent>() == null && free.GetComponent<BoxCollider>() == collider,
                "Redo did not remove just the independent runner.");
            Check(saved.SequenceEqual(File.ReadAllBytes(ScenePath)), "The installer wrote to the saved scene.");

            Check(EditorSceneManager.SaveScene(scene), "Could not save the explicit removal.");
            EditorSceneManager.OpenScene(ScenePath);
            guarded = GameObject.Find("Customer caster");
            free = GameObject.Find("Player with independent components");
            customer = guarded.GetComponent<BuyerCastingController>();
            Check(customer != null && !customer.enabled && guarded.GetComponent<AbilityRunnerComponent>() != null &&
                free.GetComponent<AbilityRunnerComponent>() == null && free.GetComponent<BoxCollider>() != null,
                "Saved scene lost the buyer setup.");
            Debug.Log("HPR_RUNNER_DEPENDENCY_PASS inherited requirement, blocked action, clean scene and Undo group, " +
                "independent removal, configured Undo, Redo and saved scene reload");
        }
    }
}
