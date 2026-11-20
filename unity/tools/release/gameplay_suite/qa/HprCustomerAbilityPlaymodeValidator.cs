// Private QA only: real Unity Play mode from a NEW customer-owned scene.
// The original customer's scene/prefab/controller/configuration remain unchanged.
#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;
using HPR;
using HprCustomerIntegrationQa;
using ExternalCustomerGame;

[InitializeOnLoad]
public static class HprCustomerAbilityPlaymodeValidator
{
    private const string StateKey = "HPR_EXTERNAL_CUSTOMER_ABILITY_QA_20261101";
    private static int frames;
    private static bool subscribed;

    static HprCustomerAbilityPlaymodeValidator()
    {
        if (SessionState.GetInt(StateKey, 0) > 0)
            Subscribe();
    }

    public static void Run()
    {
        string receipt = Environment.GetEnvironmentVariable("HPR_EXTERNAL_ABILITY_PLAY_RECEIPT");
        if (string.IsNullOrWhiteSpace(receipt) || File.Exists(receipt))
            throw new InvalidOperationException("Expected unused private playback receipt.");
        if (SessionState.GetInt(StateKey, 0) != 0)
            throw new InvalidOperationException("A previous ability Play mode QA has not completed.");
        if (EditorApplication.isPlayingOrWillChangePlaymode)
            throw new InvalidOperationException("Do not interrupt an existing Play mode.");

        var demo = EditorSceneManager.OpenScene(
            HprCustomerExistingGameAbilityValidator.DemoScene, OpenSceneMode.Single);
        var player = GameObject.Find("ExistingCustomerPlayer");
        if (player == null || player.GetComponent<ExistingPlayerController>() == null)
            throw new InvalidOperationException("Customer controller missing in copied scene.");
        if (!EditorSettings.enterPlayModeOptionsEnabled ||
            (EditorSettings.enterPlayModeOptions & EnterPlayModeOptions.DisableDomainReload) == 0)
            throw new InvalidOperationException("This test requires the customer Editor domain-reload-disabled setting.");
        SessionState.SetInt(StateKey, 1);
        frames = 0;
        Subscribe();
        EditorApplication.isPlaying = true;
        Debug.Log("HPR_EXTERNAL_CUSTOMER_ENTER_PLAY_REQUESTED");
    }

    private static void Subscribe()
    {
        if (subscribed)
            return;
        subscribed = true;
        EditorApplication.update += OnUpdate;
    }

    private static void OnUpdate()
    {
        int phase = SessionState.GetInt(StateKey, 0);
        if (phase == 0)
            return;
        try
        {
            if (phase == 1)
            {
                if (!EditorApplication.isPlaying || ++frames < 35)
                    return;
                var player = GameObject.Find("ExistingCustomerPlayer");
                var controller = player == null ? null : player.GetComponent<ExistingPlayerController>();
                var resources = player == null ? null : player.GetComponent<HprCustomerAbilityResourceBridge>();
                var runner = player == null ? null : player.GetComponent<AbilityRunnerComponent>();
                if (controller == null || resources == null || runner == null ||
                    Math.Abs(controller.MoveSpeed - 5.75f) > 0.0001f)
                    throw new InvalidOperationException("Original customer controller or integration is missing.");

                var asset = AssetDatabase.LoadAssetAtPath<AbilityData>(
                    HprCustomerExistingGameAbilityValidator.DemoAbility);
                if (asset == null || asset.Effects.Count != 1 ||
                    AssetDatabase.GetAssetPath(asset.Effects[0]) !=
                    HprCustomerExistingGameAbilityValidator.DemoEffect)
                    throw new InvalidOperationException("Customer-owned ability lost its copied effect.");

                if (Math.Abs(resources.Health - 40f) > 0.0001f ||
                    Math.Abs(resources.Stamina - 100f) > 0.0001f)
                    throw new InvalidOperationException("Customer resource baseline altered before activation.");
                if (runner.BuildEntries().Count != 1 ||
                    !runner.TryActivate(asset.Id))
                    throw new InvalidOperationException("New customer-owned healing ability did not activate.");
                if (Math.Abs(resources.Health - 60f) > 0.0001f ||
                    Math.Abs(resources.Stamina - 80f) > 0.0001f)
                    throw new InvalidOperationException("Ability failed to heal or consume stamina.");
                if (runner.TryActivate(asset.Id))
                    throw new InvalidOperationException("Ability cooldown did not block a repeat activation.");

                string receipt = Environment.GetEnvironmentVariable("HPR_EXTERNAL_ABILITY_PLAY_RECEIPT");
                File.WriteAllText(receipt,
                    "real_unity_playmode_customer_controller_retained=PASS\n" +
                    "customer_owned_ability_effect_reference=PASS\n" +
                    "healing_ability_applies_20_health=PASS\n" +
                    "ability_consumes_20_stamina=PASS\n" +
                    "cooldown_blocks_second_cast=PASS\n" +
                    "domain_reload_disabled_project_configuration=PASS\n");
                Debug.Log("HPR_EXTERNAL_CUSTOMER_PLAYMODE_ABILITY_PASS");
                SessionState.SetInt(StateKey, 2);
                EditorApplication.isPlaying = false;
            }
            else if (phase == 2 && !EditorApplication.isPlayingOrWillChangePlaymode)
            {
                SessionState.SetInt(StateKey, 0);
                EditorApplication.update -= OnUpdate;
                subscribed = false;
                EditorApplication.delayCall += () => EditorApplication.Exit(0);
            }
        }
        catch (Exception error)
        {
            Debug.LogException(error);
            SessionState.SetInt(StateKey, 0);
            EditorApplication.update -= OnUpdate;
            subscribed = false;
            EditorApplication.Exit(3);
        }
    }
}
#endif
