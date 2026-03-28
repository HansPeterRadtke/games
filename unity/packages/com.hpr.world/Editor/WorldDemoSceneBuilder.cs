#if UNITY_EDITOR
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class WorldDemoSceneBuilder
{
    private const string DemoFolder = "Packages/com.hpr.world/Demo";
    private const string ScenePath = DemoFolder + "/WorldDemo.unity";
    private const string TempSceneDirectory = "Assets/__GeneratedPackageDemos";
    private const string TempScenePath = TempSceneDirectory + "/WorldDemo.unity";
    private const string CratePath = DemoFolder + "/DemoCrate.asset";
    private const string LampPath = DemoFolder + "/DemoLamp.asset";
    private const string RegistryPath = DemoFolder + "/DemoAssetRegistry.asset";

    [MenuItem("HPR/World/Build Demo Scene")]
    public static void BuildDemoScene()
    {
        AssetMetadata crate = EnsureMetadata(CratePath, "prop_demo_crate", "Demo Supply Crate", AssetType.Prop, MaterialType.Wood, new Vector3(1.2f, 1f, 1f));
        AssetMetadata lamp = EnsureMetadata(LampPath, "prop_demo_lamp", "Demo Work Lamp", AssetType.Decoration, MaterialType.Metal, new Vector3(0.6f, 1.8f, 0.6f));
        AssetRegistry registry = EnsureRegistry(RegistryPath, crate, lamp);

        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var root = new GameObject("WorldDemoRoot");

        var cameraGo = new GameObject("Main Camera", typeof(Camera));
        cameraGo.tag = "MainCamera";
        cameraGo.transform.position = new Vector3(0f, 4.2f, -10f);
        cameraGo.transform.rotation = Quaternion.Euler(20f, 0f, 0f);

        var lightGo = new GameObject("Directional Light", typeof(Light));
        lightGo.transform.rotation = Quaternion.Euler(50f, -30f, 0f);
        lightGo.GetComponent<Light>().type = LightType.Directional;

        var floor = GameObject.CreatePrimitive(PrimitiveType.Plane);
        floor.name = "Floor";
        floor.transform.localScale = new Vector3(1.4f, 1f, 1.2f);

        var controller = root.AddComponent<WorldDemoController>();
        var so = new SerializedObject(controller);
        so.FindProperty("registry").objectReferenceValue = registry;
        var entriesProp = so.FindProperty("expectedEntries");
        var previewsProp = so.FindProperty("previews");
        entriesProp.arraySize = 2;
        previewsProp.arraySize = 2;
        CreatePreview(root.transform, entriesProp, previewsProp, 0, crate, PrimitiveType.Cube, new Vector3(-2f, 0.5f, 0f));
        CreatePreview(root.transform, entriesProp, previewsProp, 1, lamp, PrimitiveType.Cylinder, new Vector3(2f, 0.9f, 0f));
        so.ApplyModifiedPropertiesWithoutUndo();

        Directory.CreateDirectory(Path.GetDirectoryName(TempScenePath) ?? "Assets");
        EditorSceneManager.SaveScene(scene, TempScenePath);
        AssetDatabase.Refresh();

        CopyTempSceneToPackage(ScenePath, TempScenePath);
        AssetDatabase.DeleteAsset(TempScenePath);
        AssetDatabase.DeleteAsset(TempSceneDirectory);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log($"World demo scene written to {ScenePath}");
    }

    private static void CreatePreview(Transform root, SerializedProperty entriesProp, SerializedProperty previewsProp, int index, AssetMetadata metadata, PrimitiveType primitiveType, Vector3 position)
    {
        GameObject preview = GameObject.CreatePrimitive(primitiveType);
        preview.name = metadata.DisplayName + " Preview";
        preview.transform.SetParent(root, false);
        preview.transform.position = position;
        preview.transform.localScale = metadata.DefaultScale;
        entriesProp.GetArrayElementAtIndex(index).objectReferenceValue = metadata;
        previewsProp.GetArrayElementAtIndex(index).objectReferenceValue = preview.transform;
    }

    private static AssetMetadata EnsureMetadata(string path, string assetId, string displayName, AssetType assetType, MaterialType materialType, Vector3 defaultScale)
    {
        AssetMetadata asset = AssetDatabase.LoadAssetAtPath<AssetMetadata>(path);
        if (asset == null)
        {
            asset = ScriptableObject.CreateInstance<AssetMetadata>();
            AssetDatabase.CreateAsset(asset, path);
        }

        asset.AssetId = assetId;
        asset.DisplayName = displayName;
        asset.AssetType = assetType;
        asset.MaterialType = materialType;
        asset.DefaultScale = defaultScale;
        asset.PrefabAssetPath = string.Empty;
        EditorUtility.SetDirty(asset);
        return asset;
    }

    private static AssetRegistry EnsureRegistry(string path, params AssetMetadata[] entries)
    {
        AssetRegistry asset = AssetDatabase.LoadAssetAtPath<AssetRegistry>(path);
        if (asset == null)
        {
            asset = ScriptableObject.CreateInstance<AssetRegistry>();
            AssetDatabase.CreateAsset(asset, path);
        }

        asset.SetEntries(entries);
        EditorUtility.SetDirty(asset);
        return asset;
    }

    private static void CopyTempSceneToPackage(string targetScenePath, string sourceScenePath)
    {
        string sourceAbsolutePath = Path.GetFullPath(Path.Combine(Application.dataPath, "..", sourceScenePath));
        string targetAbsolutePath = Path.GetFullPath(Path.Combine(Application.dataPath, "..", targetScenePath));
        Directory.CreateDirectory(Path.GetDirectoryName(targetAbsolutePath) ?? Path.GetFullPath(Path.Combine(Application.dataPath, "..")));
        File.Copy(sourceAbsolutePath, targetAbsolutePath, true);

        string sourceMetaPath = sourceAbsolutePath + ".meta";
        string targetMetaPath = targetAbsolutePath + ".meta";
        if (!File.Exists(targetMetaPath) && File.Exists(sourceMetaPath))
        {
            File.Copy(sourceMetaPath, targetMetaPath, false);
        }
    }
}
#endif
