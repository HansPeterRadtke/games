using System;
using System.Collections.Generic;
using System.Linq;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

public static class ThirdPartyAssetIntegrator
{
    private const string MainScenePath = "Assets/Scenes/Gameplay.unity";
    private static readonly string[] FurnitureSearchRoots =
    {
        "Assets/Furniture Mega Pack - Free",
        "Assets/Furniture Mega Pack"
    };
    private static readonly string[] WeaponSearchRoots =
    {
        "Assets/Low Poly Weapons VOL.1",
        "Assets/Low Poly Weapons VOL.1 Demo",
        "Assets/Low Poly Weapons VOL.1/Prefabs",
    };
    private static readonly string[] HouseSearchRoots =
    {
        "Assets/House Interior - Free",
        "Assets/House Interior",
        "Assets/Furnished Cabin",
        "Assets/Apartment Kit",
    };
    private static readonly string[] VistaSearchRoots =
    {
        "Assets/CITY package",
        "Assets/CITY Package",
        "Assets/Nature Starter Kit 2",
        "Assets/Unity Terrain - URP Demo Scene",
        "Assets/Realistic Terrain Textures FREE",
        "Assets/Grass Flowers Pack Free",
        "Assets/Flooded Grounds",
    };
    private static readonly string[] CharacterSearchRoots =
    {
        "Assets/npc_casual_set_00",
        "Assets/Survivalist character",
        "Assets/Starter Assets",
        "Assets/StarterAssets",
    };

    private static readonly Dictionary<string, string> DoorPrefabBySaveId = new()
    {
        ["door_east"] = "Assets/Free Wood Door Pack/Prefab/Wood/Door_4/Door_4_White.prefab",
        ["door_west"] = "Assets/Free Wood Door Pack/Prefab/Wood/Door_5/Door_5_Brown.prefab",
        ["door_north"] = "Assets/Free Wood Door Pack/Prefab/Wood/Door_14/Door_14_Black.prefab",
        ["door_south"] = "Assets/Free Wood Door Pack/Prefab/Wood/Door_13/Door_13_White.prefab",
    };

    [MenuItem("HPR/Integrate/Apply Door Pack")]
    public static void ApplyDoorPack()
    {
        var scene = EditorSceneManager.OpenScene(MainScenePath, OpenSceneMode.Single);
        int updated = 0;
        foreach (var controller in UnityEngine.Object.FindObjectsByType<DoorController>())
        {
            if (!DoorPrefabBySaveId.TryGetValue(controller.SaveId, out var prefabPath))
            {
                continue;
            }

            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath);
            if (prefab == null)
            {
                throw new Exception($"Missing door prefab at {prefabPath}");
            }

            UpgradeDoor(controller, prefab);
            updated++;
        }

        if (updated == 0)
        {
            throw new Exception("No door controllers were upgraded.");
        }

        EditorSceneManager.MarkSceneDirty(scene);
        EditorSceneManager.SaveScene(scene);
        ImportedAssetMetadataSynchronizer.Synchronize();
        Debug.Log($"Door pack applied to {updated} scene doors.");
    }

    [MenuItem("HPR/Integrate/Apply Door Pack From Batch")]
    public static void ApplyDoorPackFromBatch()
    {
        ApplyDoorPack();
    }

    [MenuItem("HPR/Integrate/Apply Furniture Pack")]
    public static void ApplyFurniturePack()
    {
        if (!FurnitureSearchRoots.Any(AssetDatabase.IsValidFolder))
        {
            Debug.LogWarning("Furniture pack not imported yet.");
            return;
        }

        var scene = EditorSceneManager.OpenScene(MainScenePath, OpenSceneMode.Single);
        var world = GameObject.Find("World")?.transform;
        if (world == null)
        {
            throw new Exception("World root not found.");
        }

        var artRoot = EnsureChild(world, "ThirdPartyArt");
        var furnitureRoot = EnsureChild(artRoot, "FurnitureMegaPack");
        ClearChildren(furnitureRoot);
        var hubRoot = EnsureChild(furnitureRoot, "Hub");
        var medbayRoot = EnsureChild(furnitureRoot, "Medbay");
        var securityRoot = EnsureChild(furnitureRoot, "Security");
        var armoryRoot = EnsureChild(furnitureRoot, "Armory");
        var powerRoot = EnsureChild(furnitureRoot, "Power");

        int placed = 0;
        placed += TryPlaceFurniture(hubRoot, "hub_table", new[] { "table" }, new Vector3(0f, 0f, 3.2f), Vector3.zero, new Vector3(2.4f, 1.1f, 1.5f));
        placed += TryPlaceFurniture(hubRoot, "hub_chair_left", new[] { "chair" }, new Vector3(-1.15f, 0f, 2.6f), new Vector3(0f, 35f, 0f), new Vector3(1.0f, 1.4f, 1.0f));
        placed += TryPlaceFurniture(hubRoot, "hub_chair_right", new[] { "chair" }, new Vector3(1.15f, 0f, 2.6f), new Vector3(0f, -35f, 0f), new Vector3(1.0f, 1.4f, 1.0f));
        placed += TryPlaceFurniture(medbayRoot, "medbay_cabinet_a", new[] { "cabinet", "locker" }, new Vector3(-24.4f, 0f, 4f), new Vector3(0f, 90f, 0f), new Vector3(1.4f, 2.3f, 0.9f));
        placed += TryPlaceFurniture(medbayRoot, "medbay_cabinet_b", new[] { "cabinet", "locker" }, new Vector3(-24.4f, 0f, -2.6f), new Vector3(0f, 90f, 0f), new Vector3(1.4f, 2.3f, 0.9f));
        placed += TryPlaceFurniture(medbayRoot, "medbay_table", new[] { "bed", "table" }, new Vector3(-17.8f, 0f, 2.2f), new Vector3(0f, 180f, 0f), new Vector3(2.3f, 1.2f, 1.0f));
        placed += TryPlaceFurniture(securityRoot, "security_desk", new[] { "desk", "table" }, new Vector3(-2.2f, 0f, 23.8f), new Vector3(0f, 180f, 0f), new Vector3(2.8f, 1.2f, 1.4f));
        placed += TryPlaceFurniture(securityRoot, "security_chair", new[] { "chair" }, new Vector3(-2.2f, 0f, 22.4f), Vector3.zero, new Vector3(1.0f, 1.4f, 1.0f));
        placed += TryPlaceFurniture(securityRoot, "security_shelf", new[] { "shelf", "book" }, new Vector3(6.8f, 0f, 25.1f), new Vector3(0f, 180f, 0f), new Vector3(2.2f, 2.5f, 0.8f));
        placed += TryPlaceFurniture(armoryRoot, "armory_shelf_a", new[] { "shelf", "rack" }, new Vector3(24.2f, 0f, 4.8f), new Vector3(0f, -90f, 0f), new Vector3(2.4f, 2.6f, 0.85f));
        placed += TryPlaceFurniture(armoryRoot, "armory_shelf_b", new[] { "shelf", "rack" }, new Vector3(24.2f, 0f, -3.8f), new Vector3(0f, -90f, 0f), new Vector3(2.4f, 2.6f, 0.85f));
        placed += TryPlaceFurniture(armoryRoot, "armory_table", new[] { "table", "bench" }, new Vector3(18.5f, 0f, -1.2f), new Vector3(0f, 90f, 0f), new Vector3(2.4f, 1.1f, 1.3f));
        placed += TryPlaceFurniture(powerRoot, "power_cabinet", new[] { "cabinet", "locker" }, new Vector3(4.6f, 0f, -24.4f), Vector3.zero, new Vector3(1.6f, 2.4f, 0.9f));
        placed += TryPlaceFurniture(powerRoot, "power_table", new[] { "table", "desk" }, new Vector3(-3.8f, 0f, -23.8f), Vector3.zero, new Vector3(2.6f, 1.1f, 1.3f));

        if (placed == 0)
        {
            Debug.LogWarning("Furniture pack imported, but no matching prefabs were found.");
            return;
        }

        EditorSceneManager.MarkSceneDirty(scene);
        EditorSceneManager.SaveScene(scene);
        ImportedAssetMetadataSynchronizer.Synchronize();
        Debug.Log($"Furniture pack applied with {placed} placed props.");
    }

    [MenuItem("HPR/Integrate/Apply Furniture Pack From Batch")]
    public static void ApplyFurniturePackFromBatch()
    {
        ApplyFurniturePack();
    }

    [MenuItem("HPR/Integrate/Apply Weapon Pack")]
    public static void ApplyWeaponPack()
    {
        if (!WeaponSearchRoots.Any(AssetDatabase.IsValidFolder))
        {
            Debug.LogWarning("Weapon pack not imported yet.");
            return;
        }

        int updated = 0;
        updated += TryApplyWeaponVisual("weapon_pulse_pistol", new[] { "pistol", "handgun" }, 0.42f);
        updated += TryApplyWeaponVisual("weapon_scatter_shot", new[] { "shotgun" }, 0.62f);
        updated += TryApplyWeaponVisual("weapon_needler", new[] { "rifle", "smg", "submachine" }, 0.62f);
        updated += TryApplyWeaponVisual("weapon_arc_launcher", new[] { "launcher", "rocket", "rpg", "bazooka" }, 0.7f);
        updated += TryApplyWeaponVisual("weapon_security_baton", new[] { "baton", "club", "hammer", "axe", "knife", "sword" }, 0.54f);

        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        ImportedAssetMetadataSynchronizer.Synchronize();
        Debug.Log($"Weapon pack applied to {updated} weapon data assets.");
    }

    [MenuItem("HPR/Integrate/Apply Weapon Pack From Batch")]
    public static void ApplyWeaponPackFromBatch()
    {
        ApplyWeaponPack();
    }

    [MenuItem("HPR/Integrate/Apply House Pack")]
    public static void ApplyHousePack()
    {
        if (!HouseSearchRoots.Any(AssetDatabase.IsValidFolder) && !VistaSearchRoots.Any(AssetDatabase.IsValidFolder))
        {
            Debug.LogWarning("House/environment packs not imported yet.");
            return;
        }

        var scene = EditorSceneManager.OpenScene(MainScenePath, OpenSceneMode.Single);
        var world = GameObject.Find("World")?.transform;
        if (world == null)
        {
            throw new Exception("World root not found.");
        }

        var artRoot = EnsureChild(world, "ThirdPartyArt");
        var houseRoot = EnsureChild(artRoot, "HouseInteriorPack");
        ClearChildren(houseRoot);
        var hubRoot = EnsureChild(houseRoot, "Hub");
        var medbayRoot = EnsureChild(houseRoot, "Medbay");
        var securityRoot = EnsureChild(houseRoot, "Security");
        var vistaRoot = EnsureChild(houseRoot, "Vista");

        int placed = 0;
        placed += TryPlaceProp(HouseSearchRoots, hubRoot, "hub_sofa", new[] { "sofa", "couch" }, new Vector3(-5.4f, 0f, 6.8f), new Vector3(0f, 90f, 0f), new Vector3(2.4f, 1.4f, 1.0f));
        placed += TryPlaceProp(HouseSearchRoots, hubRoot, "hub_coffee_table", new[] { "coffee", "table" }, new Vector3(-4.1f, 0f, 6.8f), Vector3.zero, new Vector3(1.2f, 0.8f, 0.8f));
        placed += TryPlaceProp(HouseSearchRoots, hubRoot, "hub_floor_lamp", new[] { "lamp" }, new Vector3(6.4f, 0f, 6.6f), Vector3.zero, new Vector3(0.8f, 2.4f, 0.8f));
        placed += TryPlaceProp(HouseSearchRoots, hubRoot, "hub_bookshelf", new[] { "book", "shelf" }, new Vector3(7.2f, 0f, -2.8f), new Vector3(0f, -90f, 0f), new Vector3(1.3f, 2.3f, 0.5f));
        placed += TryPlaceProp(HouseSearchRoots, medbayRoot, "medbay_bed_residential", new[] { "bed" }, new Vector3(-20.8f, 0f, -4.4f), new Vector3(0f, 90f, 0f), new Vector3(2.2f, 1.0f, 1.0f));
        placed += TryPlaceProp(HouseSearchRoots, medbayRoot, "medbay_side_cabinet", new[] { "cabinet", "dresser", "wardrobe" }, new Vector3(-24.2f, 0f, -6.2f), new Vector3(0f, 90f, 0f), new Vector3(1.3f, 2.0f, 0.8f));
        placed += TryPlaceProp(HouseSearchRoots, securityRoot, "security_sideboard", new[] { "drawer", "cabinet", "desk" }, new Vector3(7.6f, 0f, 18.2f), new Vector3(0f, 180f, 0f), new Vector3(2.2f, 1.2f, 0.8f));
        placed += TryPlaceProp(HouseSearchRoots, securityRoot, "security_chair_residential", new[] { "chair" }, new Vector3(5.8f, 0f, 20.4f), new Vector3(0f, -50f, 0f), new Vector3(1.1f, 1.3f, 1.1f));
        placed += TryPlaceProp(VistaSearchRoots, vistaRoot, "vista_block_a", new[] { "building", "house" }, new Vector3(0f, 0f, 58f), Vector3.zero, new Vector3(26f, 22f, 18f));
        placed += TryPlaceProp(VistaSearchRoots, vistaRoot, "vista_block_b", new[] { "building", "house" }, new Vector3(42f, 0f, 26f), new Vector3(0f, 35f, 0f), new Vector3(20f, 18f, 16f));
        placed += TryPlaceProp(VistaSearchRoots, vistaRoot, "vista_tree_cluster", new[] { "tree", "pine", "oak" }, new Vector3(-36f, 0f, 30f), Vector3.zero, new Vector3(10f, 14f, 10f));
        placed += TryPlaceProp(VistaSearchRoots, vistaRoot, "vista_rock_cluster", new[] { "rock", "stone" }, new Vector3(-26f, 0f, 52f), Vector3.zero, new Vector3(8f, 5f, 8f));

        if (placed == 0)
        {
            Debug.LogWarning("Environment packs imported, but no matching prefabs were found.");
            return;
        }

        EditorSceneManager.MarkSceneDirty(scene);
        EditorSceneManager.SaveScene(scene);
        ImportedAssetMetadataSynchronizer.Synchronize();
        Debug.Log($"House/environment packs applied with {placed} placed props.");
    }

    [MenuItem("HPR/Integrate/Apply House Pack From Batch")]
    public static void ApplyHousePackFromBatch()
    {
        ApplyHousePack();
    }

    [MenuItem("HPR/Integrate/Apply Character Packs")]
    public static void ApplyCharacterPacks()
    {
        if (!CharacterSearchRoots.Any(AssetDatabase.IsValidFolder))
        {
            Debug.LogWarning("Character packs not imported yet.");
            return;
        }

        int updated = 0;
        updated += TryApplyEnemyVisual("enemy_sentry_hub", new[] { "female", "woman", "casual", "npc" }, 1.72f, 0f);
        updated += TryApplyEnemyVisual("enemy_medbay_intruder", new[] { "female", "casual", "npc" }, 1.7f, 0f);
        updated += TryApplyEnemyVisual("enemy_security_guard", new[] { "male", "survival", "guard", "casual" }, 1.8f, 0f);
        updated += TryApplyEnemyVisual("enemy_sweeper_armory", new[] { "male", "survival", "worker", "casual" }, 1.8f, 0f);
        updated += TryApplyEnemyVisual("enemy_power_walker", new[] { "male", "worker", "casual", "survival" }, 1.82f, 0f);

        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        ImportedAssetMetadataSynchronizer.Synchronize();
        Debug.Log($"Character packs applied to {updated} enemy data assets.");
    }

    [MenuItem("HPR/Integrate/Apply Character Packs From Batch")]
    public static void ApplyCharacterPacksFromBatch()
    {
        ApplyCharacterPacks();
    }

    private static void UpgradeDoor(DoorController controller, GameObject prefab)
    {
        var serializedDoor = new SerializedObject(controller);
        var keyItem = serializedDoor.FindProperty("requiredKeyItem")?.objectReferenceValue as ItemData;

        var oldLeaf = controller.transform.Find("DoorLeaf") ?? controller.transform.Cast<Transform>().FirstOrDefault();
        if (oldLeaf == null)
        {
            throw new Exception($"Door {controller.SaveId} is missing its existing leaf");
        }

        var targetLeafBounds = CalculateBounds(oldLeaf.gameObject);
        var oldFrameNames = new[]
        {
            $"{controller.SaveId}_FrameTop",
            $"{controller.SaveId}_FrameLeft",
            $"{controller.SaveId}_FrameRight"
        };

        var importedRoot = PrefabUtility.InstantiatePrefab(prefab, controller.transform) as GameObject;
        if (importedRoot == null)
        {
            throw new Exception($"Could not instantiate prefab {prefab.name}");
        }

        importedRoot.name = "DoorVisual";
        importedRoot.transform.localPosition = oldLeaf.localPosition;
        importedRoot.transform.localRotation = Quaternion.identity;
        importedRoot.transform.localScale = Vector3.one;

        StripForeignBehaviours(importedRoot);
        AssignLayerRecursively(importedRoot.transform, controller.gameObject.layer);

        var importedLeaf = FindChildRecursive(importedRoot.transform, "Door") ?? importedRoot.transform;
        var sourceLeafBounds = CalculateBounds(importedLeaf.gameObject);
        if (sourceLeafBounds.size.x <= 0.0001f || sourceLeafBounds.size.y <= 0.0001f || sourceLeafBounds.size.z <= 0.0001f)
        {
            throw new Exception($"Imported door {prefab.name} produced invalid bounds");
        }

        var scale = new Vector3(
            targetLeafBounds.size.x / sourceLeafBounds.size.x,
            targetLeafBounds.size.y / sourceLeafBounds.size.y,
            Mathf.Max(0.85f, targetLeafBounds.size.z / sourceLeafBounds.size.z));
        importedRoot.transform.localScale = scale;

        var alignedLeafBounds = CalculateBounds(importedLeaf.gameObject);
        importedRoot.transform.position += targetLeafBounds.center - alignedLeafBounds.center;

        foreach (var frameName in oldFrameNames)
        {
            var oldFrame = controller.transform.parent != null ? controller.transform.parent.Find(frameName) : null;
            if (oldFrame != null)
            {
                UnityEngine.Object.DestroyImmediate(oldFrame.gameObject);
            }
        }

        UnityEngine.Object.DestroyImmediate(oldLeaf.gameObject);
        controller.Configure(controller.SaveId, importedLeaf, keyItem);
        EditorUtility.SetDirty(controller);
    }

    private static int TryPlaceFurniture(Transform parent, string instanceName, string[] keywords, Vector3 position, Vector3 rotationEuler, Vector3 targetSize)
    {
        return TryPlaceProp(FurnitureSearchRoots, parent, instanceName, keywords, position, rotationEuler, targetSize);
    }

    private static int TryPlaceProp(IEnumerable<string> searchRoots, Transform parent, string instanceName, string[] keywords, Vector3 position, Vector3 rotationEuler, Vector3 targetSize)
    {
        var prefab = FindBestPrefab(searchRoots, keywords);
        if (prefab == null)
        {
            return 0;
        }

        PlaceStaticProp(parent, instanceName, prefab, position, rotationEuler, targetSize);
        return 1;
    }

    private static int TryApplyWeaponVisual(string weaponId, string[] keywords, float targetLength)
    {
        var prefab = FindBestPrefab(WeaponSearchRoots, keywords);
        if (prefab == null)
        {
            return 0;
        }

        var weapon = AssetDatabase.FindAssets("t:WeaponData", new[] { GameplayDataSeeder.WeaponsRoot })
            .Select(AssetDatabase.GUIDToAssetPath)
            .Select(AssetDatabase.LoadAssetAtPath<WeaponData>)
            .FirstOrDefault(candidate => candidate != null && candidate.Id == weaponId);
        if (weapon == null)
        {
            return 0;
        }

        float longestDimension = MeasureLongestDimension(prefab);
        if (longestDimension <= 0.001f)
        {
            return 0;
        }

        float uniformScale = targetLength / longestDimension;
        weapon.ViewPrefab = prefab;
        weapon.ViewLocalScale = Vector3.one * uniformScale;
        if (weapon.ViewMuzzleLocalPosition == Vector3.zero)
        {
            weapon.ViewMuzzleLocalPosition = new Vector3(0f, 0.01f, targetLength * 0.55f);
        }

        EditorUtility.SetDirty(weapon);
        return 1;
    }

    private static int TryApplyEnemyVisual(string enemyId, string[] keywords, float targetHeight, float yawDegrees)
    {
        var prefab = FindBestPrefab(CharacterSearchRoots, keywords);
        if (prefab == null)
        {
            return 0;
        }

        var enemy = AssetDatabase.FindAssets("t:EnemyData", new[] { GameplayDataSeeder.EnemiesRoot })
            .Select(AssetDatabase.GUIDToAssetPath)
            .Select(AssetDatabase.LoadAssetAtPath<EnemyData>)
            .FirstOrDefault(candidate => candidate != null && candidate.Id == enemyId);
        if (enemy == null)
        {
            return 0;
        }

        var bounds = MeasureBounds(prefab);
        if (bounds.size.y <= 0.01f)
        {
            return 0;
        }

        float uniformScale = targetHeight / bounds.size.y;
        enemy.VisualPrefab = prefab;
        enemy.VisualLocalScale = Vector3.one * uniformScale;
        enemy.VisualLocalPosition = new Vector3(0f, -bounds.min.y * uniformScale, 0f);
        enemy.VisualLocalEuler = new Vector3(0f, yawDegrees, 0f);
        EditorUtility.SetDirty(enemy);
        return 1;
    }

    private static Bounds CalculateBounds(GameObject root)
    {
        var renderers = root.GetComponentsInChildren<Renderer>(true);
        if (renderers.Length == 0)
        {
            return new Bounds(root.transform.position, Vector3.zero);
        }

        var bounds = renderers[0].bounds;
        foreach (var renderer in renderers.Skip(1))
        {
            bounds.Encapsulate(renderer.bounds);
        }

        return bounds;
    }

    private static Bounds CalculateLocalBounds(Transform root)
    {
        var renderers = root.GetComponentsInChildren<Renderer>(true);
        if (renderers.Length == 0)
        {
            return new Bounds(Vector3.zero, Vector3.zero);
        }

        bool initialized = false;
        var bounds = new Bounds();
        foreach (var renderer in renderers)
        {
            var worldBounds = renderer.bounds;
            var corners = new[]
            {
                new Vector3(worldBounds.min.x, worldBounds.min.y, worldBounds.min.z),
                new Vector3(worldBounds.min.x, worldBounds.min.y, worldBounds.max.z),
                new Vector3(worldBounds.min.x, worldBounds.max.y, worldBounds.min.z),
                new Vector3(worldBounds.min.x, worldBounds.max.y, worldBounds.max.z),
                new Vector3(worldBounds.max.x, worldBounds.min.y, worldBounds.min.z),
                new Vector3(worldBounds.max.x, worldBounds.min.y, worldBounds.max.z),
                new Vector3(worldBounds.max.x, worldBounds.max.y, worldBounds.min.z),
                new Vector3(worldBounds.max.x, worldBounds.max.y, worldBounds.max.z),
            };

            foreach (var corner in corners)
            {
                var localCorner = root.InverseTransformPoint(corner);
                if (!initialized)
                {
                    bounds = new Bounds(localCorner, Vector3.zero);
                    initialized = true;
                }
                else
                {
                    bounds.Encapsulate(localCorner);
                }
            }
        }

        return bounds;
    }

    private static float MeasureLongestDimension(GameObject prefab)
    {
        var bounds = MeasureBounds(prefab);
        return Mathf.Max(bounds.size.x, bounds.size.y, bounds.size.z);
    }

    private static Bounds MeasureBounds(GameObject prefab)
    {
        var instance = PrefabUtility.InstantiatePrefab(prefab) as GameObject;
        if (instance == null)
        {
            return new Bounds(Vector3.zero, Vector3.zero);
        }

        try
        {
            return CalculateBounds(instance);
        }
        finally
        {
            UnityEngine.Object.DestroyImmediate(instance);
        }
    }

    private static GameObject FindBestPrefab(IEnumerable<string> searchRoots, IEnumerable<string> keywords)
    {
        var normalized = keywords
            .Where(keyword => !string.IsNullOrWhiteSpace(keyword))
            .Select(keyword => keyword.Trim().ToLowerInvariant())
            .ToArray();
        if (normalized.Length == 0)
        {
            return null;
        }

        var roots = searchRoots.Where(AssetDatabase.IsValidFolder).Distinct().ToArray();
        if (roots.Length == 0)
        {
            return null;
        }

        return AssetDatabase.FindAssets("t:GameObject", roots)
            .Select(AssetDatabase.GUIDToAssetPath)
            .Where(path => path.EndsWith(".prefab", StringComparison.OrdinalIgnoreCase) || path.EndsWith(".fbx", StringComparison.OrdinalIgnoreCase))
            .Select(path => new
            {
                path,
                asset = AssetDatabase.LoadAssetAtPath<GameObject>(path),
                name = Path.GetFileNameWithoutExtension(path).ToLowerInvariant()
            })
            .Where(candidate => candidate.asset != null)
            .Select(candidate => new
            {
                candidate.asset,
                score = normalized.Count(keyword => candidate.name.Contains(keyword))
            })
            .Where(candidate => candidate.score > 0)
            .OrderByDescending(candidate => candidate.score)
            .ThenBy(candidate => candidate.asset.name.Length)
            .Select(candidate => candidate.asset)
            .FirstOrDefault();
    }

    private static Transform FindChildRecursive(Transform root, string name)
    {
        foreach (Transform child in root)
        {
            if (child.name == name)
            {
                return child;
            }

            var nested = FindChildRecursive(child, name);
            if (nested != null)
            {
                return nested;
            }
        }

        return null;
    }

    private static void StripForeignBehaviours(GameObject root)
    {
        foreach (var behaviour in root.GetComponentsInChildren<MonoBehaviour>(true))
        {
            UnityEngine.Object.DestroyImmediate(behaviour);
        }
    }

    private static void AssignLayerRecursively(Transform root, int layer)
    {
        root.gameObject.layer = layer;
        foreach (Transform child in root)
        {
            AssignLayerRecursively(child, layer);
        }
    }

    private static Transform EnsureChild(Transform parent, string name)
    {
        var existing = parent.Find(name);
        if (existing != null)
        {
            return existing;
        }

        var child = new GameObject(name).transform;
        child.SetParent(parent, false);
        child.localPosition = Vector3.zero;
        child.localRotation = Quaternion.identity;
        child.localScale = Vector3.one;
        return child;
    }

    private static void ClearChildren(Transform parent)
    {
        for (int i = parent.childCount - 1; i >= 0; i--)
        {
            UnityEngine.Object.DestroyImmediate(parent.GetChild(i).gameObject);
        }
    }

    private static void PlaceStaticProp(Transform parent, string instanceName, GameObject prefab, Vector3 position, Vector3 rotationEuler, Vector3 targetSize)
    {
        var instance = PrefabUtility.InstantiatePrefab(prefab, parent) as GameObject;
        if (instance == null)
        {
            throw new Exception($"Could not instantiate prefab {prefab.name}");
        }

        instance.name = instanceName;
        StripForeignBehaviours(instance);
        AssignLayerRecursively(instance.transform, parent.gameObject.layer);
        instance.transform.position = position;
        instance.transform.rotation = Quaternion.Euler(rotationEuler);
        instance.transform.localScale = Vector3.one;

        var sourceBounds = CalculateBounds(instance);
        var safeSize = new Vector3(
            Mathf.Max(0.01f, sourceBounds.size.x),
            Mathf.Max(0.01f, sourceBounds.size.y),
            Mathf.Max(0.01f, sourceBounds.size.z));
        float uniformScale = Mathf.Min(targetSize.x / safeSize.x, targetSize.y / safeSize.y, targetSize.z / safeSize.z);
        instance.transform.localScale = Vector3.one * uniformScale;

        var fittedBounds = CalculateBounds(instance);
        instance.transform.position += new Vector3(
            position.x - fittedBounds.center.x,
            position.y - fittedBounds.min.y,
            position.z - fittedBounds.center.z);

        EnsureStaticCollider(instance, CalculateLocalBounds(instance.transform));
        instance.isStatic = true;
    }

    private static void EnsureStaticCollider(GameObject root, Bounds localBounds)
    {
        if (root.GetComponentsInChildren<Collider>(true).Length > 0)
        {
            return;
        }

        var collider = root.GetComponent<BoxCollider>();
        if (collider == null)
        {
            collider = root.AddComponent<BoxCollider>();
        }

        collider.center = localBounds.center;
        collider.size = localBounds.size;
    }
}
