// Private Unity Editor QA for a customer game with its own controller, scene, prefab
// and serialized settings. The existing game is never edited; a NEW scene and
// ability definitions are authored under a customer-owned folder in a scratch copy.
#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;
using HPR;
using HPR.GameplaySuite;
using HprCustomerIntegrationQa;
using ExternalCustomerGame;

public static class HprCustomerExistingGameAbilityValidator
{
    internal const string DemoRoot = "Assets/ExternalCustomerGame/IntegrationDemos";
    internal const string DemoScene = DemoRoot + "/ExistingGameWithHprHealing.unity";
    internal const string DemoAbility = DemoRoot + "/CustomerHealing.asset";
    internal const string DemoEffect = DemoRoot + "/CustomerHealing__HPR_RepairEffect.asset";
    internal const string OriginalScene = "Assets/ExternalCustomerGame/Scenes/OriginalCustomerScene.unity";
    internal const string OriginalPrefab = "Assets/ExternalCustomerGame/Prefabs/ExistingCustomerPlayer.prefab";
    internal const string OriginalController = "Assets/ExternalCustomerGame/ExistingPlayerController.cs";
    internal const string OriginalSettings = "Assets/ExternalCustomerGame/Configs/CustomerSettings.asset";
    private const string SourceAbility = "Assets/HPRGameplaySuite/Samples/RepairAbility.asset";
    private const string SourceEffect = "Assets/HPRGameplaySuite/Samples/RepairEffect.asset";

    public static void BuildCustomerDemo()
    {
        string receipt = Environment.GetEnvironmentVariable("HPR_EXTERNAL_ABILITY_BUILD_RECEIPT");
        if (string.IsNullOrWhiteSpace(receipt) || File.Exists(receipt))
            throw new InvalidOperationException("Expected a fresh private build receipt.");
        if (AssetDatabase.IsValidFolder(DemoRoot) ||
            AssetDatabase.LoadAssetAtPath<UnityEngine.Object>(DemoAbility) != null ||
            AssetDatabase.LoadAssetAtPath<UnityEngine.Object>(DemoScene) != null)
            throw new InvalidOperationException("Refusing to modify an existing customer demo.");

        string[] protectedPaths = { OriginalScene, OriginalPrefab, OriginalController,
                                    OriginalSettings, SourceAbility, SourceEffect };
        string[] protectedBytes = protectedPaths.Select(FileDigest).ToArray();
        string[] protectedGuids = protectedPaths.Select(AssetDatabase.AssetPathToGUID).ToArray();
        if (protectedGuids.Any(string.IsNullOrEmpty))
            throw new InvalidOperationException("The original fixture was not imported.");

        Scene original = EditorSceneManager.OpenScene(OriginalScene, OpenSceneMode.Single);
        var originalPlayer = GameObject.Find("ExistingCustomerPlayer");
        if (originalPlayer == null ||
            originalPlayer.GetComponent<ExistingPlayerController>() == null ||
            Math.Abs(originalPlayer.GetComponent<ExistingPlayerController>().MoveSpeed - 5.75f) > 0.0001f)
            throw new InvalidOperationException("The independent customer controller is missing.");

        if (AssetDatabase.CreateFolder("Assets/ExternalCustomerGame", "IntegrationDemos") == "")
            throw new InvalidOperationException("Unity could not make the new demo folder.");

        // Export a NEW scene without changing the active customer's original scene.
        if (!EditorSceneManager.SaveScene(original, DemoScene, true))
            throw new InvalidOperationException("Saving new customer scene copy failed.");
        Scene demo = EditorSceneManager.OpenScene(DemoScene, OpenSceneMode.Single);
        GameObject customerPlayer = GameObject.Find("ExistingCustomerPlayer");
        if (customerPlayer == null ||
            customerPlayer.GetComponent<ExistingPlayerController>() == null)
            throw new InvalidOperationException("Copied scene lost the customer's prefab instance.");

        var ability = HprSuiteIntegrationGuide.CopySampleToCustomerPath(SourceAbility, DemoAbility) as AbilityData;
        if (ability == null || ability.Effects.Count != 1 ||
            AssetDatabase.GetAssetPath(ability.Effects[0]) != DemoEffect ||
            ability.Id == AssetDatabase.LoadAssetAtPath<AbilityData>(SourceAbility).Id)
            throw new InvalidOperationException("User-owned ability/effect dependency was not cloned.");

        // Adds isolated optional components to the NEW scene instance; the original
        // customer prefab/controller are not modified or replaced.
        var bridge = customerPlayer.AddComponent<HprCustomerAbilityResourceBridge>();
        var runner = customerPlayer.AddComponent<AbilityRunnerComponent>();
        runner.ConfigureAbilities(new[] { ability });
        // Runtime SetUnlockedAbilityIds does NOT serialize the unlock state.
        // The explicit Inspector setting is the persistable authoring contract.
        var authored = new SerializedObject(runner);
        SerializedProperty unlockAll = authored.FindProperty("unlockAllConfiguredAbilities");
        if (unlockAll == null || unlockAll.propertyType != SerializedPropertyType.Boolean)
            throw new InvalidOperationException("Inspector unlock configuration is missing.");
        unlockAll.boolValue = true;
        authored.ApplyModifiedProperties();
        runner.BindRuntimeServices(null, bridge);
        EditorUtility.SetDirty(bridge);
        EditorUtility.SetDirty(runner);
        EditorSceneManager.MarkSceneDirty(demo);
        if (!EditorSceneManager.SaveScene(demo, DemoScene))
            throw new InvalidOperationException("New customer ability scene could not be saved.");

        demo = EditorSceneManager.OpenScene(DemoScene, OpenSceneMode.Single);
        customerPlayer = GameObject.Find("ExistingCustomerPlayer");
        runner = customerPlayer == null ? null : customerPlayer.GetComponent<AbilityRunnerComponent>();
        bridge = customerPlayer == null ? null : customerPlayer.GetComponent<HprCustomerAbilityResourceBridge>();
        if (runner == null || bridge == null ||
            customerPlayer.GetComponent<ExistingPlayerController>() == null)
            throw new InvalidOperationException("Saved demo did not retain all independent components.");
        runner.RefreshRuntimeBindings();
        var entries = runner.BuildEntries();
        if (entries.Count != 1 || entries[0].Id != ability.Id || !entries[0].Unlocked)
            throw new InvalidOperationException("Saved ability is not configured and unlocked.");

        for (int i = 0; i < protectedPaths.Length; i++)
            if (FileDigest(protectedPaths[i]) != protectedBytes[i] ||
                AssetDatabase.AssetPathToGUID(protectedPaths[i]) != protectedGuids[i])
                throw new InvalidOperationException("Customer or vendor original mutated: " + protectedPaths[i]);

        File.WriteAllText(receipt,
            "new_copied_customer_demo_scene=PASS\n" +
            "original_controller_prefab_scene_settings_unchanged=PASS\n" +
            "independent_user_ability_effect_assets=PASS\n" +
            "new_scene_contains_customer_controller_and_optional_hpr_ability=PASS\n" +
            "inspector_serialized_ability_remains_configured_after_scene_reload=PASS\n");
        Debug.Log("HPR_CUSTOMER_REAL_ABILITY_INTEGRATION_BUILD_PASS");
    }

    // Recovery for the precise first failed private QA run. This method does NOT
    // repeat scene creation, asset copying, or any completed external effects.
    public static void RepairExistingDemoUnlock()
    {
        string receipt = Environment.GetEnvironmentVariable("HPR_EXTERNAL_ABILITY_REPAIR_RECEIPT");
        if (string.IsNullOrWhiteSpace(receipt) || File.Exists(receipt))
            throw new InvalidOperationException("Expected a fresh private recovery receipt.");
        if (!AssetDatabase.IsValidFolder(DemoRoot) ||
            AssetDatabase.LoadAssetAtPath<AbilityData>(DemoAbility) == null ||
            AssetDatabase.LoadAssetAtPath<SceneAsset>(DemoScene) == null)
            throw new InvalidOperationException("Expected the existing, previously built QA demo.");
        string[] originals = { OriginalScene, OriginalPrefab, OriginalController,
                               OriginalSettings, SourceAbility, SourceEffect };
        string[] beforeBytes = originals.Select(FileDigest).ToArray();
        string[] beforeGuids = originals.Select(AssetDatabase.AssetPathToGUID).ToArray();
        Scene demo = EditorSceneManager.OpenScene(DemoScene, OpenSceneMode.Single);
        GameObject player = GameObject.Find("ExistingCustomerPlayer");
        if (player == null || player.GetComponent<ExistingPlayerController>() == null ||
            player.GetComponent<HprCustomerAbilityResourceBridge>() == null)
            throw new InvalidOperationException("Saved partial customer demo is inconsistent.");
        AbilityRunnerComponent runner = player.GetComponent<AbilityRunnerComponent>();
        if (runner == null)
            throw new InvalidOperationException("Saved ability runner is missing.");
        var authored = new SerializedObject(runner);
        SerializedProperty unlockAll = authored.FindProperty("unlockAllConfiguredAbilities");
        if (unlockAll == null || unlockAll.propertyType != SerializedPropertyType.Boolean ||
            unlockAll.boolValue)
            throw new InvalidOperationException("Expected the specific unconfigured unlock flag.");
        unlockAll.boolValue = true;
        authored.ApplyModifiedProperties();
        EditorUtility.SetDirty(runner);
        EditorSceneManager.MarkSceneDirty(demo);
        if (!EditorSceneManager.SaveScene(demo, DemoScene))
            throw new InvalidOperationException("Could not save the corrected private demo scene.");
        demo = EditorSceneManager.OpenScene(DemoScene, OpenSceneMode.Single);
        player = GameObject.Find("ExistingCustomerPlayer");
        runner = player == null ? null : player.GetComponent<AbilityRunnerComponent>();
        if (runner == null || player.GetComponent<ExistingPlayerController>() == null)
            throw new InvalidOperationException("Reopened corrected scene lacks expected components.");
        runner.RefreshRuntimeBindings();
        AbilityData ability = AssetDatabase.LoadAssetAtPath<AbilityData>(DemoAbility);
        var entries = runner.BuildEntries();
        if (entries.Count != 1 || !entries[0].Unlocked || entries[0].Id != ability.Id)
            throw new InvalidOperationException("Inspector unlock flag did not persist across scene load.");
        for (int i = 0; i < originals.Length; i++)
            if (FileDigest(originals[i]) != beforeBytes[i] ||
                AssetDatabase.AssetPathToGUID(originals[i]) != beforeGuids[i])
                throw new InvalidOperationException("Original customer/vendor content changed: " + originals[i]);
        File.WriteAllText(receipt,
            "existing_disposable_demo_repaired_without_recreation=PASS\n" +
            "serializable_inspector_unlock_persisted_after_scene_reload=PASS\n" +
            "original_customer_vendor_files_unchanged=PASS\n");
        Debug.Log("HPR_CUSTOMER_SAVED_UNLOCK_RECOVERED");
    }

    private static string FileDigest(string assetPath)
    {
        string physical = Path.Combine(Directory.GetParent(Application.dataPath).FullName, assetPath);
        using (var sha = SHA256.Create())
        using (var input = File.OpenRead(physical))
            return Convert.ToBase64String(sha.ComputeHash(input));
    }
}
#endif
