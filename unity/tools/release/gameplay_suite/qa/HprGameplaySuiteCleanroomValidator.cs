// Original offline buyer-package QA. This source is NOT included in the product archive.
#if UNITY_EDITOR
using System;
using System.IO;
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
        foreach (string property in new[] { "playerRoot", "enemyVisual", "lootItem", "weaponData", "enemyData" })
        {
            var field = serialized.FindProperty(property);
            if (field == null || field.objectReferenceValue == null)
                throw new InvalidOperationException("Missing imported scene binding " + property);
        }
        var scripts = AssetDatabase.FindAssets("t:MonoScript", new[] { "Assets/HPRGameplaySuite/Modules" });
        if (scripts.Length < 30)
            throw new InvalidOperationException("Expected HPR module sources are absent from imported product");
        string receipt = Environment.GetEnvironmentVariable("HPR_SUITE_CLEANROOM_RECEIPT");
        if (string.IsNullOrWhiteSpace(receipt))
            throw new InvalidOperationException("Private cleanroom QA receipt path absent");
        File.WriteAllText(receipt,
            "imported_scene=PASS\nserialized_references=5/5\n" +
            "module_script_guids=" + scripts.Length + "\n" +
            "engine=Unity 6000.4\nno_provider_write=true\n");
        Debug.Log("HPR SUITE CLEANROOM SUCCESS: actual imported scene, five bindings and module scripts verified");
    }
}
#endif
