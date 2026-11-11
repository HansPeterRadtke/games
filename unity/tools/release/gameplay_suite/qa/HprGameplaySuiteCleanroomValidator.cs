// Original offline buyer-package QA. This source is NOT included in the product archive.
#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using HPR.GameplaySuite;

public static class HprGameplaySuiteCleanroomValidator
{
    public static void Run()
    {
        const string scenePath = "Assets/HPRGameplaySuite/Demo/GameplaySuiteShowcase.unity";
        if (AssetDatabase.LoadAssetAtPath<SceneAsset>(scenePath) == null)
            throw new InvalidOperationException("Imported buyer archive does not contain its demo scene");
        var scene = EditorSceneManager.OpenScene(scenePath, OpenSceneMode.Single);
        HprGameplaySuitePlayground candidate = null;
        foreach (var root in scene.GetRootGameObjects())
        {
            var component = root.GetComponent<HprGameplaySuitePlayground>();
            if (component != null) candidate = component;
        }
        if (candidate == null)
            throw new InvalidOperationException("Imported scene has no integrated playground component");
        var serialized = new SerializedObject(candidate);
        foreach (string property in new[] { "playerRoot", "enemyVisual", "arenaCamera", "medkitPickup", "keyPickup",
            "demoDoor", "lootItem", "keyItem", "weaponData", "enemyData", "healAbility", "pulseAbility", "worldRegistry" })
        {
            var field = serialized.FindProperty(property);
            if (field == null || field.objectReferenceValue == null)
                throw new InvalidOperationException("Missing imported scene binding " + property);
        }
        foreach (string path in new[] {
            "Assets/HPRGameplaySuite/QUICKSTART.md",
            "Assets/HPRGameplaySuite/ARCHITECTURE.md",
            "Assets/HPRGameplaySuite/Integration/HprSuiteIntegration.cs",
            "Assets/HPRGameplaySuite/Integration/HprSuiteSnapshot.cs",
            "Assets/HPRGameplaySuite/Integration/HprSuiteArenaMotor.cs",
            "Assets/HPRGameplaySuite/Integration/HprSuiteInput.cs",
            "Assets/HPRGameplaySuite/Editor/HprSuiteIntegrationGuide.cs",
            "Assets/HPRGameplaySuite/Editor/Styles/HprSuiteIntegrationGuide.uss",
            "Assets/HPRGameplaySuite/Samples/TrainingKey.asset",
            "Assets/HPRGameplaySuite/Samples/RepairAbility.asset",
            "Assets/HPRGameplaySuite/Samples/PulseAbility.asset",
            "Assets/HPRGameplaySuite/Samples/TrainingWorldRegistry.asset"
        })
        {
            if (AssetDatabase.LoadMainAssetAtPath(path) == null)
                throw new InvalidOperationException("New sample/dependency missing in buyer archive: " + path);
        }
        string installerIssue = HprGameplaySuiteSceneBuilder.AbilityInstallerIssue();
        if (installerIssue != null)
            throw new InvalidOperationException("Imported ability installer unavailable: " + installerIssue);
        // Buyer safety regression: the scene-builder menu must never overwrite
        // existing customized sample assets nor replace an imported demo scene.
        string sceneFile = Path.Combine(Application.dataPath, "HPRGameplaySuite/Demo/GameplaySuiteShowcase.unity");
        string medkitFile = Path.Combine(Application.dataPath, "HPRGameplaySuite/Samples/FieldMedkit.asset");
        byte[] sceneBefore = File.ReadAllBytes(sceneFile);
        byte[] medkitBefore = File.ReadAllBytes(medkitFile);
        bool blocked = false;
        try
        {
            HprGameplaySuiteSceneBuilder.BuildShowcase();
        }
        catch (InvalidOperationException)
        {
            blocked = true;
        }
        if (!blocked || !sceneBefore.SequenceEqual(File.ReadAllBytes(sceneFile)) ||
            !medkitBefore.SequenceEqual(File.ReadAllBytes(medkitFile)))
            throw new InvalidOperationException(
                "Existing buyer demo assets were overwritten by the build tool");

        var scripts = AssetDatabase.FindAssets("t:MonoScript", new[] { "Assets/HPRGameplaySuite/Modules" });
        if (scripts.Length < 30)
            throw new InvalidOperationException("Expected HPR module sources are absent from imported product");
        string receipt = Environment.GetEnvironmentVariable("HPR_SUITE_CLEANROOM_RECEIPT");
        if (string.IsNullOrWhiteSpace(receipt))
            throw new InvalidOperationException("Private cleanroom QA receipt path absent");
        File.WriteAllText(receipt,
            "imported_scene=PASS\nserialized_references=13/13\n" +
            "additional_samples_and_docs=12/12\ncompiled_ability_installer=PASS\nexisting_user_assets_not_overwritten=PASS\nmodule_script_guids=" + scripts.Length + "\n" +
            "engine=Unity " + Application.unityVersion + "\nno_provider_write=true\n");
        Debug.Log("HPR SUITE CLEANROOM SUCCESS: actual imported scene, thirteen bindings and module scripts verified");
    }
}
#endif
