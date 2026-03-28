#if UNITY_EDITOR
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class AiDemoSceneBuilder
{
    private const string DemoFolder = "Packages/com.hpr.ai/Demo";
    private const string ScenePath = DemoFolder + "/AiDemo.unity";
    private const string TempSceneDirectory = "Assets/__GeneratedPackageDemos";
    private const string TempScenePath = TempSceneDirectory + "/AiDemo.unity";
    private const string RaiderPath = DemoFolder + "/DemoRaider.asset";
    private const string SentryPath = DemoFolder + "/DemoSentry.asset";

    [MenuItem("HPR/AI/Build Demo Scene")]
    public static void BuildDemoScene()
    {
        EnemyData raider = EnsureEnemy(RaiderPath, "enemy_demo_raider", "Demo Raider", EnemyAIType.AggressiveChase, EnemyAttackStyle.Melee, 120f, 4.8f, 10f, 2.2f, 18f, new Vector3(1.1f, 2f, 1.1f));
        EnemyData sentry = EnsureEnemy(SentryPath, "enemy_demo_sentry", "Demo Sentry", EnemyAIType.StationaryAttack, EnemyAttackStyle.Ranged, 80f, 2.1f, 18f, 7.5f, 11f, new Vector3(1.6f, 1.3f, 1.6f));

        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var root = new GameObject("AiDemoRoot");

        var cameraGo = new GameObject("Main Camera", typeof(Camera));
        cameraGo.tag = "MainCamera";
        cameraGo.transform.position = new Vector3(0f, 5f, -10f);
        cameraGo.transform.rotation = Quaternion.Euler(20f, 0f, 0f);

        var lightGo = new GameObject("Directional Light", typeof(Light));
        lightGo.transform.rotation = Quaternion.Euler(50f, -30f, 0f);
        lightGo.GetComponent<Light>().type = LightType.Directional;

        var floor = GameObject.CreatePrimitive(PrimitiveType.Plane);
        floor.name = "Floor";
        floor.transform.localScale = new Vector3(1.4f, 1f, 1.2f);

        var controller = root.AddComponent<AiDemoController>();
        var so = new SerializedObject(controller);
        var enemiesProp = so.FindProperty("enemies");
        var previewsProp = so.FindProperty("previews");
        enemiesProp.arraySize = 2;
        previewsProp.arraySize = 2;

        CreatePreview(root.transform, enemiesProp, previewsProp, 0, raider, PrimitiveType.Capsule, new Vector3(-2.5f, 1f, 0f));
        CreatePreview(root.transform, enemiesProp, previewsProp, 1, sentry, PrimitiveType.Cube, new Vector3(2.5f, 0.7f, 0f));
        so.ApplyModifiedPropertiesWithoutUndo();

        Directory.CreateDirectory(Path.GetDirectoryName(TempScenePath) ?? "Assets");
        EditorSceneManager.SaveScene(scene, TempScenePath);
        AssetDatabase.Refresh();

        CopyTempSceneToPackage(ScenePath, TempScenePath);
        AssetDatabase.DeleteAsset(TempScenePath);
        AssetDatabase.DeleteAsset(TempSceneDirectory);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log($"AI demo scene written to {ScenePath}");
    }

    private static void CreatePreview(Transform root, SerializedProperty enemiesProp, SerializedProperty previewsProp, int index, EnemyData enemy, PrimitiveType primitiveType, Vector3 position)
    {
        GameObject preview = GameObject.CreatePrimitive(primitiveType);
        preview.name = enemy.DisplayName + " Preview";
        preview.transform.SetParent(root, false);
        preview.transform.position = position;
        preview.transform.localScale = enemy.VisualLocalScale;
        preview.transform.localEulerAngles = enemy.VisualLocalEuler;
        enemiesProp.GetArrayElementAtIndex(index).objectReferenceValue = enemy;
        previewsProp.GetArrayElementAtIndex(index).objectReferenceValue = preview.transform;
    }

    private static EnemyData EnsureEnemy(string path, string id, string displayName, EnemyAIType aiType, EnemyAttackStyle attackStyle, float maxHealth, float moveSpeed, float chaseRange, float attackRange, float attackDamage, Vector3 scale)
    {
        EnemyData asset = AssetDatabase.LoadAssetAtPath<EnemyData>(path);
        if (asset == null)
        {
            asset = ScriptableObject.CreateInstance<EnemyData>();
            AssetDatabase.CreateAsset(asset, path);
        }

        asset.Id = id;
        asset.DisplayName = displayName;
        asset.AIType = aiType;
        asset.AttackStyle = attackStyle;
        asset.MaxHealth = maxHealth;
        asset.MoveSpeed = moveSpeed;
        asset.ChaseSpeed = moveSpeed + 1.5f;
        asset.ChaseRange = chaseRange;
        asset.AttackRange = attackRange;
        asset.AttackDamage = attackDamage;
        asset.AttackCooldown = 1.3f;
        asset.ProjectileSpeed = 24f;
        asset.ProjectileImpact = 6f;
        asset.PreferredRange = attackRange;
        asset.VisualLocalScale = scale;
        asset.VisualLocalEuler = Vector3.zero;
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
