// Real Unity Editor buyer-game detach and Undo QA. Private scratch-project only.
// Never include this validator in the Unity Asset Store buyer package.
#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEditor.UIElements;
using UnityEngine;
using UnityEngine.UIElements;
using HPR;
using HPR.GameplaySuite.Experimental;
using HprCustomerIntegrationQa;
using ExternalCustomerGame;

public static class HprSelectedAbilityDetachValidator
{
    private const string Root = "Assets/ExternalCustomerGame";
    private const string SourceScene = Root + "/IntegrationDemos/AbilityInstallerWizardDemo.unity";
    private const string DetachScene = Root + "/IntegrationDemos/AbilityDetachWizardQA.unity";
    private const string OriginalScene = Root + "/Scenes/OriginalCustomerScene.unity";
    private const string OriginalPrefab = Root + "/Prefabs/ExistingCustomerPlayer.prefab";
    private const string OriginalCode = Root + "/ExistingPlayerController.cs";
    private const string OriginalSettings = Root + "/Configs/CustomerSettings.asset";
    private const string OriginalAbility = Root + "/IntegrationDemos/CustomerHealing.asset";
    private const string OriginalEffect = Root + "/IntegrationDemos/CustomerHealing__HPR_RepairEffect.asset";

    public static void Run()
    {
        string receipt = Environment.GetEnvironmentVariable("HPR_SELECTED_ABILITY_DETACH_RECEIPT");
        if (string.IsNullOrWhiteSpace(receipt) || File.Exists(receipt))
            throw new InvalidOperationException("Require a previously unused private detach receipt.");
        if (AssetDatabase.LoadAssetAtPath<UnityEngine.Object>(DetachScene) != null ||
            File.Exists(Physical(DetachScene)))
            throw new InvalidOperationException("Refusing to replace an existing buyer scene.");

        string[] protectedOriginals = {
            SourceScene, OriginalScene, OriginalPrefab, OriginalCode,
            OriginalSettings, OriginalAbility, OriginalEffect,
            "ProjectSettings/InputManager.asset", "ProjectSettings/GraphicsSettings.asset",
            "Packages/manifest.json"
        };
        byte[][] before = protectedOriginals.Select(path => File.ReadAllBytes(Physical(path))).ToArray();
        string[] assetGuids = protectedOriginals
            .Where(path => path.StartsWith("Assets/", StringComparison.Ordinal))
            .Select(AssetDatabase.AssetPathToGUID).ToArray();
        if (assetGuids.Any(string.IsNullOrEmpty))
            throw new InvalidOperationException("Original customer-owned Unity metadata was missing");

        var source = EditorSceneManager.OpenScene(SourceScene, OpenSceneMode.Single);
        var originalPlayer = GameObject.Find("ExistingCustomerPlayer");
        if (originalPlayer == null ||
            originalPlayer.GetComponent<ExistingPlayerController>() == null ||
            originalPlayer.GetComponent<HprCustomerAbilityResourceBridge>() == null ||
            originalPlayer.GetComponent<AbilityRunnerComponent>() == null)
            throw new InvalidOperationException("Existing customer integration demo was not populated");
        if (!EditorSceneManager.SaveScene(source, DetachScene, true))
            throw new InvalidOperationException("Could not create independent buyer test scene");

        EditorSceneManager.OpenScene(DetachScene, OpenSceneMode.Single);
        var player = GameObject.Find("ExistingCustomerPlayer");
        var customer = player == null ? null : player.GetComponent<ExistingPlayerController>();
        var provider = player == null ? null : player.GetComponent<HprCustomerAbilityResourceBridge>();
        var runner = player == null ? null : player.GetComponent<AbilityRunnerComponent>();
        var ability = AssetDatabase.LoadAssetAtPath<AbilityData>(OriginalAbility);
        if (customer == null || provider == null || runner == null || ability == null ||
            Math.Abs(customer.MoveSpeed - 5.75f) > 0.0001f)
            throw new InvalidOperationException("Copy does not preserve original customer integration");
        var originalPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(OriginalPrefab);
        if (HprSelectedAbilityInstaller.ValidateRemoval(player) != null ||
            HprSelectedAbilityInstaller.ValidateRemoval(originalPrefab) == null ||
            HprSelectedAbilityInstaller.ValidateRemoval(GameObject.Find("Main Camera")) == null)
            throw new InvalidOperationException("Read-only removal gate failed scene/asset checks");

        var baseline = new SerializedObject(runner);
        if (!AbilityConfigured(baseline, ability, provider))
            throw new InvalidOperationException("Original installed ability was not configured");

        Selection.activeGameObject = player;
        HprSelectedAbilityInstaller.Open();
        var window = Resources.FindObjectsOfTypeAll<HprSelectedAbilityInstaller>().FirstOrDefault();
        if (window == null) throw new InvalidOperationException("Installed Editor window missing");
        try
        {
            window.CreateGUI();
            var remove = window.rootVisualElement.Query<Button>().ToList()
                .FirstOrDefault(button => button.text.Contains("Remove HPR runner"));
            if (remove == null || !remove.enabledInHierarchy)
                throw new InvalidOperationException("User cannot see enabled removal action");
        }
        finally { window.Close(); }

        if (!HprSelectedAbilityInstaller.RemoveExplicitly(player) ||
            player.GetComponent<AbilityRunnerComponent>() != null ||
            player.GetComponent<ExistingPlayerController>() != customer ||
            player.GetComponent<HprCustomerAbilityResourceBridge>() != provider)
            throw new InvalidOperationException("Explicit removal changed unrelated customer components");

        Undo.PerformUndo();
        runner = player.GetComponent<AbilityRunnerComponent>();
        if (runner == null || !AbilityConfigured(new SerializedObject(runner), ability, provider))
            throw new InvalidOperationException("Unity Undo did not fully restore the HPR ability");

        Undo.PerformRedo();
        if (player.GetComponent<AbilityRunnerComponent>() != null ||
            player.GetComponent<ExistingPlayerController>() == null ||
            player.GetComponent<HprCustomerAbilityResourceBridge>() == null)
            throw new InvalidOperationException("Unity Redo failed to reapply only the selected removal");

        var scene = EditorSceneManager.GetActiveScene();
        if (!EditorSceneManager.SaveScene(scene, DetachScene))
            throw new InvalidOperationException("Could not save the new customer-owned scene without HPR runner");
        EditorSceneManager.OpenScene(DetachScene, OpenSceneMode.Single);
        player = GameObject.Find("ExistingCustomerPlayer");
        if (player == null || player.GetComponent<AbilityRunnerComponent>() != null ||
            player.GetComponent<ExistingPlayerController>() == null ||
            player.GetComponent<HprCustomerAbilityResourceBridge>() == null)
            throw new InvalidOperationException("Removal did not persist in independently saved customer scene");

        int assetIndex = 0;
        for (int index = 0; index < protectedOriginals.Length; index++)
        {
            string path = protectedOriginals[index];
            if (!before[index].SequenceEqual(File.ReadAllBytes(Physical(path))))
                throw new InvalidOperationException("Original buyer file was changed: " + path);
            if (path.StartsWith("Assets/", StringComparison.Ordinal) &&
                assetGuids[assetIndex++] != AssetDatabase.AssetPathToGUID(path))
                throw new InvalidOperationException("Original customer GUID was changed: " + path);
        }

        File.WriteAllText(receipt,
            "single_instance_scene_removal_gate=PASS\n" +
            "prefab_asset_and_unrelated_object_rejected=PASS\n" +
            "explicit_runner_removal_keeps_customer_controller_and_resources=PASS\n" +
            "unity_undo_restores_serialized_ability_and_resource=PASS\n" +
            "unity_redo_removes_only_the_runner=PASS\n" +
            "new_buyer_scene_retains_removed_state_after_reload=PASS\n" +
            "original_customer_scene_prefab_source_settings_and_guids_preserved=PASS\n" +
            "real_installer_editor_window_shows_remove_action=PASS\n");
        Debug.Log("HPR_SELECTED_ABILITY_DETACH_UNDO_REDO_PASS");
        Selection.activeGameObject = null;
    }

    private static bool AbilityConfigured(SerializedObject runner,
                                          AbilityData ability,
                                          HprCustomerAbilityResourceBridge provider)
    {
        var configured = runner.FindProperty("configuredAbilities");
        var unlock = runner.FindProperty("unlockAllConfiguredAbilities");
        var resources = runner.FindProperty("resourcePoolBehaviour");
        return configured != null && configured.arraySize == 1 &&
            configured.GetArrayElementAtIndex(0).objectReferenceValue == ability &&
            unlock != null && unlock.boolValue &&
            resources != null && resources.objectReferenceValue == provider;
    }

    private static string Physical(string relative) =>
        Path.Combine(Directory.GetParent(Application.dataPath).FullName, relative);
}
#endif
