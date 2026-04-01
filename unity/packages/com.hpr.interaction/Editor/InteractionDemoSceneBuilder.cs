namespace HPR
{
    #if UNITY_EDITOR
    using System.IO;
    using UnityEditor;
    using UnityEditor.SceneManagement;
    using UnityEngine;

    public static class InteractionDemoSceneBuilder
    {
        private const string DemoFolder = "Packages/com.hpr.interaction/Demo";
        private const string ScenePath = DemoFolder + "/InteractionDemo.unity";
        private const string TempSceneDirectory = "Assets/__GeneratedPackageDemos";
        private const string TempScenePath = "Assets/__GeneratedPackageDemos/InteractionDemo.unity";
        private const string KeyItemPath = DemoFolder + "/DemoBronzeKey.asset";
        private const string MedkitItemPath = DemoFolder + "/DemoMedkit.asset";

        [MenuItem("Tools/HPR/Interaction/Build Demo Scene")]
        public static void BuildDemoScene()
        {
            var keyItem = EnsureItem(KeyItemPath, "demo_bronze_key", "Bronze Key", ItemType.Key, 1, new Color(0.7f, 0.5f, 0.2f));
            var medkitItem = EnsureItem(MedkitItemPath, "demo_medkit", "Demo Medkit", ItemType.Consumable, 25, new Color(0.7f, 0.15f, 0.15f));

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            var eventRoot = new GameObject("EventBus");
            eventRoot.AddComponent<EventManager>();
            eventRoot.AddComponent<EventBusSourceAdapter>();

            var lightGo = new GameObject("Directional Light");
            var light = lightGo.AddComponent<Light>();
            light.type = LightType.Directional;
            lightGo.transform.rotation = Quaternion.Euler(50f, -30f, 0f);

            var floor = GameObject.CreatePrimitive(PrimitiveType.Plane);
            floor.name = "Floor";
            floor.transform.localScale = new Vector3(2f, 1f, 2f);

            var actorGo = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            actorGo.name = "Actor";
            actorGo.transform.position = new Vector3(0f, 1f, -4f);
            var inventory = actorGo.AddComponent<InventoryComponent>();
            var actor = actorGo.AddComponent<SimpleInteractionActor>();
            var sensor = actorGo.AddComponent<InteractionSensor>();

            var actorSerialized = new SerializedObject(actor);
            actorSerialized.FindProperty("inventory").objectReferenceValue = inventory;
            actorSerialized.ApplyModifiedPropertiesWithoutUndo();

            var inventorySerialized = new SerializedObject(inventory);
            var knownItems = inventorySerialized.FindProperty("knownItems");
            knownItems.arraySize = 2;
            knownItems.GetArrayElementAtIndex(0).objectReferenceValue = keyItem;
            knownItems.GetArrayElementAtIndex(1).objectReferenceValue = medkitItem;
            inventorySerialized.ApplyModifiedPropertiesWithoutUndo();

            var cameraGo = new GameObject("Main Camera");
            cameraGo.tag = "MainCamera";
            cameraGo.transform.SetParent(actorGo.transform, false);
            cameraGo.transform.localPosition = new Vector3(0f, 0.9f, 0f);
            cameraGo.transform.localRotation = Quaternion.identity;
            var camera = cameraGo.AddComponent<Camera>();
            camera.fieldOfView = 65f;

            var sensorSerialized = new SerializedObject(sensor);
            sensorSerialized.FindProperty("sourceCamera").objectReferenceValue = camera;
            sensorSerialized.ApplyModifiedPropertiesWithoutUndo();

            var pickup = GameObject.CreatePrimitive(PrimitiveType.Cube);
            pickup.name = "MedkitPickup";
            pickup.transform.position = new Vector3(0f, 0.6f, 0f);
            pickup.transform.localScale = new Vector3(0.4f, 0.4f, 0.4f);
            pickup.AddComponent<InventoryPickupInteractable>();
            var pickupSerialized = new SerializedObject(pickup.GetComponent<InventoryPickupInteractable>());
            pickupSerialized.FindProperty("itemData").objectReferenceValue = medkitItem;
            pickupSerialized.FindProperty("amount").intValue = 1;
            pickupSerialized.FindProperty("eventBusSourceBehaviour").objectReferenceValue = eventRoot.GetComponent<EventBusSourceAdapter>();
            pickupSerialized.ApplyModifiedPropertiesWithoutUndo();

            var keyPickup = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            keyPickup.name = "KeyPickup";
            keyPickup.transform.position = new Vector3(-2f, 0.5f, 1f);
            keyPickup.transform.localScale = new Vector3(0.3f, 0.05f, 0.3f);
            keyPickup.AddComponent<InventoryPickupInteractable>();
            var keyPickupSerialized = new SerializedObject(keyPickup.GetComponent<InventoryPickupInteractable>());
            keyPickupSerialized.FindProperty("itemData").objectReferenceValue = keyItem;
            keyPickupSerialized.FindProperty("amount").intValue = 1;
            keyPickupSerialized.FindProperty("eventBusSourceBehaviour").objectReferenceValue = eventRoot.GetComponent<EventBusSourceAdapter>();
            keyPickupSerialized.ApplyModifiedPropertiesWithoutUndo();

            var doorPivot = new GameObject("Door");
            doorPivot.transform.position = new Vector3(2f, 0f, 2f);
            var frame = GameObject.CreatePrimitive(PrimitiveType.Cube);
            frame.name = "Frame";
            frame.transform.SetParent(doorPivot.transform, false);
            frame.transform.localPosition = new Vector3(0f, 1.25f, 0f);
            frame.transform.localScale = new Vector3(2.4f, 2.6f, 0.25f);
            var leaf = GameObject.CreatePrimitive(PrimitiveType.Cube);
            leaf.name = "Leaf";
            leaf.transform.SetParent(doorPivot.transform, false);
            leaf.transform.localPosition = new Vector3(-0.5f, 1f, 0f);
            leaf.transform.localScale = new Vector3(1f, 2f, 0.12f);
            var door = doorPivot.AddComponent<KeyDoorInteractable>();
            var doorSerialized = new SerializedObject(door);
            doorSerialized.FindProperty("requiredKeyItem").objectReferenceValue = keyItem;
            doorSerialized.FindProperty("doorLeaf").objectReferenceValue = leaf.transform;
            doorSerialized.ApplyModifiedPropertiesWithoutUndo();

            var demoControllerGo = new GameObject("InteractionDemoController");
            var demoController = demoControllerGo.AddComponent<InteractionDemoController>();
            var demoSerialized = new SerializedObject(demoController);
            demoSerialized.FindProperty("actor").objectReferenceValue = actor;
            demoSerialized.FindProperty("sensor").objectReferenceValue = sensor;
            demoSerialized.FindProperty("actorCamera").objectReferenceValue = camera;
            demoSerialized.FindProperty("medkitPickup").objectReferenceValue = pickup.GetComponent<InventoryPickupInteractable>();
            demoSerialized.FindProperty("keyPickup").objectReferenceValue = keyPickup.GetComponent<InventoryPickupInteractable>();
            demoSerialized.FindProperty("door").objectReferenceValue = door;
            var demoItems = demoSerialized.FindProperty("demoItems");
            demoItems.arraySize = 2;
            demoItems.GetArrayElementAtIndex(0).objectReferenceValue = keyItem;
            demoItems.GetArrayElementAtIndex(1).objectReferenceValue = medkitItem;
            demoSerialized.ApplyModifiedPropertiesWithoutUndo();

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
            Debug.Log($"Interaction demo scene written to {ScenePath}");
        }

        private static ItemData EnsureItem(string path, string id, string displayName, ItemType itemType, int value, Color color)
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
            item.Description = $"Demo item for {displayName}.";
            item.PickupPrompt = $"Pick up {displayName}";
            item.PickupStatus = $"Collected {displayName}";
            item.PlaceholderColor = color;
            EditorUtility.SetDirty(item);
            return item;
        }
    }
    #endif
}
