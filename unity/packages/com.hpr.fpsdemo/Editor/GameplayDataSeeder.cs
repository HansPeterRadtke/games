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
    public const string SkillsRoot = DataRoot + "/Skills";
    public const string AssetMetadataRoot = DataRoot + "/AssetMetadata";
    public const string AssetRegistryPath = DataRoot + "/AssetRegistry.asset";

    public static void EnsureDataAssets()
    {
        EnsureFolder("Assets", "Data");
        EnsureFolder(DataRoot, "Weapons");
        EnsureFolder(DataRoot, "Items");
        EnsureFolder(DataRoot, "Enemies");
        EnsureFolder(DataRoot, "Skills");
        EnsureFolder(DataRoot, "AssetMetadata");
        EnsureAssetRegistry();
        EnsureSkillAssets();
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

    public static List<SkillNodeData> LoadAllSkills()
    {
        return LoadAssets<SkillNodeData>(SkillsRoot)
            .Where(asset => asset != null && !string.IsNullOrWhiteSpace(asset.Id))
            .OrderBy(asset => asset.Cost)
            .ThenBy(asset => asset.DisplayName)
            .ToList();
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

    private static void EnsureSkillAssets()
    {
        SkillNodeData vigor = EnsureSkillAsset(
            "skill_vigor",
            "Vigor Matrix",
            "Reinforces the suit frame for a larger health reserve.",
            1,
            startingUnlocked: true,
            healthBonus: 20f,
            staminaBonus: 0f,
            damageBonus: 0f,
            moveSpeedBonus: 0f,
            new Color(0.82f, 0.3f, 0.34f, 1f));

        SkillNodeData sprinter = EnsureSkillAsset(
            "skill_sprinter",
            "Sprinter Servo",
            "Retunes the leg servos for faster repositioning.",
            1,
            startingUnlocked: false,
            healthBonus: 0f,
            staminaBonus: 0f,
            damageBonus: 0f,
            moveSpeedBonus: 0.18f,
            new Color(0.24f, 0.7f, 0.94f, 1f),
            vigor);

        EnsureSkillAsset(
            "skill_recovery",
            "Recovery Lattice",
            "Expands the stamina reserve for longer sprint windows.",
            1,
            startingUnlocked: false,
            healthBonus: 0f,
            staminaBonus: 25f,
            damageBonus: 0f,
            moveSpeedBonus: 0f,
            new Color(0.28f, 0.88f, 0.54f, 1f),
            vigor);

        EnsureSkillAsset(
            "skill_overcharge",
            "Overcharge Chamber",
            "Routes more power into weapon systems for heavier shots.",
            2,
            startingUnlocked: false,
            healthBonus: 0f,
            staminaBonus: 0f,
            damageBonus: 0.2f,
            moveSpeedBonus: 0f,
            new Color(0.95f, 0.64f, 0.2f, 1f),
            sprinter);
    }

    private static SkillNodeData EnsureSkillAsset(
        string id,
        string displayName,
        string description,
        int cost,
        bool startingUnlocked,
        float healthBonus,
        float staminaBonus,
        float damageBonus,
        float moveSpeedBonus,
        Color themeColor,
        params SkillNodeData[] prerequisites)
    {
        string path = $"{SkillsRoot}/{id}.asset";
        var asset = AssetDatabase.LoadAssetAtPath<SkillNodeData>(path);
        if (asset == null)
        {
            asset = ScriptableObject.CreateInstance<SkillNodeData>();
            AssetDatabase.CreateAsset(asset, path);
        }

        asset.Id = id;
        asset.DisplayName = displayName;
        asset.Description = description;
        asset.Cost = Mathf.Max(1, cost);
        asset.StartingUnlocked = startingUnlocked;
        asset.MaxHealthBonus = healthBonus;
        asset.MaxStaminaBonus = staminaBonus;
        asset.DamageMultiplierBonus = damageBonus;
        asset.MoveSpeedMultiplierBonus = moveSpeedBonus;
        asset.ThemeColor = themeColor;
        asset.Prerequisites = prerequisites?.Where(requirement => requirement != null).Distinct().ToList() ?? new List<SkillNodeData>();
        EditorUtility.SetDirty(asset);
        AssetDatabase.SaveAssets();
        return asset;
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
