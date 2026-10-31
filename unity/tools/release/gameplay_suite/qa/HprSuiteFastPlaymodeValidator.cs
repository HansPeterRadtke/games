// Isolated buyer archive acceptance for Unity's domain-reload-disabled Play Mode.
// Test driver is NOT included in the commercial package.
#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using HPR.GameplaySuite;

[InitializeOnLoad]
public static class HprSuiteFastPlaymodeValidator
{
    private const string Prefix = "HPR_SUITE_FAST_PLAY_QA_20261031";
    private static int frames;
    private static int phase;
    private static bool subscribed;

    static HprSuiteFastPlaymodeValidator()
    {
        if (SessionState.GetInt(Prefix + "_phase", 0) > 0) Subscribe();
    }

    private static void Subscribe()
    {
        if (subscribed) return;
        subscribed = true;
        EditorApplication.update += OnUpdate;
    }

    public static void Run()
    {
        if (SessionState.GetInt(Prefix + "_phase", 0) != 0)
            throw new InvalidOperationException("Prior domain-reload test did not finish");
        string path = Environment.GetEnvironmentVariable("HPR_SUITE_FAST_PLAY_RECEIPT");
        if (string.IsNullOrWhiteSpace(path) || File.Exists(path))
            throw new InvalidOperationException("Fresh private domain-reload receipt required");
        EditorSceneManager.OpenScene(
            "Assets/HPRGameplaySuite/Demo/GameplaySuiteShowcase.unity", OpenSceneMode.Single);

        SessionState.SetBool(Prefix + "_originalEnabled", EditorSettings.enterPlayModeOptionsEnabled);
        SessionState.SetInt(Prefix + "_originalOptions", (int)EditorSettings.enterPlayModeOptions);
        EditorSettings.enterPlayModeOptionsEnabled = true;
        EditorSettings.enterPlayModeOptions = EnterPlayModeOptions.DisableDomainReload;
        SessionState.SetInt(Prefix + "_phase", 1);
        phase = 1;
        frames = 0;
        Subscribe();
        EditorApplication.isPlaying = true;
        Debug.Log("HPR_SUITE_FAST_PLAY_FIRST_ENTER_REQUESTED");
    }

    private static void OnUpdate()
    {
        phase = SessionState.GetInt(Prefix + "_phase", 0);
        if (phase == 0) return;
        try
        {
            if (phase == 1)
            {
                if (!EditorApplication.isPlaying || ++frames < 30) return;
                HprGameplaySuitePlayground suite = FindSuite();
                suite.SetAutomaticEnemy(false);
                AssertClean(suite, "first entry");
                if (!suite.EnemyAttack() || suite.PlayerHealth != 92f)
                    throw new InvalidOperationException("First entry did not deliver exactly one attack");
                NextPhase(2);
                EditorApplication.isPlaying = false;
            }
            else if (phase == 2)
            {
                if (EditorApplication.isPlayingOrWillChangePlaymode) return;
                NextPhase(3);
                EditorApplication.isPlaying = true;
            }
            else if (phase == 3)
            {
                if (!EditorApplication.isPlaying || ++frames < 30) return;
                HprGameplaySuitePlayground suite = FindSuite();
                suite.SetAutomaticEnemy(false);
                AssertClean(suite, "second entry with C# domain retained");
                if (!suite.EnemyAttack() || suite.PlayerHealth != 92f)
                    throw new InvalidOperationException(
                        "Second entry delivered duplicate damage or lacked event subscription");
                string receipt = Environment.GetEnvironmentVariable("HPR_SUITE_FAST_PLAY_RECEIPT");
                File.WriteAllText(receipt,
                    "domain_reload_disabled_two_editor_play_entries=PASS\n" +
                    "fresh_vitals_weapon_inventory_each_entry=PASS\n" +
                    "typed_event_no_duplicate_subscribers=PASS\n" +
                    "composition_and_world_registry_each_entry=PASS\n");
                Debug.Log("HPR_SUITE_FAST_PLAY_QA_SUCCESS");
                NextPhase(4);
                EditorApplication.isPlaying = false;
            }
            else if (phase == 4 && !EditorApplication.isPlayingOrWillChangePlaymode)
            {
                RestoreOriginalEditorSettings();
                NextPhase(0);
                EditorApplication.update -= OnUpdate;
                subscribed = false;
                EditorApplication.delayCall += () => EditorApplication.Exit(0);
            }
        }
        catch (Exception ex)
        {
            Debug.LogError("HPR_SUITE_FAST_PLAY_QA_FAILED " + ex);
            RestoreOriginalEditorSettings();
            SessionState.SetInt(Prefix + "_phase", 0);
            EditorApplication.update -= OnUpdate;
            subscribed = false;
            EditorApplication.isPlaying = false;
            EditorApplication.delayCall += () => EditorApplication.Exit(1);
        }
    }

    private static void NextPhase(int next)
    {
        phase = next;
        frames = 0;
        SessionState.SetInt(Prefix + "_phase", phase);
    }

    private static void RestoreOriginalEditorSettings()
    {
        EditorSettings.enterPlayModeOptionsEnabled =
            SessionState.GetBool(Prefix + "_originalEnabled", false);
        EditorSettings.enterPlayModeOptions =
            (EnterPlayModeOptions)SessionState.GetInt(Prefix + "_originalOptions", 0);
    }

    private static HprGameplaySuitePlayground FindSuite()
    {
        HprGameplaySuitePlayground suite =
            UnityEngine.Object.FindAnyObjectByType<HprGameplaySuitePlayground>();
        if (suite == null || !suite.isActiveAndEnabled)
            throw new InvalidOperationException("Imported scene controller absent in Play Mode");
        return suite;
    }

    private static void AssertClean(HprGameplaySuitePlayground suite, string context)
    {
        if (suite.PlayerHealth != 100f || suite.PlayerStamina != 100f ||
            suite.EnemyHealth != 60f || suite.MagazineAmmo != 6 ||
            suite.KeyCount != 0 || suite.LootCount != 0 ||
            !suite.ServicesAvailable || !suite.WorldCatalogAvailable)
            throw new InvalidOperationException("Dirty/reused demo state on " + context);
    }
}
#endif
