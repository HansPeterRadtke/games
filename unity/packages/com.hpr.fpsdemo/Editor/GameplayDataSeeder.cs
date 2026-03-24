using System.Collections.Generic;
using System.Linq;
using UnityEditor;
using UnityEngine;

public static class GameplayDataSeeder
{
    public const string DataRoot = "Assets/Data";
    public const string WeaponsRoot = DataRoot + "/Weapons";
    public const string ItemsRoot = DataRoot + "/Items";
    public const string EnemiesRoot = DataRoot + "/Enemies";
    public const string AssetMetadataRoot = DataRoot + "/AssetMetadata";
    public const string AssetRegistryPath = DataRoot + "/AssetRegistry.asset";

    public static void EnsureDataAssets()
    {
        EnsureFolder("Assets", "Data");
        EnsureFolder(DataRoot, "Weapons");
        EnsureFolder(DataRoot, "Items");
        EnsureFolder(DataRoot, "Enemies");
        EnsureFolder(DataRoot, "AssetMetadata");
        EnsureAssetRegistry();
        EnsureGameplayAssetDefaults();
        ImportedAssetMetadataSynchronizer.Synchronize();
        AssetDatabase.Refresh();
    }

    public static List<WeaponData> LoadDefaultWeapons()
    {
        return LoadAssets<WeaponData>(WeaponsRoot)
            .Where(asset => asset != null && asset.IncludeInDefaultLoadout)
            .OrderBy(asset => asset.DefaultSlot)
            .ThenBy(asset => asset.DisplayName)
            .ToList();
    }

    public static List<ItemData> LoadAllItems()
    {
        return LoadAssets<ItemData>(ItemsRoot)
            .Where(asset => asset != null && asset.IncludeInKnownItems)
            .OrderBy(asset => asset.ItemType)
            .ThenBy(asset => asset.DisplayName)
            .ToList();
    }

    public static ItemData LoadItem(string id)
    {
        return LoadAssets<ItemData>(ItemsRoot).FirstOrDefault(asset => asset != null && asset.Id == id);
    }

    public static EnemyData LoadEnemy(string id)
    {
        return LoadAssets<EnemyData>(EnemiesRoot).FirstOrDefault(asset => asset != null && asset.Id == id);
    }

    public static AssetRegistry LoadAssetRegistry()
    {
        var registry = AssetDatabase.LoadAssetAtPath<AssetRegistry>(AssetRegistryPath);
        if (registry != null)
        {
            return registry;
        }

        EnsureAssetRegistry();
        return AssetDatabase.LoadAssetAtPath<AssetRegistry>(AssetRegistryPath);
    }

    public static List<AssetMetadata> LoadAllAssetMetadata()
    {
        return LoadAssets<AssetMetadata>(AssetMetadataRoot)
            .Where(asset => asset != null && !string.IsNullOrWhiteSpace(asset.AssetId))
            .OrderBy(asset => asset.AssetType)
            .ThenBy(asset => asset.AssetId)
            .ToList();
    }

    private static List<T> LoadAssets<T>(string folder) where T : UnityEngine.Object
    {
        return AssetDatabase.FindAssets($"t:{typeof(T).Name}", new[] { folder })
            .Select(AssetDatabase.GUIDToAssetPath)
            .Select(AssetDatabase.LoadAssetAtPath<T>)
            .Where(asset => asset != null)
            .ToList();
    }

    private static void EnsureFolder(string parent, string child)
    {
        if (!AssetDatabase.IsValidFolder($"{parent}/{child}"))
        {
            AssetDatabase.CreateFolder(parent, child);
        }
    }

    private static void EnsureAssetRegistry()
    {
        if (AssetDatabase.LoadAssetAtPath<AssetRegistry>(AssetRegistryPath) != null)
        {
            return;
        }

        var registry = ScriptableObject.CreateInstance<AssetRegistry>();
        AssetDatabase.CreateAsset(registry, AssetRegistryPath);
        AssetDatabase.SaveAssets();
    }

    private static void EnsureGameplayAssetDefaults()
    {
        bool changed = false;

        foreach (var weapon in LoadAssets<WeaponData>(WeaponsRoot))
        {
            if (weapon == null)
            {
                continue;
            }

            FireModeType expectedFireMode = DeriveFireMode(weapon);
            if (weapon.FireModeType != expectedFireMode)
            {
                weapon.FireModeType = expectedFireMode;
                EditorUtility.SetDirty(weapon);
                changed = true;
            }
        }

        foreach (var enemy in LoadAssets<EnemyData>(EnemiesRoot))
        {
            if (enemy == null)
            {
                continue;
            }

            EnemyAIType expectedAi = DeriveAiType(enemy);
            if (enemy.AIType != expectedAi)
            {
                enemy.AIType = expectedAi;
                EditorUtility.SetDirty(enemy);
                changed = true;
            }
        }

        if (changed)
        {
            AssetDatabase.SaveAssets();
        }
    }

    private static FireModeType DeriveFireMode(WeaponData weapon)
    {
        if (weapon == null)
        {
            return FireModeType.Hitscan;
        }

        string id = weapon.Id ?? string.Empty;
        if (weapon.Kind == EquipmentKind.Utility)
        {
            return FireModeType.Utility;
        }

        if (weapon.Kind == EquipmentKind.Melee)
        {
            return FireModeType.Melee;
        }

        if (weapon.Kind == EquipmentKind.Scatter || id.Contains("scatter"))
        {
            return FireModeType.Shotgun;
        }

        if (weapon.Kind == EquipmentKind.Explosive || id.Contains("launcher") || id.Contains("needler"))
        {
            return FireModeType.Projectile;
        }

        return FireModeType.Hitscan;
    }

    private static EnemyAIType DeriveAiType(EnemyData enemy)
    {
        if (enemy == null)
        {
            return EnemyAIType.PatrolChase;
        }

        string id = enemy.Id ?? string.Empty;
        if (id.Contains("sentry"))
        {
            return EnemyAIType.StationaryAttack;
        }

        if (id.Contains("power") || id.Contains("sweeper"))
        {
            return EnemyAIType.AggressiveChase;
        }

        return EnemyAIType.PatrolChase;
    }
}
