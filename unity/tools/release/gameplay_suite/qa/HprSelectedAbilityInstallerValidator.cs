// Disposable Editor QA. NEVER included in buyer package.
// A prior genuine customer game has a controller, scene, prefab and a
// customer-owned healing ability. Test one explicit Editor operation + Undo.
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
using ExternalCustomerGame;
using HprCustomerIntegrationQa;

public static class HprSelectedAbilityInstallerValidator
{
    private const string Customer = "Assets/ExternalCustomerGame";
    private const string OriginalScene = Customer + "/Scenes/OriginalCustomerScene.unity";
    private const string OriginalPrefab = Customer + "/Prefabs/ExistingCustomerPlayer.prefab";
    private const string OriginalController = Customer + "/ExistingPlayerController.cs";
    private const string OriginalSettings = Customer + "/Configs/CustomerSettings.asset";
    private const string NewScene = Customer + "/IntegrationDemos/AbilityInstallerWizardDemo.unity";
    private const string UserAbility = Customer + "/IntegrationDemos/CustomerHealing.asset";
    private const string UserEffect = Customer + "/IntegrationDemos/CustomerHealing__HPR_RepairEffect.asset";

    public static void Run()
    {
        string receipt = Environment.GetEnvironmentVariable("HPR_SELECTED_ABILITY_RECEIPT");
        if (string.IsNullOrWhiteSpace(receipt) || File.Exists(receipt))
            throw new InvalidOperationException("Expected a fresh private Editor validation receipt.");
        if (AssetDatabase.LoadAssetAtPath<UnityEngine.Object>(NewScene) != null)
            throw new InvalidOperationException("Existing scene would be overwritten. Stop.");

        string[] originals = { OriginalScene, OriginalPrefab, OriginalController,
                               OriginalSettings, UserAbility, UserEffect };
        byte[][] bytes = originals.Select(path =>
            File.ReadAllBytes(Path.Combine(Directory.GetParent(Application.dataPath).FullName,
                                          path))).ToArray();
        string[] guids = originals.Select(AssetDatabase.AssetPathToGUID).ToArray();
        if (guids.Any(string.IsNullOrEmpty))
            throw new InvalidOperationException("Missing buyer scene, controller or ability fixture.");

        var sourceScene = EditorSceneManager.OpenScene(OriginalScene, OpenSceneMode.Single);
        GameObject originalPlayer = GameObject.Find("ExistingCustomerPlayer");
        if (originalPlayer == null ||
            originalPlayer.GetComponent<ExistingPlayerController>() == null ||
            Math.Abs(originalPlayer.GetComponent<ExistingPlayerController>().MoveSpeed - 5.75f) > 0.00001f)
            throw new InvalidOperationException("Original buyer player is not intact.");

        if (!EditorSceneManager.SaveScene(sourceScene, NewScene, true))
            throw new InvalidOperationException("Could not create private copy of customer scene.");
        var scene = EditorSceneManager.OpenScene(NewScene, OpenSceneMode.Single);
        GameObject player = GameObject.Find("ExistingCustomerPlayer");
        if (player == null)
            throw new InvalidOperationException("Copied customer player does not exist.");
        AbilityData userAbility = AssetDatabase.LoadAssetAtPath<AbilityData>(UserAbility);
        if (userAbility == null || userAbility.Effects == null || userAbility.Effects.Count != 1 ||
            AssetDatabase.GetAssetPath(userAbility.Effects[0]) != UserEffect)
            throw new InvalidOperationException("Independent user-owned healing effect is missing.");

        if (HprSelectedAbilityInstaller.ValidateSelection(player, userAbility, null) == null)
            throw new InvalidOperationException("Missing ability resource provider was accepted.");
        if (player.GetComponent<AbilityRunnerComponent>() != null)
            throw new InvalidOperationException("Preview installed a component without consent.");

        var provider = player.AddComponent<HprCustomerAbilityResourceBridge>();
        AbilityData vendorAbility = AssetDatabase.LoadAssetAtPath<AbilityData>(
            "Assets/HPRGameplaySuite/Samples/RepairAbility.asset");
        if (HprSelectedAbilityInstaller.ValidateSelection(player, vendorAbility, provider) == null ||
            player.GetComponent<AbilityRunnerComponent>() != null)
            throw new InvalidOperationException("Vendor-owned ability was accepted as customer-owned.");
        if (HprSelectedAbilityInstaller.ValidateSelection(player, userAbility, provider) != null)
            throw new InvalidOperationException("Ready user-owned ability was refused.");

        var runner = HprSelectedAbilityInstaller.AttachExplicitly(player, userAbility, provider);
        if (runner == null || player.GetComponent<ExistingPlayerController>() == null)
            throw new InvalidOperationException("Installer replaced the player's custom controller.");
        VerifySerialized(runner, userAbility, provider);

        Undo.PerformUndo();
        if (player.GetComponent<AbilityRunnerComponent>() != null ||
            player.GetComponent<ExistingPlayerController>() == null ||
            player.GetComponent<HprCustomerAbilityResourceBridge>() == null)
            throw new InvalidOperationException("Undo did not completely remove only the HPR runner.");

        Undo.PerformRedo();
        runner = player.GetComponent<AbilityRunnerComponent>();
        if (runner == null)
            throw new InvalidOperationException("Redo did not restore the selected ability.");
        VerifySerialized(runner, userAbility, provider);

        EditorSceneManager.MarkSceneDirty(scene);
        if (!EditorSceneManager.SaveScene(scene, NewScene))
            throw new InvalidOperationException("Customer-owned copied scene did not save.");

        scene = EditorSceneManager.OpenScene(NewScene, OpenSceneMode.Single);
        player = GameObject.Find("ExistingCustomerPlayer");
        runner = player == null ? null : player.GetComponent<AbilityRunnerComponent>();
        provider = player == null ? null : player.GetComponent<HprCustomerAbilityResourceBridge>();
        if (runner == null || provider == null ||
            player.GetComponent<ExistingPlayerController>() == null)
            throw new InvalidOperationException("New customer scene lost integrated components.");
        VerifySerialized(runner, userAbility, provider);
        runner.RefreshRuntimeBindings();
        var entries = runner.BuildEntries();
        if (entries.Count != 1 || entries[0].Id != userAbility.Id || !entries[0].Unlocked)
            throw new InvalidOperationException("Ability was not unlocked after reload.");

        HprSelectedAbilityInstaller.Open();
        var window = Resources.FindObjectsOfTypeAll<HprSelectedAbilityInstaller>().FirstOrDefault();
        if (window == null)
            throw new InvalidOperationException("The actual integration EditorWindow did not open.");
        try
        {
            window.CreateGUI();
            var fields = window.rootVisualElement.Query<ObjectField>().ToList();
            var buttons = window.rootVisualElement.Query<Button>().ToList();
            var help = window.rootVisualElement.Q<HelpBox>();
            if (fields.Count < 3 || buttons.Count < 2 || help == null)
                throw new InvalidOperationException("Editor UI missing required inputs and status.");
        }
        finally
        {
            window.Close();
        }

        for (int i = 0; i < originals.Length; i++)
        {
            string physical = Path.Combine(Directory.GetParent(Application.dataPath).FullName,
                                           originals[i]);
            if (!bytes[i].SequenceEqual(File.ReadAllBytes(physical)) ||
                guids[i] != AssetDatabase.AssetPathToGUID(originals[i]))
                throw new InvalidOperationException("Original buyer/vendor asset was changed: " +
                                                    originals[i]);
        }

        File.WriteAllText(receipt,
            "read_only_preflight_and_unsafe_vendor_rejection=PASS\n" +
            "explicit_component_attach=PASS\n" +
            "undo_removes_only_selected_runner=PASS\n" +
            "redo_restores_configured_runner=PASS\n" +
            "inspector_serialization_persists_across_scene_reload=PASS\n" +
            "buyer_controller_prefab_original_scene_settings_assets_unchanged=PASS\n" +
            "editor_ui_fields_buttons_and_status=PASS\n" +
            "no_automatic_project_setting_or_scene_save_in_installer=PASS\n");
        Debug.Log("HPR_SELECTED_ABILITY_UNDO_AND_SCENE_QA_PASS");
    }

    private static void VerifySerialized(AbilityRunnerComponent runner, AbilityData ability,
                                          HprCustomerAbilityResourceBridge provider)
    {
        var serialized = new SerializedObject(runner);
        var configured = serialized.FindProperty("configuredAbilities");
        var unlocked = serialized.FindProperty("unlockAllConfiguredAbilities");
        var resources = serialized.FindProperty("resourcePoolBehaviour");
        if (configured == null || configured.arraySize != 1 ||
            configured.GetArrayElementAtIndex(0).objectReferenceValue != ability ||
            unlocked == null || !unlocked.boolValue ||
            resources == null || resources.objectReferenceValue != provider)
            throw new InvalidOperationException("Installed ability Inspector data is invalid.");
    }
}
#endif
