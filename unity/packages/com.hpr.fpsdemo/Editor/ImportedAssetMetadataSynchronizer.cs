using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

public static class ImportedAssetMetadataSynchronizer
{
    private const string ImportedMetadataRoot = GameplayDataSeeder.AssetMetadataRoot + "/Imported";

    private static readonly string[] SearchRoots =
    {
        "Assets/Free Wood Door Pack",
        "Assets/Low Poly Weapons VOL.1",
        "Assets/House Interior - Free",
        "Assets/Furniture Mega Pack - Free",
        "Assets/Furnished Cabin",
        "Assets/Apartment Kit",
        "Assets/CITY package",
        "Assets/Nature Starter Kit 2",
        "Assets/Unity Terrain - URP Demo Scene",
        "Assets/Realistic Terrain Textures FREE",
        "Assets/Grass Flowers Pack Free",
        "Assets/Flooded Grounds",
        "Assets/npc_casual_set_00",
        "Assets/Survivalist character",
        "Assets/Human Crafting Animations FREE",
        "Assets/RPG_Animations_Pack_FREE",
        "Assets/Starter Assets"
    };

    public static void Synchronize()
    {
        EnsureFolder(GameplayDataSeeder.AssetMetadataRoot, "Imported");

        var metadataAssets = new List<AssetMetadata>();
        foreach (string root in SearchRoots.Where(AssetDatabase.IsValidFolder))
        {
            AssetType assetType = ClassifyAssetType(root);
            MaterialType materialType = ClassifyMaterialType(root);
            foreach (string guid in AssetDatabase.FindAssets("t:Prefab", new[] { root }))
            {
                string prefabPath = AssetDatabase.GUIDToAssetPath(guid);
                AssetMetadata metadata = EnsureMetadata(prefabPath, assetType, materialType);
                if (metadata != null)
                {
                    metadataAssets.Add(metadata);
                }
            }
        }

        AssetRegistry registry = GameplayDataSeeder.LoadAssetRegistry();
        registry.SetEntries(metadataAssets.OrderBy(asset => asset.AssetType).ThenBy(asset => asset.AssetId));
        EditorUtility.SetDirty(registry);
        AssetDatabase.SaveAssets();
    }

    private static AssetMetadata EnsureMetadata(string prefabPath, AssetType assetType, MaterialType materialType)
    {
        if (string.IsNullOrWhiteSpace(prefabPath))
        {
            return null;
        }

        string assetId = BuildAssetId(prefabPath);
        string assetFileName = assetId.Replace('/', '_');
        string metadataPath = ImportedMetadataRoot + "/" + assetFileName + ".asset";
        AssetMetadata metadata = AssetDatabase.LoadAssetAtPath<AssetMetadata>(metadataPath);
        if (metadata == null)
        {
            metadata = ScriptableObject.CreateInstance<AssetMetadata>();
            AssetDatabase.CreateAsset(metadata, metadataPath);
        }

        metadata.AssetId = assetId;
        metadata.DisplayName = Path.GetFileNameWithoutExtension(prefabPath);
        metadata.PrefabAssetPath = prefabPath;
        metadata.AssetType = assetType;
        metadata.DefaultScale = Vector3.one;
        metadata.MaterialType = materialType;
        EditorUtility.SetDirty(metadata);
        return metadata;
    }

    private static string BuildAssetId(string prefabPath)
    {
        string relative = prefabPath.Replace("Assets/", string.Empty).Replace(".prefab", string.Empty);
        return relative
            .Replace("\\", "/")
            .Replace(" ", "_")
            .ToLowerInvariant();
    }

    private static AssetType ClassifyAssetType(string root)
    {
        string lower = root.ToLowerInvariant();
        if (lower.Contains("weapon"))
        {
            return AssetType.Weapon;
        }

        if (lower.Contains("npc") || lower.Contains("character") || lower.Contains("survivalist"))
        {
            return AssetType.Enemy;
        }

        if (lower.Contains("city") || lower.Contains("terrain") || lower.Contains("nature") || lower.Contains("house") || lower.Contains("apartment"))
        {
            return AssetType.Environment;
        }

        if (lower.Contains("furniture"))
        {
            return AssetType.Prop;
        }

        return AssetType.Decoration;
    }

    private static MaterialType ClassifyMaterialType(string root)
    {
        string lower = root.ToLowerInvariant();
        if (lower.Contains("wood"))
        {
            return MaterialType.Wood;
        }

        if (lower.Contains("metal") || lower.Contains("weapon"))
        {
            return MaterialType.Metal;
        }

        if (lower.Contains("nature") || lower.Contains("grass"))
        {
            return MaterialType.Organic;
        }

        if (lower.Contains("house") || lower.Contains("apartment") || lower.Contains("city"))
        {
            return MaterialType.Concrete;
        }

        if (lower.Contains("character"))
        {
            return MaterialType.Fabric;
        }

        return MaterialType.Unknown;
    }

    private static void EnsureFolder(string parent, string child)
    {
        if (!AssetDatabase.IsValidFolder(parent + "/" + child))
        {
            AssetDatabase.CreateFolder(parent, child);
        }
    }
}
