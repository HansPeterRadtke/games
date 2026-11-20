// Isolated real Unity Editor UI Toolkit behavior test; never ship this file.
// Exercises the actual installed HPR Editor window, selection events, and
// consent-gated button state WITHOUT saving/changing any customer-owned asset.
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

public static class HprSelectedAbilityInstallerUiBehaviorValidator
{
    private const string OriginalScene =
        "Assets/ExternalCustomerGame/Scenes/OriginalCustomerScene.unity";
    private const string CustomerAbility =
        "Assets/ExternalCustomerGame/IntegrationDemos/CustomerHealing.asset";
    private const string VendorAbility =
        "Assets/HPRGameplaySuite/Samples/RepairAbility.asset";

    public static void Run()
    {
        string receipt = Environment.GetEnvironmentVariable("HPR_INSTALLER_UI_BEHAVIOR_RECEIPT");
        if (string.IsNullOrWhiteSpace(receipt) || File.Exists(receipt))
            throw new InvalidOperationException("A fresh private UI behavior receipt is required.");

        byte[] sourceScene = File.ReadAllBytes(
            Path.Combine(Directory.GetParent(Application.dataPath).FullName, OriginalScene));
        EditorSceneManager.OpenScene(OriginalScene, OpenSceneMode.Single);
        var player = GameObject.Find("ExistingCustomerPlayer");
        if (player == null || player.GetComponent<ExistingPlayerController>() == null)
            throw new InvalidOperationException("No independent customer player in original scene.");
        if (player.GetComponent<AbilityRunnerComponent>() != null)
            throw new InvalidOperationException("Customer original scene has already been edited.");
        var provider = player.AddComponent<HprCustomerAbilityResourceBridge>();
        var customer = AssetDatabase.LoadAssetAtPath<AbilityData>(CustomerAbility);
        var vendor = AssetDatabase.LoadAssetAtPath<AbilityData>(VendorAbility);
        if (provider == null || customer == null || vendor == null)
            throw new InvalidOperationException("Missing imported independent/vendor AbilityData.");

        Selection.activeGameObject = player;
        HprSelectedAbilityInstaller.Open();
        var window = Resources.FindObjectsOfTypeAll<HprSelectedAbilityInstaller>().FirstOrDefault();
        if (window == null)
            throw new InvalidOperationException("Actual installed HPR Editor window was not created.");
        try
        {
            window.CreateGUI();
            var fields = window.rootVisualElement.Query<ObjectField>().ToList();
            var button = window.rootVisualElement.Query<Button>().ToList()
                .FirstOrDefault(b => b.text.Contains("Attach ability"));
            var help = window.rootVisualElement.Q<HelpBox>();
            if (button == null || help == null || fields.Count != 3)
                throw new InvalidOperationException("Buyer UI fields/status/attach button are missing.");

            var targetInput = fields.Single(f => f.label == "Selected object");
            var abilityInput = fields.Single(f => f.label == "Customer-owned ability");
            var providerInput = fields.Single(f => f.label == "Resource provider");

            if (targetInput.value != player || providerInput.value != provider ||
                button.enabledInHierarchy)
                throw new InvalidOperationException("Initial read-only preview incorrectly enables attachment.");

            abilityInput.value = vendor;
            if (button.enabledInHierarchy || !help.text.Contains("Copy"))
                throw new InvalidOperationException("Vendor-owned sample should be refused by actual UI.");

            abilityInput.value = customer;
            if (!button.enabledInHierarchy || help.messageType != HelpBoxMessageType.Info)
                throw new InvalidOperationException("Valid customer ability did not enable attach.");

            providerInput.value = null;
            if (button.enabledInHierarchy || !help.text.Contains("IAbilityResourcePool"))
                throw new InvalidOperationException("Removing required provider did not disable attach.");
            providerInput.value = provider;
            if (!button.enabledInHierarchy)
                throw new InvalidOperationException("Valid provider did not restore attach readiness.");

            var other = new GameObject("Other buyer scene object not configured for this ability");
            targetInput.value = other;
            if (button.enabledInHierarchy)
                throw new InvalidOperationException("Attach remains enabled on unrelated customer scene object.");
            targetInput.value = player;
            if (!button.enabledInHierarchy)
                throw new InvalidOperationException("Reselecting original player did not restore readiness.");

            if (player.GetComponent<AbilityRunnerComponent>() != null)
                throw new InvalidOperationException("Read-only UI preview unexpectedly installed an HPR component.");

            File.WriteAllText(receipt,
                "real_unity_editor_window_constructed=PASS\n" +
                "missing_customer_ability_disables_attach=PASS\n" +
                "vendor_sample_rejected_with_actionable_feedback=PASS\n" +
                "valid_customer_ability_enables_attach=PASS\n" +
                "missing_resource_provider_disables_attach=PASS\n" +
                "reselected_customer_player_restores_readiness=PASS\n" +
                "read_only_preview_creates_no_ability_runner=PASS\n");
            Debug.Log("HPR_SELECTED_ABILITY_REAL_UI_BEHAVIOR_PASS");
        }
        finally
        {
            window.Close();
            Selection.activeGameObject = null;
        }
        if (!sourceScene.SequenceEqual(File.ReadAllBytes(
            Path.Combine(Directory.GetParent(Application.dataPath).FullName, OriginalScene))))
            throw new InvalidOperationException("Customer original scene bytes changed during UI preview");
    }
}
#endif
