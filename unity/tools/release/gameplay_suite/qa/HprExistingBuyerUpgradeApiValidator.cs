// Private real Unity customer-upgrade QA: protects the selected ability installer
// and runtime API pair from the November 21 old-package CS1061 failure.
// NEVER include this fixture in the actual buyer archive.
#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.UIElements;
using UnityEngine;
using UnityEngine.UIElements;
using HPR;
using HPR.GameplaySuite;
using HPR.GameplaySuite.Experimental;

public static class HprExistingBuyerUpgradeApiValidator
{
    private static void Expect(bool ok, string why)
    { if (!ok) throw new InvalidOperationException("HPR_UPGRADE_API_QA: " + why); }

    public static void Run()
    {
        string receipt = Environment.GetEnvironmentVariable("HPR_UPGRADE_API_RECEIPT");
        Expect(Application.isBatchMode && !string.IsNullOrWhiteSpace(receipt) &&
            Path.IsPathRooted(receipt) && receipt.StartsWith(
                "/data/var/marketplace-account-setup/", StringComparison.Ordinal) &&
            !File.Exists(receipt) && !Directory.Exists(receipt),
            "a fresh absolute private QA receipt is required");

        AbilityData bundledAbility = AssetDatabase.LoadAssetAtPath<AbilityData>(
            "Assets/HPRGameplaySuite/Samples/RepairAbility.asset");
        Expect(bundledAbility != null, "original packaged sample ability missing");
        Expect(bundledAbility.TryValidateRuntimeSettings(out string reason),
            "sample ability runtime settings invalid: " + reason);

        var root = new GameObject("HPR disposable unsaved upgrade API fixture");
        HprSelectedAbilityInstaller window = null;
        try
        {
            var pool = root.AddComponent<HprSuiteAbilityPool>();
            Expect(!pool.HasValidStatsSource, "empty resource pool must not pretend to have stats");
            var stats = root.AddComponent<ActorStatsComponent>();
            pool.Bind(stats);
            Expect(pool.HasValidStatsSource && pool.StatsSource == stats,
                "the actual packaged ability pool cannot resolve its stats source");
            var other = new GameObject("HPR disposable foreign stats fixture");
            try
            {
                var foreign = other.AddComponent<ActorStatsComponent>();
                bool rejected = false;
                try { pool.Bind(foreign); }
                catch (ArgumentException) { rejected = true; }
                Expect(rejected && pool.StatsSource == stats,
                    "foreign stats were accepted or the previous binding was lost");
            }
            finally { UnityEngine.Object.DestroyImmediate(other); }

            HprSelectedAbilityInstaller.Open();
            window = Resources.FindObjectsOfTypeAll<HprSelectedAbilityInstaller>()
                .FirstOrDefault();
            Expect(window != null, "selected ability buyer menu did not open its Editor window");
            window.CreateGUI();
            var fields = window.rootVisualElement.Query<ObjectField>().ToList();
            var buttons = window.rootVisualElement.Query<Button>().ToList();
            Expect(fields.Count >= 3 && buttons.Count >= 2 &&
                window.rootVisualElement.Q<HelpBox>() != null,
                "buyer installer UI is missing required selection/action controls");
            Expect(root.GetComponent<AbilityRunnerComponent>() == null,
                "opening installer UI may not modify a customer object");
        }
        finally
        {
            if (window != null) window.Close();
            UnityEngine.Object.DestroyImmediate(root);
        }

        using (var stream = new FileStream(receipt, FileMode.CreateNew,
            FileAccess.Write, FileShare.None))
        using (var writer = new StreamWriter(stream))
        {
            writer.Write("actual_imported_AbilityData_validated=PASS\n" +
                "ability_pool_stats_binding=PASS\n" +
                "cross_object_stats_binding_rejected=PASS\n" +
                "selected_ability_editor_window_controls=PASS\n" +
                "preflight_has_no_automatic_runner_side_effect=PASS\n");
        }
        Debug.Log("HPR_EXISTING_BUYER_UPGRADE_API_QA_PASS");
    }
}
#endif
