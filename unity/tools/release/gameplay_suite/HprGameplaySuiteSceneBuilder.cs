// Copyright (c) Multiverse Studio. All rights reserved.
// Editor-only authoring of an original integrated sample scene and release archive.
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

        [MenuItem("Tools/HPR/Gameplay Suite/Build Showcase")]
        public static void BuildShowcase()
        {
            Directory.CreateDirectory(Samples);
            Directory.CreateDirectory(Root + "/Demo");
            AssetDatabase.Refresh();

            var medkit = AssetDatabase.LoadAssetAtPath<ItemData>(Samples + "/FieldMedkit.asset");
            if (medkit == null)
            {
                medkit = ScriptableObject.CreateInstance<ItemData>();
                AssetDatabase.CreateAsset(medkit, Samples + "/FieldMedkit.asset");
            }
            medkit.Id = "hpr_suite_field_medkit";
            medkit.DisplayName = "Field Medkit";
            medkit.Description = "Loot recovered when the demo enemy is eliminated; consuming restores 30 health.";
            medkit.ItemType = ItemType.Consumable;
            medkit.StartingPlayerQuantity = 0;
            EditorUtility.SetDirty(medkit);

            var rifle = AssetDatabase.LoadAssetAtPath<WeaponData>(Samples + "/DemoRifle.asset");
            if (rifle == null)
            {
                rifle = ScriptableObject.CreateInstance<WeaponData>();
                AssetDatabase.CreateAsset(rifle, Samples + "/DemoRifle.asset");
            }
            rifle.Id = "hpr_suite_demo_rifle";
            rifle.DisplayName = "Demo Rifle";
            rifle.Damage = 15f;
            rifle.Range = 50f;
            rifle.FireDelay = 0.35f;
            rifle.MagazineSize = 6;
            rifle.StartingMagazineAmmo = 6;
            rifle.StartingReserveAmmo = 30;
            rifle.MaxAmmo = 60;
            rifle.UsesAmmo = true;
            EditorUtility.SetDirty(rifle);

            var raider = AssetDatabase.LoadAssetAtPath<EnemyData>(Samples + "/DemoRaider.asset");
            if (raider == null)
            {
                raider = ScriptableObject.CreateInstance<EnemyData>();
                AssetDatabase.CreateAsset(raider, Samples + "/DemoRaider.asset");
            }
            raider.Id = "hpr_suite_demo_raider";
            raider.DisplayName = "Demonstration Raider";
            raider.MaxHealth = 60f;
            raider.AttackRange = 2.5f;
            raider.ChaseRange = 10f;
            raider.AttackDamage = 8f;
            raider.AttackCooldown = 1f;
            raider.AIType = EnemyAIType.PatrolChase;
            EditorUtility.SetDirty(raider);

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            GameObject ground = GameObject.CreatePrimitive(PrimitiveType.Plane);
            ground.name = "Original ground — no external art";
            ground.transform.localScale = new Vector3(1.7f, 1, 1.2f);

            GameObject player = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            player.name = "Player — health + event transport + inventory";
            player.transform.position = new Vector3(-2.5f, 1f, 0f);
            player.AddComponent<EventManager>();
            player.AddComponent<InventoryComponent>();
            player.AddComponent<ActorStatsComponent>();

            GameObject enemy = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            enemy.name = "Enemy — deterministic decision and damage state";
            enemy.transform.position = new Vector3(2.5f, 1f, 0f);
            var material = AssetDatabase.LoadAssetAtPath<Material>(Samples + "/DemoEnemy.mat");
            if (material == null)
            {
                Shader shader = Shader.Find("Standard") ?? Shader.Find("Universal Render Pipeline/Lit");
                if (shader == null) throw new InvalidOperationException("No supported demo material shader is available");
                material = new Material(shader);
                AssetDatabase.CreateAsset(material, Samples + "/DemoEnemy.mat");
            }
            material.color = Color.red;
            EditorUtility.SetDirty(material);
            enemy.GetComponent<Renderer>().sharedMaterial = material;

            GameObject cameraObject = new GameObject("Main Camera", typeof(Camera), typeof(AudioListener));
            cameraObject.tag = "MainCamera";
            cameraObject.transform.position = new Vector3(0, 6f, -13f);
            cameraObject.transform.rotation = Quaternion.Euler(20f, 0, 0);
            cameraObject.GetComponent<Camera>().clearFlags = CameraClearFlags.Skybox;

            GameObject lightObject = new GameObject("Directional Light", typeof(Light));
            lightObject.transform.rotation = Quaternion.Euler(45f, -35f, 0);
            lightObject.GetComponent<Light>().type = LightType.Directional;
            lightObject.GetComponent<Light>().intensity = 1.2f;

            GameObject root = new GameObject("HPR Gameplay Suite — controller");
            var controller = root.AddComponent<HprGameplaySuitePlayground>();
            SerializedObject serialized = new SerializedObject(controller);
            serialized.FindProperty("playerRoot").objectReferenceValue = player;
            serialized.FindProperty("enemyVisual").objectReferenceValue = enemy;
            serialized.FindProperty("lootItem").objectReferenceValue = medkit;
            serialized.FindProperty("weaponData").objectReferenceValue = rifle;
            serialized.FindProperty("enemyData").objectReferenceValue = raider;
            serialized.ApplyModifiedPropertiesWithoutUndo();
            AssetDatabase.SaveAssets();
            if (!EditorSceneManager.SaveScene(scene, Scene)) throw new InvalidOperationException("Unity failed to save the integrated scene");
            AssetDatabase.Refresh();
            Debug.Log("HPR Gameplay Suite integrated scene saved at " + Scene);
        }

        public static void BuildAndExport()
        {
            BuildShowcase();
            string archive = Environment.GetEnvironmentVariable("HPR_GAMEPLAY_SUITE_OUTPUT");
            if (string.IsNullOrWhiteSpace(archive)) throw new InvalidOperationException("HPR_GAMEPLAY_SUITE_OUTPUT is required");
            Directory.CreateDirectory(Path.GetDirectoryName(archive) ?? ".");
            AssetDatabase.ExportPackage(Root, archive, ExportPackageOptions.Recurse);
            if (!File.Exists(archive) || new FileInfo(archive).Length < 4096)
                throw new IOException("Unity did not create a nonempty package from the suite root");
            Debug.Log("HPR Gameplay Suite single-root package export succeeded; bytes=" + new FileInfo(archive).Length);
        }
    }
}
#endif
