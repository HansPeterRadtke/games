using System.Collections.Generic;
using System.Linq;
using UnityEditor;

public static class GameplayDataSeeder
{
    public const string DataRoot = "Assets/Data";
    public const string WeaponsRoot = DataRoot + "/Weapons";
    public const string ItemsRoot = DataRoot + "/Items";
    public const string EnemiesRoot = DataRoot + "/Enemies";

    public static void EnsureDataAssets()
    {
        EnsureFolder("Assets", "Data");
        EnsureFolder(DataRoot, "Weapons");
        EnsureFolder(DataRoot, "Items");
        EnsureFolder(DataRoot, "Enemies");
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
}
