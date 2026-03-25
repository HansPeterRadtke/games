using System;
using System.Collections.Generic;
using System.Linq;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;

public static class ThirdPartyAssetIntegrator
{
    private const string MainScenePath = "Assets/Scenes/Gameplay.unity";
    private static readonly string[] FurnitureSearchRoots =
    {
        "Assets/Furniture Mega Pack - Free",
        "Assets/Furniture Mega Pack",
        "Assets/dlgames",
        "Assets/dlgames/Furniture Mega Pack - Free"
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
        "Assets/nappin",
        "Assets/nappin/HouseInteriorPack",
        "Assets/FurnishedCabin",
        "Assets/Furnished Cabin",
        "Assets/Brick Project Studio",
        "Assets/Brick Project Studio/Apartment Kit",
        "Assets/Apartment Kit",
    };
    private static readonly string[] VistaSearchRoots =
    {
        "Assets/CITY package",
        "Assets/CITY Package",
        "Assets/NatureStarterKit2",
        "Assets/Nature Starter Kit 2",
        "Assets/Unity Terrain - URP Demo Scene",
        "Assets/Realistic Terrain Textures FREE",
        "Assets/Grass Flowers Pack Free",
        "Assets/Flooded_Grounds",
        "Assets/Flooded Grounds",
    };
    private static readonly string[] CharacterSearchRoots =
    {
        "Assets/npc_casual_set_00",
        "Assets/Survivalist",
        "Assets/Survivalist/Prefab",
        "Assets/Survivalist character",
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

        NormalizeImportedMaterials(FurnitureSearchRoots.Concat(HouseSearchRoots));

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
        placed += TryPlaceFurniture(hubRoot, "hub_table", FurniturePrefab("Tables/Table10.prefab"), new[] { "table" }, new Vector3(0f, 0f, 3.2f), Vector3.zero, new Vector3(1.46f, 0.78f, 1.18f));
        placed += TryPlaceFurniture(hubRoot, "hub_chair_left", FurniturePrefab("Chairs/Chair09.prefab"), new[] { "chair" }, new Vector3(-1.02f, 0f, 2.38f), new Vector3(0f, 30f, 0f), new Vector3(0.58f, 1.02f, 0.58f));
        placed += TryPlaceFurniture(hubRoot, "hub_chair_right", FurniturePrefab("Chairs/Chair09.prefab"), new[] { "chair" }, new Vector3(1.02f, 0f, 2.38f), new Vector3(0f, -30f, 0f), new Vector3(0.58f, 1.02f, 0.58f));
        placed += TryPlaceFurniture(medbayRoot, "medbay_cabinet_a", FurniturePrefab("Closets/Closet05.prefab"), new[] { "cabinet", "locker" }, new Vector3(-24.4f, 0f, 4f), new Vector3(0f, 90f, 0f), new Vector3(1.08f, 2.02f, 0.56f));
        placed += TryPlaceFurniture(medbayRoot, "medbay_cabinet_b", FurniturePrefab("Closets/Closet05.prefab"), new[] { "cabinet", "locker" }, new Vector3(-24.4f, 0f, -2.6f), new Vector3(0f, 90f, 0f), new Vector3(1.08f, 2.02f, 0.56f));
        placed += TryPlaceFurniture(medbayRoot, "medbay_bed", FurniturePrefab("Beds/Bed05.prefab"), new[] { "bed" }, new Vector3(-17.8f, 0f, 2.2f), new Vector3(0f, 180f, 0f), new Vector3(2.04f, 0.74f, 0.98f));
        placed += TryPlaceFurniture(securityRoot, "security_desk", FurniturePrefab("Tables/Table23.prefab"), new[] { "desk", "table" }, new Vector3(-2.2f, 0f, 23.8f), new Vector3(0f, 180f, 0f), new Vector3(1.38f, 0.76f, 0.72f));
        placed += TryPlaceFurniture(securityRoot, "security_chair", FurniturePrefab("Chairs/Chair04.prefab"), new[] { "chair" }, new Vector3(-2.2f, 0f, 22.48f), Vector3.zero, new Vector3(0.56f, 1f, 0.56f));
        placed += TryPlaceFurniture(securityRoot, "security_shelf", FurniturePrefab("Closets/Closet21.prefab"), new[] { "shelf", "book" }, new Vector3(6.8f, 0f, 25.1f), new Vector3(0f, 180f, 0f), new Vector3(1.12f, 2.02f, 0.42f));
        placed += TryPlaceFurniture(armoryRoot, "armory_shelf_a", FurniturePrefab("Closets/Closet31.prefab"), new[] { "shelf", "rack" }, new Vector3(24.2f, 0f, 4.8f), new Vector3(0f, -90f, 0f), new Vector3(1.18f, 2.02f, 0.48f));
        placed += TryPlaceFurniture(armoryRoot, "armory_shelf_b", FurniturePrefab("Closets/Closet31.prefab"), new[] { "shelf", "rack" }, new Vector3(24.2f, 0f, -3.8f), new Vector3(0f, -90f, 0f), new Vector3(1.18f, 2.02f, 0.48f));
        placed += TryPlaceFurniture(armoryRoot, "armory_table", FurniturePrefab("Tables/Table25.prefab"), new[] { "table", "bench" }, new Vector3(18.5f, 0f, -1.2f), new Vector3(0f, 90f, 0f), new Vector3(1.52f, 0.8f, 0.72f));
        placed += TryPlaceFurniture(powerRoot, "power_cabinet", FurniturePrefab("Closets/Closet12.prefab"), new[] { "cabinet", "locker" }, new Vector3(4.6f, 0f, -24.4f), Vector3.zero, new Vector3(0.98f, 2f, 0.52f));
        placed += TryPlaceFurniture(powerRoot, "power_table", FurniturePrefab("Tables/Table45.prefab"), new[] { "table", "desk" }, new Vector3(-3.8f, 0f, -23.8f), Vector3.zero, new Vector3(1.46f, 0.78f, 0.76f));

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
        updated += TryApplyWeaponVisual("weapon_pulse_pistol", new[] { "M1911" }, new[] { "pistol", "handgun" }, 0.42f, new Vector3(0f, 195f, 0f));
        updated += TryApplyWeaponVisual("weapon_scatter_shot", new[] { "Bennelli_M4" }, new[] { "shotgun" }, 0.62f, new Vector3(5f, 180f, -12f));
        updated += TryApplyWeaponVisual("weapon_needler", new[] { "Uzi", "M4_8", "AK74" }, new[] { "uzi", "smg", "submachine", "rifle" }, 0.62f, new Vector3(0f, 192f, 12f));
        updated += TryApplyWeaponVisual("weapon_arc_launcher", new[] { "RPG7" }, new[] { "launcher", "rocket", "rpg", "bazooka" }, 0.7f, new Vector3(-10f, 180f, -90f));
        updated += TryApplyWeaponVisual("weapon_repair_tool", new[] { "ANPEQ15", "ELCAN" }, new[] { "tool", "scope", "laser" }, 0.28f, new Vector3(0f, 180f, -70f));

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
        placed += TryPlaceProp(VistaSearchRoots, vistaRoot, "vista_block_a", new[] { "Assets/Brick Project Studio/Apartment Kit/_Prefabs/Apt Build Kit/Exteriors/Special/Ext_apt_01_01.prefab" }, new[] { "building", "house" }, new Vector3(0f, 0f, 58f), Vector3.zero, new Vector3(26f, 22f, 18f));
        placed += TryPlaceProp(VistaSearchRoots, vistaRoot, "vista_block_b", new[] { "Assets/Brick Project Studio/Apartment Kit/_Prefabs/Apt Build Kit/Exteriors/Special/Ext_apt_01_02.prefab" }, new[] { "building", "house" }, new Vector3(42f, 0f, 26f), new Vector3(0f, 35f, 0f), new Vector3(20f, 18f, 16f));
        placed += TryPlaceProp(VistaSearchRoots, vistaRoot, "vista_tree_cluster", Array.Empty<string>(), new[] { "tree", "pine", "oak" }, new Vector3(-36f, 0f, 30f), Vector3.zero, new Vector3(10f, 14f, 10f));
        placed += TryPlaceProp(VistaSearchRoots, vistaRoot, "vista_rock_cluster", Array.Empty<string>(), new[] { "rock", "stone" }, new Vector3(-26f, 0f, 52f), Vector3.zero, new Vector3(8f, 5f, 8f));

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
        updated += TryApplyEnemyVisual("enemy_sentry_hub", new[] { "female", "woman", "casual", "npc" }, new[] { "npc_csl_00_character_01f_02", "npc_csl_tshirt_00f_01_02" }, 1.72f, 0f);
        updated += TryApplyEnemyVisual("enemy_medbay_intruder", new[] { "female", "casual", "npc" }, new[] { "npc_csl_00_character_02f_01", "npc_csl_tshirt_00f_01_03" }, 1.7f, 0f);
        updated += TryApplyEnemyVisual("enemy_security_guard", new[] { "male", "survival", "guard", "casual" }, new[] { "Survivalist (1)", "npc_csl_00_character_01m_02" }, 1.8f, 0f);
        updated += TryApplyEnemyVisual("enemy_sweeper_armory", new[] { "male", "survival", "worker", "casual" }, new[] { "Survivalist (2)", "npc_csl_00_character_02m_03" }, 1.8f, 0f);
        updated += TryApplyEnemyVisual("enemy_power_walker", new[] { "male", "worker", "casual", "survival" }, new[] { "Survivalist (4)", "npc_csl_00_character_02m_01" }, 1.82f, 0f);

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

    [MenuItem("HPR/Integrate/Apply Interior Packs From Batch")]
    public static void ApplyInteriorPacksFromBatch()
    {
        ApplyHousePack();
        ApplyFurniturePack();
    }

    [MenuItem("HPR/Integrate/Apply Selected Local Packs From Batch")]
    public static void ApplySelectedLocalPacksFromBatch()
    {
        ApplyDoorPack();
        ApplyWeaponPack();
        ApplyCharacterPacks();
        ApplyHousePack();
        ApplyFurniturePack();
    }

    private static string[] FurniturePrefab(string relativePath)
    {
        return new[]
        {
            $"Assets/Furniture Mega Pack/Prefabs/{relativePath}",
            $"Assets/Furniture Mega Pack - Free/Prefabs/{relativePath}",
            $"Assets/dlgames/Furniture Mega Pack - Free/Prefabs/{relativePath}"
        };
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

    private static int TryPlaceFurniture(Transform parent, string instanceName, string[] preferredPrefabPaths, string[] keywords, Vector3 position, Vector3 rotationEuler, Vector3 targetSize)
    {
        var prefab = TryLoadAssetAtAnyPath(preferredPrefabPaths) ?? FindBestPrefab(FurnitureSearchRoots, keywords);
        if (prefab == null)
        {
            return 0;
        }

        PlaceStaticProp(parent, instanceName, prefab, position, rotationEuler, targetSize);
        return 1;
    }

    private static int TryPlaceProp(IEnumerable<string> searchRoots, Transform parent, string instanceName, string[] preferredPrefabPaths, string[] keywords, Vector3 position, Vector3 rotationEuler, Vector3 targetSize)
    {
        var prefab = TryLoadAssetAtAnyPath(preferredPrefabPaths) ?? FindBestPrefab(searchRoots, keywords);
        if (prefab == null)
        {
            return 0;
        }

        PlaceStaticProp(parent, instanceName, prefab, position, rotationEuler, targetSize);
        return 1;
    }

    private static int TryApplyWeaponVisual(string weaponId, string[] preferredPrefabNames, string[] keywords, float targetLength, Vector3? localEulerOverride = null)
    {
        var prefab = FindBestPrefab(WeaponSearchRoots, keywords, preferredPrefabNames);
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
        if (localEulerOverride.HasValue)
        {
            weapon.ViewLocalEuler = localEulerOverride.Value;
        }
        if (weapon.ViewMuzzleLocalPosition == Vector3.zero)
        {
            weapon.ViewMuzzleLocalPosition = new Vector3(0f, 0.01f, targetLength * 0.55f);
        }

        EditorUtility.SetDirty(weapon);
        return 1;
    }

    private static int TryApplyEnemyVisual(string enemyId, string[] keywords, string[] preferredPrefabNames, float targetHeight, float yawDegrees)
    {
        var prefab = FindBestPrefab(CharacterSearchRoots, keywords, preferredPrefabNames);
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

    private static GameObject FindBestPrefab(IEnumerable<string> searchRoots, IEnumerable<string> keywords, IEnumerable<string> preferredPrefabNames = null)
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

        var preferred = (preferredPrefabNames ?? Array.Empty<string>())
            .Where(name => !string.IsNullOrWhiteSpace(name))
            .Select(name => name.Trim().ToLowerInvariant())
            .ToArray();

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
                score = normalized.Count(keyword => candidate.name.Contains(keyword)),
                preferredScore = preferred.Any(name => candidate.name == name) ? 2 :
                    preferred.Count(name => candidate.name.Contains(name))
            })
            .Where(candidate => candidate.score > 0 || candidate.preferredScore > 0)
            .OrderByDescending(candidate => candidate.preferredScore)
            .ThenByDescending(candidate => candidate.score)
            .ThenBy(candidate => candidate.asset.name.Length)
            .Select(candidate => candidate.asset)
            .FirstOrDefault();
    }

    private static GameObject TryLoadAssetAtAnyPath(IEnumerable<string> preferredPaths)
    {
        if (preferredPaths == null)
        {
            return null;
        }

        foreach (var path in preferredPaths)
        {
            if (string.IsNullOrWhiteSpace(path))
            {
                continue;
            }

            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(path);
            if (prefab != null)
            {
                return prefab;
            }
        }

        return null;
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

    private static void NormalizeImportedMaterials(IEnumerable<string> searchRoots)
    {
        var roots = searchRoots.Where(AssetDatabase.IsValidFolder).Distinct().ToArray();
        if (roots.Length == 0)
        {
            return;
        }

        var standardShader = Shader.Find("Standard");
        var urpLitShader = Shader.Find("Universal Render Pipeline/Lit");
        foreach (var guid in AssetDatabase.FindAssets("t:Material", roots))
        {
            var path = AssetDatabase.GUIDToAssetPath(guid);
            var material = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (material == null)
            {
                continue;
            }

            bool invalidShader = material.shader == null || material.shader.name.StartsWith("Hidden/InternalErrorShader", StringComparison.OrdinalIgnoreCase);
            bool unsupportedPipelineShader = material.shader != null &&
                (material.shader.name.Contains("Universal Render Pipeline", StringComparison.OrdinalIgnoreCase) ||
                 material.shader.name.Contains("HDRP", StringComparison.OrdinalIgnoreCase));
            if (invalidShader || unsupportedPipelineShader)
            {
                if (standardShader != null && (invalidShader || urpLitShader == null))
                {
                    material.shader = standardShader;
                }
                else if (urpLitShader != null)
                {
                    material.shader = urpLitShader;
                }
            }

            var baseMap = ResolveBestTexture(material);
            if (baseMap != null && material.HasProperty("_MainTex"))
            {
                material.SetTexture("_MainTex", baseMap);
            }
            if (baseMap != null && material.HasProperty("_BaseMap"))
            {
                material.SetTexture("_BaseMap", baseMap);
            }

            var normalMap = material.HasProperty("_BumpMap") ? material.GetTexture("_BumpMap") : null;
            if (normalMap == null && material.HasProperty("_Normal_Map"))
            {
                normalMap = material.GetTexture("_Normal_Map");
            }
            if (normalMap != null && material.HasProperty("_BumpMap"))
            {
                material.SetTexture("_BumpMap", normalMap);
                material.EnableKeyword("_NORMALMAP");
            }

            var metallicMap = material.HasProperty("_MetallicGlossMap") ? material.GetTexture("_MetallicGlossMap") : null;
            if (metallicMap == null && material.HasProperty("_Metallic_Map"))
            {
                metallicMap = material.GetTexture("_Metallic_Map");
            }
            if (metallicMap != null && material.HasProperty("_MetallicGlossMap"))
            {
                material.SetTexture("_MetallicGlossMap", metallicMap);
                material.EnableKeyword("_METALLICGLOSSMAP");
            }

            var color = ResolveBestColor(material);
            if (material.HasProperty("_Color"))
            {
                material.SetColor("_Color", color);
            }
            if (material.HasProperty("_BaseColor"))
            {
                material.SetColor("_BaseColor", color);
            }

            if (material.shader != null && material.shader.name == "Standard")
            {
                material.SetFloat("_Glossiness", Mathf.Clamp(material.GetFloat("_Glossiness"), 0.05f, 0.45f));
            }

            EditorUtility.SetDirty(material);
        }
    }

    private static Texture ResolveBestTexture(Material material)
    {
        if (material == null)
        {
            return null;
        }

        foreach (var propertyName in new[]
                 {
                     "_MainTex",
                     "_BaseMap",
                     "_Base_Map",
                     "_BaseColorMap",
                     "_BaseColorTexture",
                     "_ColorMap",
                     "_Albedo",
                     "_AlbedoMap",
                     "_Diffuse",
                     "_DiffuseMap",
                     "_BaseTex"
                 })
        {
            if (!material.HasProperty(propertyName))
            {
                continue;
            }

            var texture = material.GetTexture(propertyName);
            if (texture != null)
            {
                return texture;
            }
        }

        if (material.shader == null)
        {
            return null;
        }

        for (int i = 0; i < material.shader.GetPropertyCount(); i++)
        {
            if (material.shader.GetPropertyType(i) != ShaderPropertyType.Texture)
            {
                continue;
            }

            string propertyName = material.shader.GetPropertyName(i);
            string lowered = propertyName.ToLowerInvariant();
            if (!lowered.Contains("base") && !lowered.Contains("albedo") && !lowered.Contains("diffuse") && !lowered.Contains("color"))
            {
                continue;
            }

            var texture = material.GetTexture(propertyName);
            if (texture != null)
            {
                return texture;
            }
        }

        return null;
    }

    private static Color ResolveBestColor(Material material)
    {
        if (material == null)
        {
            return Color.white;
        }

        foreach (var propertyName in new[] { "_Color", "_BaseColor", "_TintColor" })
        {
            if (!material.HasProperty(propertyName))
            {
                continue;
            }

            var color = material.GetColor(propertyName);
            if (color.maxColorComponent > 0.01f)
            {
                return color;
            }
        }

        return Color.white;
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
