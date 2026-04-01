namespace HPR
{
    #if UNITY_EDITOR
    using System.IO;
    using UnityEditor;
    using UnityEditor.SceneManagement;
    using UnityEngine;

    public static class InventoryDemoSceneBuilder
    {
        private const string DemoFolder = "Packages/com.hpr.inventory/Demo";
        private const string ScenePath = DemoFolder + "/InventoryDemo.unity";
        private const string TempSceneDirectory = "Assets/__GeneratedPackageDemos";
        private const string TempScenePath = "Assets/__GeneratedPackageDemos/InventoryDemo.unity";
        private const string PotionPath = DemoFolder + "/HealthPotion.asset";
        private const string AmmoPath = DemoFolder + "/RifleAmmo.asset";
        private const string KeyPath = DemoFolder + "/SilverKey.asset";

        [MenuItem("Tools/HPR/Inventory/Build Demo Scene")]
        public static void BuildDemoScene()
        {
            var potion = EnsureItem(PotionPath, "health_potion", "Health Potion", ItemType.Consumable, 25, 2, new Color(0.75f, 0.15f, 0.15f));
            var ammo = EnsureItem(AmmoPath, "rifle_ammo", "Rifle Ammo", ItemType.Ammo, 12, 0, new Color(0.2f, 0.2f, 0.2f));
            var key = EnsureItem(KeyPath, "silver_key", "Silver Key", ItemType.Key, 1, 1, new Color(0.7f, 0.7f, 0.9f));

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var root = new GameObject("InventoryDemoRoot");

            var inventoryGo = new GameObject("Inventory");
            inventoryGo.transform.SetParent(root.transform);
            var inventory = inventoryGo.AddComponent<InventoryComponent>();

            var controllerGo = new GameObject("InventoryDemoController");
            controllerGo.transform.SetParent(root.transform);
            var controller = controllerGo.AddComponent<InventoryDemoController>();

            var cameraGo = new GameObject("Main Camera");
            cameraGo.tag = "MainCamera";
            cameraGo.transform.position = new Vector3(0f, 0f, -10f);
            cameraGo.AddComponent<Camera>();

            var inventorySerialized = new SerializedObject(inventory);
            var knownItems = inventorySerialized.FindProperty("knownItems");
            knownItems.arraySize = 3;
            knownItems.GetArrayElementAtIndex(0).objectReferenceValue = potion;
            knownItems.GetArrayElementAtIndex(1).objectReferenceValue = ammo;
            knownItems.GetArrayElementAtIndex(2).objectReferenceValue = key;
            inventorySerialized.ApplyModifiedPropertiesWithoutUndo();

            var controllerSerialized = new SerializedObject(controller);
            controllerSerialized.FindProperty("inventory").objectReferenceValue = inventory;
            var demoItems = controllerSerialized.FindProperty("demoItems");
            demoItems.arraySize = 3;
            demoItems.GetArrayElementAtIndex(0).objectReferenceValue = potion;
            demoItems.GetArrayElementAtIndex(1).objectReferenceValue = ammo;
            demoItems.GetArrayElementAtIndex(2).objectReferenceValue = key;
            controllerSerialized.ApplyModifiedPropertiesWithoutUndo();

            Directory.CreateDirectory(Path.GetDirectoryName(TempScenePath) ?? "Assets");
            EditorSceneManager.SaveScene(scene, TempScenePath);
            AssetDatabase.Refresh();

            var sourceAbsolutePath = Path.GetFullPath(Path.Combine(Application.dataPath, "..", TempScenePath));
            var targetAbsolutePath = Path.GetFullPath(Path.Combine(Application.dataPath, "..", ScenePath));
            Directory.CreateDirectory(Path.GetDirectoryName(targetAbsolutePath) ?? Path.GetFullPath(Path.Combine(Application.dataPath, "..")));
            File.Copy(sourceAbsolutePath, targetAbsolutePath, true);

            var sourceMetaPath = $"{sourceAbsolutePath}.meta";
            var targetMetaPath = $"{targetAbsolutePath}.meta";
            if (!File.Exists(targetMetaPath) && File.Exists(sourceMetaPath))
            {
                File.Copy(sourceMetaPath, targetMetaPath, false);
            }

            AssetDatabase.DeleteAsset(TempScenePath);
            AssetDatabase.DeleteAsset(TempSceneDirectory);
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log($"Inventory demo scene written to {ScenePath}");
        }

        private static ItemData EnsureItem(string path, string id, string displayName, ItemType itemType, int value, int startingQuantity, Color color)
        {
            var item = AssetDatabase.LoadAssetAtPath<ItemData>(path);
            if (item == null)
            {
                item = ScriptableObject.CreateInstance<ItemData>();
                AssetDatabase.CreateAsset(item, path);
            }

            item.Id = id;
            item.ItemType = itemType;
            item.DisplayName = displayName;
            item.Value = value;
            item.StartingPlayerQuantity = startingQuantity;
            item.PickupPrompt = $"Pick up {displayName}";
            item.PickupStatus = $"Collected {displayName}";
            item.Description = $"Demo item for {displayName}.";
            item.PlaceholderColor = color;
            EditorUtility.SetDirty(item);
            return item;
        }
    }
    #endif
}
