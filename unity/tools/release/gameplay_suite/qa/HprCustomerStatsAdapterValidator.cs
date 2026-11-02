// Genuine Unity 6000.6 Editor QA in a private disposable customer game.
// This source is a regression probe, NOT part of a buyer-facing package.
#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;
using HPR;
using HPR.GameplaySuite;
using HPR.GameplaySuite.Experimental;
using ExternalCustomerGame;

[InitializeOnLoad]
public static class HprCustomerStatsAdapterValidator
{
    private const string OriginalScene =
        "Assets/ExternalCustomerGame/Scenes/OriginalCustomerScene.unity";
    private const string NewScene =
        "Assets/ExternalCustomerGame/IntegrationDemos/CustomerActorStatsIntegrated.unity";
    private const string OriginalPrefab =
        "Assets/ExternalCustomerGame/Prefabs/ExistingCustomerPlayer.prefab";
    private const string OriginalCode =
        "Assets/ExternalCustomerGame/ExistingPlayerController.cs";
    private const string OriginalSettings =
        "Assets/ExternalCustomerGame/Configs/CustomerSettings.asset";
    private const string CustomerAbility =
        "Assets/ExternalCustomerGame/IntegrationDemos/CustomerHealing.asset";
    private const string CustomerEffect =
        "Assets/ExternalCustomerGame/IntegrationDemos/CustomerHealing__HPR_RepairEffect.asset";
    private const string SessionKey = "HPR_CUSTOMER_STATS_ADAPTER_EDITOR_PLAY_20261102";
    private static int frames;
    private static bool subscribed;

    static HprCustomerStatsAdapterValidator()
    {
        if (SessionState.GetInt(SessionKey, 0) != 0)
            Subscribe();
    }

    public static void BuildNewCustomerScene()
    {
        string receipt = Environment.GetEnvironmentVariable("HPR_STATS_ADAPTER_RECEIPT");
        if (string.IsNullOrWhiteSpace(receipt) || File.Exists(receipt))
            throw new InvalidOperationException("Expected a fresh private stats-adapter receipt");
        if (File.Exists(Physical(NewScene)) || File.Exists(Physical(NewScene + ".meta")) ||
            AssetDatabase.LoadMainAssetAtPath(NewScene) != null)
            throw new InvalidOperationException("Refusing existing customer scene overwrite");

        string[] originals = { OriginalScene, OriginalPrefab, OriginalCode,
                               OriginalSettings, CustomerAbility, CustomerEffect };
        string[] bytes = originals.Select(path => Digest(Physical(path))).ToArray();
        string[] guids = originals.Select(AssetDatabase.AssetPathToGUID).ToArray();
        if (guids.Any(string.IsNullOrWhiteSpace))
            throw new InvalidOperationException("Original customer input is missing metadata");

        var source = EditorSceneManager.OpenScene(OriginalScene, OpenSceneMode.Single);
        var customerPlayer = GameObject.Find("ExistingCustomerPlayer");
        if (customerPlayer == null ||
            customerPlayer.GetComponent<ExistingPlayerController>() == null)
            throw new InvalidOperationException("Original customer controller is missing");
        if (customerPlayer.GetComponent<AbilityRunnerComponent>() != null)
            throw new InvalidOperationException("Refusing unexpected preexisting HPR runner");
        if (!EditorSceneManager.SaveScene(source, NewScene, true))
            throw new InvalidOperationException("Could not create a separate customer scene");
        Scene newScene = EditorSceneManager.OpenScene(NewScene, OpenSceneMode.Single);
        customerPlayer = GameObject.Find("ExistingCustomerPlayer");
        if (customerPlayer == null ||
            customerPlayer.GetComponent<ExistingPlayerController>() == null)
            throw new InvalidOperationException("The copied scene lost the customer controller");

        AbilityData ability = AssetDatabase.LoadAssetAtPath<AbilityData>(CustomerAbility);
        if (ability == null || ability.Effects == null || ability.Effects.Count != 1 ||
            AssetDatabase.GetAssetPath(ability.Effects[0]) != CustomerEffect)
            throw new InvalidOperationException("Independent customer healing ability is missing");

        // First check the buyer-visible error when HPR resource pool is
        // present but not connected to any ActorStats source.
        var orphan = new GameObject("QA resource pool without ActorStats");
        var empty = orphan.AddComponent<HprSuiteAbilityPool>();
        string rejection = HprSelectedAbilityInstaller.ValidateSelection(orphan, ability, empty);
        if (string.IsNullOrEmpty(rejection) ||
            !rejection.Contains("missing an ActorStatsComponent"))
            throw new InvalidOperationException("The UI accepted a resource pool that cannot function");
        UnityEngine.Object.DestroyImmediate(orphan);

        // Add HPR Stats without replacing/re-writing the existing controller.
        var stats = customerPlayer.AddComponent<ActorStatsComponent>();
        var pool = customerPlayer.AddComponent<HprSuiteAbilityPool>();
        if (stats == null || pool == null)
            throw new InvalidOperationException("Could not add optional customer-owned HPR components");

        // Verify the Reset()/same-GameObject fallback works in the Editor
        // even when no customer C# script has invoked Bind().
        var serializedPool = new SerializedObject(pool);
        var sourceRef = serializedPool.FindProperty("stats");
        if (sourceRef == null || sourceRef.propertyType != SerializedPropertyType.ObjectReference)
            throw new InvalidOperationException("Resource adapter's Inspector reference is not serialized");
        sourceRef.objectReferenceValue = null;
        serializedPool.ApplyModifiedProperties();
        if (!pool.HasValidStatsSource || pool.StatsSource != stats)
            throw new InvalidOperationException("Native HPR Stats fallback does not work without custom C#");

        var otherGameObject = new GameObject("QA unrelated stats owner");
        var unrelatedStats = otherGameObject.AddComponent<ActorStatsComponent>();
        bool invalidRejected = false;
        try
        {
            pool.Bind(unrelatedStats);
        }
        catch (ArgumentException)
        {
            invalidRejected = true;
        }
        UnityEngine.Object.DestroyImmediate(otherGameObject);
        if (!invalidRejected || pool.StatsSource != stats)
            throw new InvalidOperationException("Cross-customer-object Stats binding was accepted");

        pool.Bind(stats);
        var written = new SerializedObject(pool).FindProperty("stats");
        if (written == null || written.objectReferenceValue != stats)
            throw new InvalidOperationException("Native HPR Stats Bind did not serialize the component");
        stats.SetHealth(40f);
        stats.SetStamina(100f);
        EditorUtility.SetDirty(pool);
        EditorUtility.SetDirty(stats);
        if (HprSelectedAbilityInstaller.ValidateSelection(customerPlayer, ability, pool) != null)
            throw new InvalidOperationException("A correctly configured native HPR pool was rejected");
        var runner = HprSelectedAbilityInstaller.AttachExplicitly(customerPlayer, ability, pool);
        if (runner == null ||
            customerPlayer.GetComponent<ExistingPlayerController>() == null)
            throw new InvalidOperationException("Installer replaced the existing customer controller");
        Undo.PerformUndo();
        if (customerPlayer.GetComponent<AbilityRunnerComponent>() != null ||
            customerPlayer.GetComponent<ExistingPlayerController>() == null ||
            customerPlayer.GetComponent<HprSuiteAbilityPool>() != pool)
            throw new InvalidOperationException("Installer Undo removed or damaged existing buyer components");
        Undo.PerformRedo();
        runner = customerPlayer.GetComponent<AbilityRunnerComponent>();
        if (runner == null ||
            HprSelectedAbilityInstaller.ValidateSelection(customerPlayer, ability, pool) == null)
            throw new InvalidOperationException("Installer Redo failed to restore the configured ability");
        EditorSceneManager.MarkSceneDirty(newScene);
        if (!EditorSceneManager.SaveScene(newScene, NewScene))
            throw new InvalidOperationException("New customer scene did not save");

        newScene = EditorSceneManager.OpenScene(NewScene, OpenSceneMode.Single);
        customerPlayer = GameObject.Find("ExistingCustomerPlayer");
        stats = customerPlayer == null ? null : customerPlayer.GetComponent<ActorStatsComponent>();
        pool = customerPlayer == null ? null : customerPlayer.GetComponent<HprSuiteAbilityPool>();
        runner = customerPlayer == null ? null : customerPlayer.GetComponent<AbilityRunnerComponent>();
        if (stats == null || pool == null || runner == null ||
            customerPlayer.GetComponent<ExistingPlayerController>() == null)
            throw new InvalidOperationException("Saved scene lost customer controller or HPR components");
        written = new SerializedObject(pool).FindProperty("stats");
        if (written == null || written.objectReferenceValue != stats ||
            !pool.HasValidStatsSource || pool.StatsSource != stats)
            throw new InvalidOperationException("Stats resource reference was not serialized on scene reload");
        var configured = new SerializedObject(runner).FindProperty("resourcePoolBehaviour");
        if (configured == null || configured.objectReferenceValue != pool)
            throw new InvalidOperationException("Ability runner lost the native Stats resource binding");
        runner.RefreshRuntimeBindings();
        var entries = runner.BuildEntries();
        if (entries.Count != 1 || !entries[0].Unlocked || entries[0].Id != ability.Id)
            throw new InvalidOperationException("Installed customer ability was not initialized");

        for (int i = 0; i < originals.Length; i++)
            if (Digest(Physical(originals[i])) != bytes[i] ||
                AssetDatabase.AssetPathToGUID(originals[i]) != guids[i])
                throw new InvalidOperationException("Original customer file changed: " + originals[i]);

        File.WriteAllText(receipt,
            "native_hpr_pool_rejects_missing_stats_component=PASS\n" +
            "native_hpr_pool_fallback_works_without_customer_source_changes=PASS\n" +
            "cross_object_stats_binding_rejected=PASS\n" +
            "stats_source_inspector_reference_survives_scene_reload=PASS\n" +
            "buyer_ability_attach_undo_redo_preserves_customer_components=PASS\n" +
            "buyer_ability_runner_preserves_customer_controller=PASS\n" +
            "customer_ability_unlocked_and_bound_after_reload=PASS\n" +
            "original_customer_scene_prefab_script_settings_ability_unchanged=PASS\n");
        Debug.Log("HPR_CUSTOMER_STATS_ADAPTER_SCENE_BUILD_PASS");
    }

    public static void RunPlaymode()
    {
        string receipt = Environment.GetEnvironmentVariable("HPR_STATS_ADAPTER_PLAY_RECEIPT");
        if (string.IsNullOrWhiteSpace(receipt) || File.Exists(receipt))
            throw new InvalidOperationException("Expected fresh private Play-mode receipt");
        if (SessionState.GetInt(SessionKey, 0) != 0 ||
            EditorApplication.isPlayingOrWillChangePlaymode)
            throw new InvalidOperationException("Another Play-mode test is already active");
        EditorSceneManager.OpenScene(NewScene, OpenSceneMode.Single);
        var buyer = GameObject.Find("ExistingCustomerPlayer");
        if (buyer == null || buyer.GetComponent<ExistingPlayerController>() == null ||
            buyer.GetComponent<HprSuiteAbilityPool>() == null)
            throw new InvalidOperationException("Customer-authored new scene was not saved");
        SessionState.SetInt(SessionKey, 1);
        frames = 0;
        Subscribe();
        EditorApplication.isPlaying = true;
        Debug.Log("HPR_CUSTOMER_STATS_ADAPTER_REAL_PLAY_ENTER_REQUESTED");
    }

    private static void Subscribe()
    {
        if (subscribed) return;
        EditorApplication.update += OnUpdate;
        subscribed = true;
    }

    private static void OnUpdate()
    {
        int phase = SessionState.GetInt(SessionKey, 0);
        if (phase == 0) return;
        try
        {
            if (phase == 1)
            {
                if (!EditorApplication.isPlaying || ++frames < 40) return;
                var player = GameObject.Find("ExistingCustomerPlayer");
                var stats = player == null ? null : player.GetComponent<ActorStatsComponent>();
                var pool = player == null ? null : player.GetComponent<HprSuiteAbilityPool>();
                var runner = player == null ? null : player.GetComponent<AbilityRunnerComponent>();
                var ability = AssetDatabase.LoadAssetAtPath<AbilityData>(CustomerAbility);
                if (stats == null || pool == null || runner == null || ability == null ||
                    player.GetComponent<ExistingPlayerController>() == null ||
                    !pool.HasValidStatsSource || pool.StatsSource != stats)
                    throw new InvalidOperationException("Real Play mode lost the customer/native resource bindings");
                if (Math.Abs(stats.Health - 40f) > .001f || Math.Abs(stats.Stamina - 100f) > .001f)
                    throw new InvalidOperationException("Native HPR Stats starting values did not survive Play mode");
                runner.RefreshRuntimeBindings();
                if (!runner.TryActivate(ability.Id))
                    throw new InvalidOperationException("New customer scene's healing ability failed in Play mode");
                if (Math.Abs(stats.Health - 60f) > .001f || Math.Abs(stats.Stamina - 80f) > .001f)
                    throw new InvalidOperationException("Native HPR Stats healing/stamina effect was incorrect");
                if (runner.TryActivate(ability.Id))
                    throw new InvalidOperationException("Native HPR healing ability ignored cooldown");

                File.WriteAllText(Environment.GetEnvironmentVariable("HPR_STATS_ADAPTER_PLAY_RECEIPT"),
                    "actual_unity_6000_6_customer_playmode=PASS\n" +
                    "existing_customer_controller_retained=PASS\n" +
                    "saved_native_stats_reference_functional_after_reload=PASS\n" +
                    "healing_restored_twenty_health=PASS\n" +
                    "stamina_consumed_twenty=PASS\n" +
                    "ability_cooldown_blocked_second_cast=PASS\n");
                Debug.Log("HPR_CUSTOMER_STATS_ADAPTER_REAL_PLAYMODE_PASS");
                SessionState.SetInt(SessionKey, 2);
                EditorApplication.isPlaying = false;
            }
            else if (phase == 2 && !EditorApplication.isPlayingOrWillChangePlaymode)
            {
                SessionState.SetInt(SessionKey, 0);
                EditorApplication.update -= OnUpdate;
                subscribed = false;
                EditorApplication.delayCall += () => EditorApplication.Exit(0);
            }
        }
        catch (Exception error)
        {
            Debug.LogException(error);
            SessionState.SetInt(SessionKey, 0);
            EditorApplication.update -= OnUpdate;
            subscribed = false;
            EditorApplication.Exit(3);
        }
    }

    private static string Physical(string path) =>
        Path.Combine(Directory.GetParent(Application.dataPath).FullName, path);

    private static string Digest(string physical)
    {
        using (var input = File.OpenRead(physical))
        using (var digest = SHA256.Create())
            return Convert.ToBase64String(digest.ComputeHash(input));
    }
}
#endif
