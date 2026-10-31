// Copyright (c) Multiverse Studio. All rights reserved.
// Original self-contained training arena built entirely from Unity primitives.
#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using HPR;

namespace HPR.GameplaySuite
{
    public static class HprGameplaySuiteSceneBuilder
    {
        private const string Root = "Assets/HPRGameplaySuite";
        private const string Samples = Root + "/Samples";
        private const string Scene = Root + "/Demo/GameplaySuiteShowcase.unity";

        private static T CreateAsset<T>(string filename) where T : ScriptableObject
        {
            string path = Samples + "/" + filename + ".asset";
            T data = AssetDatabase.LoadAssetAtPath<T>(path);
            if (data != null) return data;
            data = ScriptableObject.CreateInstance<T>();
            AssetDatabase.CreateAsset(data, path);
            return data;
        }

        private static Material CreateMaterial(string name, Color color, float metallic = 0f)
        {
            string path = Samples + "/" + name + ".mat";
            Material material = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (material == null)
            {
                Shader shader = Shader.Find("Standard") ?? Shader.Find("Universal Render Pipeline/Lit") ??
                    Shader.Find("Unlit/Color");
                if (shader == null) throw new InvalidOperationException("Unity has no supported demo shader");
                material = new Material(shader);
                AssetDatabase.CreateAsset(material, path);
            }
            material.color = color;
            if (material.HasProperty("_Metallic")) material.SetFloat("_Metallic", metallic);
            if (material.HasProperty("_Glossiness")) material.SetFloat("_Glossiness", 0.4f);
            EditorUtility.SetDirty(material);
            return material;
        }

        private static GameObject Shape(string name, PrimitiveType type, Vector3 pos, Vector3 scale, Material material,
            Transform parent = null)
        {
            GameObject obj = GameObject.CreatePrimitive(type);
            obj.name = name;
            if (parent != null) obj.transform.SetParent(parent, false);
            obj.transform.position = pos;
            obj.transform.localScale = scale;
            obj.GetComponent<Renderer>().sharedMaterial = material;
            return obj;
        }

        private static void SetRef(Component component, string property, UnityEngine.Object value)
        {
            var data = new SerializedObject(component);
            SerializedProperty field = data.FindProperty(property);
            if (field == null) throw new MissingFieldException(component.GetType().Name, property);
            field.objectReferenceValue = value;
            data.ApplyModifiedPropertiesWithoutUndo();
            EditorUtility.SetDirty(component);
        }

        [MenuItem("Tools/HPR/Gameplay Suite/Build Showcase")]
        public static void BuildShowcase()
        {
            Directory.CreateDirectory(Samples);
            Directory.CreateDirectory(Root + "/Demo");
            AssetDatabase.Refresh();
            Material floorMat = CreateMaterial("ArenaDarkSlate", new Color(.11f, .16f, .22f));
            Material trimMat = CreateMaterial("ArenaSteel", new Color(.26f, .32f, .39f), .35f);
            Material wallMat = CreateMaterial("ArenaWall", new Color(.17f, .24f, .32f));
            Material cyanMat = CreateMaterial("ArenaCyan", new Color(.1f, .74f, .82f));
            Material amberMat = CreateMaterial("ArenaAmber", new Color(.98f, .67f, .17f));
            Material redMat = CreateMaterial("ArenaEnemy", new Color(.98f, .32f, .18f));
            Material blueMat = CreateMaterial("ArenaPlayer", new Color(.22f, .55f, .96f));

            ItemData medkit = CreateAsset<ItemData>("FieldMedkit");
            medkit.Id = "hpr_suite_field_medkit";
            medkit.DisplayName = "Field Medkit";
            medkit.Description = "Collect from the cyan supply station or defeat the enemy; restores 30 health.";
            medkit.ItemType = ItemType.Consumable;
            medkit.StartingPlayerQuantity = 0;
            EditorUtility.SetDirty(medkit);

            ItemData key = CreateAsset<ItemData>("TrainingKey");
            key.Id = "hpr_suite_training_key";
            key.DisplayName = "Training Key";
            key.Description = "Pick up the amber key to unlock the training gate.";
            key.ItemType = ItemType.Key;
            key.StartingPlayerQuantity = 0;
            EditorUtility.SetDirty(key);

            WeaponData rifle = CreateAsset<WeaponData>("DemoRifle");
            rifle.Id = "hpr_suite_demo_rifle";
            rifle.DisplayName = "Training Rifle";
            rifle.Damage = 15f;
            rifle.Range = 50f;
            rifle.FireDelay = 0.35f;
            rifle.MagazineSize = 6;
            rifle.StartingMagazineAmmo = 6;
            rifle.StartingReserveAmmo = 30;
            rifle.MaxAmmo = 60;
            rifle.UsesAmmo = true;
            EditorUtility.SetDirty(rifle);

            EnemyData raider = CreateAsset<EnemyData>("DemoRaider");
            raider.Id = "hpr_suite_demo_raider";
            raider.DisplayName = "Training Target";
            raider.MaxHealth = 60f;
            raider.AttackRange = 2.5f;
            raider.ChaseRange = 10f;
            raider.AttackDamage = 8f;
            raider.AttackCooldown = 1f;
            raider.AIType = EnemyAIType.PatrolChase;
            EditorUtility.SetDirty(raider);

            AbilityEffectData healEffect = CreateAsset<AbilityEffectData>("RepairEffect");
            healEffect.Id = "hpr_suite_repair_effect";
            healEffect.DisplayName = "Recovery";
            healEffect.EffectType = AbilityEffectType.Heal;
            healEffect.Value = 20f;
            EditorUtility.SetDirty(healEffect);

            AbilityData heal = CreateAsset<AbilityData>("RepairAbility");
            heal.Id = "hpr_suite_repair";
            heal.DisplayName = "Field Recovery";
            heal.Description = "Spend twenty stamina to restore twenty health. Four-second cooldown.";
            heal.Cost = 20f;
            heal.Cooldown = 4f;
            heal.Effects.Clear();
            heal.Effects.Add(healEffect);
            EditorUtility.SetDirty(heal);

            AbilityEffectData pulseEffect = CreateAsset<AbilityEffectData>("PulseEffect");
            pulseEffect.Id = "hpr_suite_pulse_effect";
            pulseEffect.DisplayName = "Pulse";
            pulseEffect.EffectType = AbilityEffectType.AreaDamage;
            pulseEffect.Value = 12f;
            pulseEffect.Radius = 7f;
            pulseEffect.ForwardOffset = 0f;
            EditorUtility.SetDirty(pulseEffect);

            AbilityData pulse = CreateAsset<AbilityData>("PulseAbility");
            pulse.Id = "hpr_suite_pulse";
            pulse.DisplayName = "Damage Pulse";
            pulse.Description = "Area damage to the target through a typed DamageEvent. Six-second cooldown.";
            pulse.Cost = 25f;
            pulse.Cooldown = 6f;
            pulse.TargetType = AbilityTargetType.Area;
            pulse.Effects.Clear();
            pulse.Effects.Add(pulseEffect);
            EditorUtility.SetDirty(pulse);

            AssetMetadata medkitMetadata = CreateAsset<AssetMetadata>("WorldMedkitMetadata");
            medkitMetadata.AssetId = medkit.Id;
            medkitMetadata.DisplayName = medkit.DisplayName;
            medkitMetadata.AssetType = AssetType.Prop;
            EditorUtility.SetDirty(medkitMetadata);
            AssetRegistry catalog = CreateAsset<AssetRegistry>("TrainingWorldRegistry");
            catalog.SetEntries(new[] { medkitMetadata });
            EditorUtility.SetDirty(catalog);

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            Shape("Arena / dark floor", PrimitiveType.Plane, Vector3.zero, new Vector3(1.7f, 1f, 1.2f), floorMat);
            Shape("North safety boundary", PrimitiveType.Cube, new Vector3(0, .55f, 6f), new Vector3(17f, 1.1f, .3f), wallMat);
            Shape("South safety boundary", PrimitiveType.Cube, new Vector3(0, .55f, -6f), new Vector3(17f, 1.1f, .3f), wallMat);
            Shape("West safety boundary", PrimitiveType.Cube, new Vector3(-8.5f, .55f, 0), new Vector3(.25f, 1.1f, 12f), wallMat);
            Shape("East safety boundary", PrimitiveType.Cube, new Vector3(8.5f, .55f, 0), new Vector3(.25f, 1.1f, 12f), wallMat);
            Shape("Arena center stripe", PrimitiveType.Cube, new Vector3(0, .025f, 0), new Vector3(.08f, .045f, 10f), trimMat);
            Shape("Player zone highlight", PrimitiveType.Cube, new Vector3(-4f, .025f, 0), new Vector3(5f, .045f, .12f), cyanMat);
            Shape("Enemy zone highlight", PrimitiveType.Cube, new Vector3(3f, .025f, 0), new Vector3(5f, .045f, .12f), amberMat);
            Shape("Training cargo block", PrimitiveType.Cube, new Vector3(0.6f, .45f, 3.4f), new Vector3(1.5f, .9f, 1.4f), trimMat);

            GameObject player = Shape("Player / Stats, Inventory, Abilities, EventBus", PrimitiveType.Capsule,
                new Vector3(-4f, 1f, 0f), Vector3.one, blueMat);
            player.AddComponent<EventManager>();
            player.AddComponent<InventoryComponent>();
            player.AddComponent<ActorStatsComponent>();
            player.AddComponent<SimpleInteractionActor>();
            player.AddComponent<HprSuiteAbilityPool>();
            player.AddComponent<AbilityRunnerComponent>();

            GameObject enemy = Shape("Target / EnemyRuntime and damageable adapter", PrimitiveType.Capsule,
                new Vector3(3.3f, 1f, 0), new Vector3(1.2f, 1.1f, 1.2f), redMat);
            enemy.AddComponent<HprSuiteEnemyTarget>();

            GameObject medkitStation = Shape("Cyan station / interact to collect medkit", PrimitiveType.Cube,
                new Vector3(-4.0f, .55f, 2.3f), new Vector3(1f, 1.1f, 1f), cyanMat);
            var medkitPickup = medkitStation.AddComponent<InventoryPickupInteractable>();
            SetRef(medkitPickup, "itemData", medkit);

            GameObject keyStation = Shape("Amber station / interact to collect key", PrimitiveType.Cube,
                new Vector3(-2f, .45f, -2.1f), new Vector3(.9f, .9f, .9f), amberMat);
            var keyPickup = keyStation.AddComponent<InventoryPickupInteractable>();
            SetRef(keyPickup, "itemData", key);

            GameObject doorRoot = new GameObject("Training gate / requires key");
            doorRoot.transform.position = new Vector3(4.0f, 0f, 2.3f);
            var leaf = Shape("Rotating keyed gate", PrimitiveType.Cube,
                doorRoot.transform.position + new Vector3(0, 1.05f, 0),
                new Vector3(1.65f, 2.1f, .23f), amberMat, doorRoot.transform);
            var door = doorRoot.AddComponent<KeyDoorInteractable>();
            SetRef(door, "requiredKeyItem", key);
            SetRef(door, "doorLeaf", leaf.transform);

            GameObject cameraObject = new GameObject("Main Camera", typeof(Camera), typeof(AudioListener));
            cameraObject.tag = "MainCamera";
            cameraObject.transform.position = new Vector3(0f, 12.5f, -15f);
            cameraObject.transform.rotation = Quaternion.Euler(38f, 0f, 0f);
            Camera camera = cameraObject.GetComponent<Camera>();
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(.06f, .11f, .18f);
            camera.fieldOfView = 60f;

            GameObject sun = new GameObject("Main warm light", typeof(Light));
            sun.transform.rotation = Quaternion.Euler(45f, -35f, 0);
            sun.GetComponent<Light>().type = LightType.Directional;
            sun.GetComponent<Light>().intensity = 1.3f;
            GameObject fill = new GameObject("Training fill light", typeof(Light));
            fill.transform.position = new Vector3(-4, 7, -2);
            fill.GetComponent<Light>().type = LightType.Point;
            fill.GetComponent<Light>().range = 15;
            fill.GetComponent<Light>().intensity = 1.9f;

            GameObject root = new GameObject("HPR Gameplay Suite / integrated controller");
            var controller = root.AddComponent<HprGameplaySuitePlayground>();
            SetRef(controller, "playerRoot", player);
            SetRef(controller, "enemyVisual", enemy);
            SetRef(controller, "lootItem", medkit);
            SetRef(controller, "keyItem", key);
            SetRef(controller, "weaponData", rifle);
            SetRef(controller, "enemyData", raider);
            SetRef(controller, "healAbility", heal);
            SetRef(controller, "pulseAbility", pulse);
            SetRef(controller, "worldRegistry", catalog);
            SetRef(controller, "medkitPickup", medkitStation);
            SetRef(controller, "keyPickup", keyStation);
            SetRef(controller, "demoDoor", door);

            AssetDatabase.SaveAssets();
            if (!EditorSceneManager.SaveScene(scene, Scene))
                throw new InvalidOperationException("Unity failed to save original training arena");
            AssetDatabase.Refresh();
            Debug.Log("HPR Gameplay Suite arena saved at " + Scene);
        }

        public static void BuildAndExport()
        {
            BuildShowcase();
            string archive = Environment.GetEnvironmentVariable("HPR_GAMEPLAY_SUITE_OUTPUT");
            if (string.IsNullOrWhiteSpace(archive))
                throw new InvalidOperationException("HPR_GAMEPLAY_SUITE_OUTPUT is required");
            Directory.CreateDirectory(Path.GetDirectoryName(archive) ?? ".");
            AssetDatabase.ExportPackage(Root, archive, ExportPackageOptions.Recurse);
            if (!File.Exists(archive) || new FileInfo(archive).Length < 4096)
                throw new IOException("Unity did not export the HPR suite");
            Debug.Log("HPR Gameplay Suite candidate built; bytes=" + new FileInfo(archive).Length);
        }
    }
}
#endif
