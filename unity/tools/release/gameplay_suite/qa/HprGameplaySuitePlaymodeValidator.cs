// Independent Editor-only QA. Opens the imported buyer scene, enters real
// Unity Play mode and checks the scene's automatically initialized components.
// This file is NOT shipped in the Unity buyer archive.
#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using HPR.GameplaySuite;

[InitializeOnLoad]
public static class HprGameplaySuitePlaymodeValidator
{
    private const string SessionKey = "HprSuiteLivePlaymodePendingV2";
    private const string ReceiptEnv = "HPR_SUITE_PLAYMODE_RECEIPT";
    private static int frameCount;

    static HprGameplaySuitePlaymodeValidator()
    {
        EditorApplication.update -= Tick;
        if (SessionState.GetBool(SessionKey, false))
            EditorApplication.update += Tick;
    }

    public static void Run()
    {
        if (SessionState.GetBool(SessionKey, false))
            throw new InvalidOperationException("An unresolved suite playmode test is already active");
        string receipt = Environment.GetEnvironmentVariable(ReceiptEnv);
        if (string.IsNullOrWhiteSpace(receipt) || File.Exists(receipt))
            throw new InvalidOperationException("Need a fresh private playmode receipt path");
        EditorSceneManager.OpenScene("Assets/HPRGameplaySuite/Demo/GameplaySuiteShowcase.unity",
            OpenSceneMode.Single);
        SessionState.SetBool(SessionKey, true);
        frameCount = 0;
        EditorApplication.update += Tick;
        EditorApplication.isPlaying = true;
        Debug.Log("HPR_QA_PLAYMODE_ENTER_REQUESTED");
    }

    private static void Tick()
    {
        if (!SessionState.GetBool(SessionKey, false))
        {
            EditorApplication.update -= Tick;
            return;
        }
        if (!EditorApplication.isPlaying || ++frameCount < 20) return;
        try
        {
            HprGameplaySuitePlayground suite =
                UnityEngine.Object.FindAnyObjectByType<HprGameplaySuitePlayground>();
            if (suite == null || !suite.isActiveAndEnabled)
                throw new InvalidOperationException("Real imported scene controller missing or disabled");
            if (suite.PlayerHealth != 100 || suite.EnemyHealth != 60 ||
                suite.MagazineAmmo != 6 || suite.PlayerStamina != 100)
                throw new InvalidOperationException("Real playmode Awake did not initialize correctly");
            if (!suite.ServicesAvailable || !suite.WorldCatalogAvailable)
                throw new InvalidOperationException("Real playmode service/world bindings missing");
            if (!suite.EnemyAttack() || suite.PlayerHealth != 92)
                throw new InvalidOperationException("Real scene typed attack event did not apply damage");
            if (!suite.UseHealAbility() || suite.PlayerStamina != 80 || suite.PlayerHealth != 100)
                throw new InvalidOperationException("Real scene healing ability failed");
            suite.SaveCheckpoint();
            if (!suite.Fire() || suite.MagazineAmmo != 5 || suite.EnemyHealth != 45)
                throw new InvalidOperationException("Real scene weapon runtime failed");
            if (!suite.RestoreCheckpoint() || suite.MagazineAmmo != 6 || suite.EnemyHealth != 60)
                throw new InvalidOperationException("Real scene full checkpoint restore failed");
            string receipt = Environment.GetEnvironmentVariable(ReceiptEnv);
            File.WriteAllText(receipt,
                "imported_scene_actual_playmode=PASS\n" +
                "real_awake_and_scene_bindings=PASS\n" +
                "composition_and_world_registry=PASS\n" +
                "combat_and_typed_damage_event=PASS\n" +
                "live_ability_and_stamina=PASS\n" +
                "live_weapon_and_checkpoint_restore=PASS\n");
            Debug.Log("HPR_QA_REAL_PLAYMODE_PASS");
            Complete(0);
        }
        catch (Exception error)
        {
            Debug.LogError("HPR_QA_REAL_PLAYMODE_FAILED " + error);
            Complete(1);
        }
    }

    private static void Complete(int exit)
    {
        SessionState.SetBool(SessionKey, false);
        EditorApplication.update -= Tick;
        EditorApplication.isPlaying = false;
        EditorApplication.delayCall += () => EditorApplication.Exit(exit);
    }
}
#endif
