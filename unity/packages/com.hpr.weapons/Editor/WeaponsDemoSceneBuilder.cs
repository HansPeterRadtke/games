namespace HPR
{
    #if UNITY_EDITOR
    using System.Collections.Generic;
    using System.IO;
    using UnityEditor;
    using UnityEditor.SceneManagement;
    using UnityEngine;

    public static class WeaponsDemoSceneBuilder
    {
        private const string DemoFolder = "Packages/com.hpr.weapons/Demo";
        private const string ScenePath = DemoFolder + "/WeaponsDemo.unity";
        private const string TempSceneDirectory = "Assets/__GeneratedPackageDemos";
        private const string TempScenePath = TempSceneDirectory + "/WeaponsDemo.unity";
        private const string RiflePath = DemoFolder + "/DemoRifle.asset";
        private const string ScatterPath = DemoFolder + "/DemoScattergun.asset";

        [MenuItem("Tools/HPR/Weapons/Build Demo Scene")]
        public static void BuildDemoScene()
        {
            WeaponData rifle = EnsureWeapon(
                RiflePath,
                "weapon_demo_rifle",
                "Demo Rifle",
                FireModeType.Hitscan,
                EquipmentKind.Hitscan,
                PrimitiveType.Cube,
                18f,
                64f,
                0.2f,
                180,
                new Vector3(1.6f, 0.18f, 0.25f));
            WeaponData scatter = EnsureWeapon(
                ScatterPath,
                "weapon_demo_scatter",
                "Demo Scattergun",
                FireModeType.Shotgun,
                EquipmentKind.Scatter,
                PrimitiveType.Cylinder,
                11f,
                18f,
                0.85f,
                48,
                new Vector3(0.28f, 1.15f, 0.28f),
                pellets: 7,
                spread: 0.16f);

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var root = new GameObject("WeaponsDemoRoot");

            var cameraGo = new GameObject("Main Camera", typeof(Camera));
            cameraGo.tag = "MainCamera";
            cameraGo.transform.position = new Vector3(0f, 3.4f, -9f);
            cameraGo.transform.rotation = Quaternion.Euler(18f, 0f, 0f);

            var lightGo = new GameObject("Directional Light", typeof(Light));
            lightGo.transform.rotation = Quaternion.Euler(50f, -30f, 0f);
            lightGo.GetComponent<Light>().type = LightType.Directional;

            var floor = GameObject.CreatePrimitive(PrimitiveType.Plane);
            floor.name = "Floor";
            floor.transform.position = Vector3.zero;
            floor.transform.localScale = new Vector3(1.4f, 1f, 1.2f);

            var controller = root.AddComponent<WeaponsDemoController>();
            var controllerSo = new SerializedObject(controller);
            var weaponsProp = controllerSo.FindProperty("weapons");
            var previewsProp = controllerSo.FindProperty("previews");
            weaponsProp.arraySize = 2;
            previewsProp.arraySize = 2;

            CreatePreview(root.transform, weaponsProp, previewsProp, 0, rifle, new Vector3(-2f, 1.05f, 0f));
            CreatePreview(root.transform, weaponsProp, previewsProp, 1, scatter, new Vector3(2f, 1.05f, 0f));
            controllerSo.ApplyModifiedPropertiesWithoutUndo();

            Directory.CreateDirectory(Path.GetDirectoryName(TempScenePath) ?? "Assets");
            EditorSceneManager.SaveScene(scene, TempScenePath);
            AssetDatabase.Refresh();

            CopyTempSceneToPackage(ScenePath, TempScenePath);
            AssetDatabase.DeleteAsset(TempScenePath);
            AssetDatabase.DeleteAsset(TempSceneDirectory);
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log($"Weapons demo scene written to {ScenePath}");
        }

        private static void CreatePreview(Transform root, SerializedProperty weaponsProp, SerializedProperty previewsProp, int index, WeaponData weapon, Vector3 position)
        {
            GameObject preview = GameObject.CreatePrimitive(weapon.ViewShape);
            preview.name = weapon.DisplayName + " Preview";
            preview.transform.SetParent(root, false);
            preview.transform.position = position;
            preview.transform.localScale = weapon.ViewLocalScale;
            preview.transform.localEulerAngles = weapon.ViewLocalEuler;
            weaponsProp.GetArrayElementAtIndex(index).objectReferenceValue = weapon;
            previewsProp.GetArrayElementAtIndex(index).objectReferenceValue = preview.transform;
        }

        private static WeaponData EnsureWeapon(string path, string id, string displayName, FireModeType fireMode, EquipmentKind kind, PrimitiveType shape, float damage, float range, float fireDelay, int maxAmmo, Vector3 scale, int pellets = 1, float spread = 0.01f)
        {
            WeaponData asset = AssetDatabase.LoadAssetAtPath<WeaponData>(path);
            if (asset == null)
            {
                asset = ScriptableObject.CreateInstance<WeaponData>();
                AssetDatabase.CreateAsset(asset, path);
            }

            asset.Id = id;
            asset.DisplayName = displayName;
            asset.FireModeType = fireMode;
            asset.Kind = kind;
            asset.Damage = damage;
            asset.Range = range;
            asset.FireDelay = fireDelay;
            asset.MaxAmmo = maxAmmo;
            asset.AmmoPerPickup = Mathf.Max(4, maxAmmo / 6);
            asset.ViewShape = shape;
            asset.ViewLocalScale = scale;
            asset.ViewLocalEuler = Vector3.zero;
            asset.Pellets = pellets;
            asset.Spread = spread;
            asset.MagazineSize = Mathf.Max(1, maxAmmo / 6);
            asset.StartingMagazineAmmo = asset.MagazineSize;
            asset.StartingReserveAmmo = Mathf.Max(asset.MagazineSize, maxAmmo / 2);
            asset.UsesAmmo = true;
            asset.ProjectileSpeed = 42f;
            asset.ImpactForce = 10f;
            EditorUtility.SetDirty(asset);
            return asset;
        }

        private static void CopyTempSceneToPackage(string targetScenePath, string sourceScenePath)
        {
            string sourceAbsolutePath = Path.GetFullPath(Path.Combine(Application.dataPath, "..", sourceScenePath));
            string targetAbsolutePath = Path.GetFullPath(Path.Combine(Application.dataPath, "..", targetScenePath));
            Directory.CreateDirectory(Path.GetDirectoryName(targetAbsolutePath) ?? Path.GetFullPath(Path.Combine(Application.dataPath, "..")));
            File.Copy(sourceAbsolutePath, targetAbsolutePath, true);

            string sourceMetaPath = sourceAbsolutePath + ".meta";
            string targetMetaPath = targetAbsolutePath + ".meta";
            if (!File.Exists(targetMetaPath) && File.Exists(sourceMetaPath))
            {
                File.Copy(sourceMetaPath, targetMetaPath, false);
            }
        }
    }
    #endif
}
