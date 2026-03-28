#if UNITY_EDITOR
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.UI;

public static class AbilitiesDemoSceneBuilder
{
    private const string DemoFolder = "Packages/com.hpr.abilities/Demo";
    private const string ScenePath = DemoFolder + "/AbilitiesDemo.unity";
    private const string TempSceneDirectory = "Assets/__GeneratedPackageDemos";
    private const string TempScenePath = "Assets/__GeneratedPackageDemos/AbilitiesDemo.unity";
    private const string RepairEffectPath = DemoFolder + "/RepairPulseEffect.asset";
    private const string ShockEffectPath = DemoFolder + "/ShockPulseEffect.asset";
    private const string RepairAbilityPath = DemoFolder + "/RepairPulse.asset";
    private const string ShockAbilityPath = DemoFolder + "/ShockPulse.asset";

    [MenuItem("HPR/Abilities/Build Demo Scene")]
    public static void BuildDemoScene()
    {
        var repairEffect = EnsureEffect(RepairEffectPath, "effect_repair_demo", "Repair Field", AbilityEffectType.Heal, 24f, 0f, 0.5f, new Color(0.22f, 0.82f, 0.36f, 1f));
        var shockEffect = EnsureEffect(ShockEffectPath, "effect_shock_demo", "Shock Ring", AbilityEffectType.AreaDamage, 32f, 5.5f, 1.3f, new Color(0.95f, 0.56f, 0.18f, 1f));
        var repairAbility = EnsureAbility(RepairAbilityPath, "ability_repair_demo", "Repair Pulse", "Restores health at stamina cost.", 8f, 18f, AbilityTargetType.Self, "Repair pulse emitted.", "Repair pulse unavailable.", new Color(0.24f, 0.82f, 0.42f, 1f), repairEffect);
        var shockAbility = EnsureAbility(ShockAbilityPath, "ability_shock_demo", "Shock Pulse", "Emits an area burst that damages nearby targets.", 12f, 24f, AbilityTargetType.Area, "Shock pulse emitted.", "Shock pulse unavailable.", new Color(0.95f, 0.6f, 0.2f, 1f), shockEffect);

        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var root = new GameObject("AbilitiesDemoRoot");

        var eventRoot = new GameObject("EventBus");
        eventRoot.transform.SetParent(root.transform, false);
        eventRoot.AddComponent<EventManager>();
        eventRoot.AddComponent<EventBusSourceAdapter>();

        var light = new GameObject("Directional Light");
        light.transform.rotation = Quaternion.Euler(50f, -30f, 0f);
        light.AddComponent<Light>().type = LightType.Directional;

        var cameraGo = new GameObject("Main Camera");
        cameraGo.tag = "MainCamera";
        cameraGo.transform.position = new Vector3(0f, 6.5f, -10f);
        cameraGo.transform.rotation = Quaternion.Euler(28f, 0f, 0f);
        cameraGo.AddComponent<Camera>().clearFlags = CameraClearFlags.SolidColor;

        var floor = GameObject.CreatePrimitive(PrimitiveType.Plane);
        floor.name = "Floor";
        floor.transform.position = Vector3.zero;
        floor.transform.localScale = new Vector3(2.2f, 1f, 2.2f);
        floor.GetComponent<Renderer>().sharedMaterial.color = new Color(0.16f, 0.18f, 0.22f, 1f);

        var actor = GameObject.CreatePrimitive(PrimitiveType.Capsule);
        actor.name = "AbilityActor";
        actor.transform.position = new Vector3(0f, 1f, 0f);
        actor.GetComponent<Renderer>().sharedMaterial.color = new Color(0.24f, 0.72f, 0.96f, 1f);
        var actorStats = actor.AddComponent<AbilityDemoStats>();
        actorStats.ResetStats();
        var actorStatsSerialized = new SerializedObject(actorStats);
        actorStatsSerialized.FindProperty("eventBusSourceBehaviour").objectReferenceValue = eventRoot.GetComponent<EventBusSourceAdapter>();
        actorStatsSerialized.ApplyModifiedPropertiesWithoutUndo();
        var runner = actor.AddComponent<AbilityRunnerComponent>();
        var runnerSo = new SerializedObject(runner);
        var configured = runnerSo.FindProperty("configuredAbilities");
        configured.arraySize = 2;
        configured.GetArrayElementAtIndex(0).objectReferenceValue = repairAbility;
        configured.GetArrayElementAtIndex(1).objectReferenceValue = shockAbility;
        runnerSo.FindProperty("unlockAllConfiguredAbilities").boolValue = true;
        runnerSo.FindProperty("eventBusSourceBehaviour").objectReferenceValue = eventRoot.GetComponent<EventBusSourceAdapter>();
        runnerSo.FindProperty("resourcePoolBehaviour").objectReferenceValue = actorStats;
        runnerSo.ApplyModifiedPropertiesWithoutUndo();

        var dummy = GameObject.CreatePrimitive(PrimitiveType.Cube);
        dummy.name = "TargetDummy";
        dummy.transform.position = new Vector3(3f, 1f, 1.25f);
        dummy.transform.localScale = new Vector3(1.4f, 2f, 1.4f);
        dummy.GetComponent<Renderer>().sharedMaterial.color = new Color(0.88f, 0.26f, 0.28f, 1f);
        var dummyStats = dummy.AddComponent<AbilityDemoStats>();
        dummyStats.ResetStats();
        var dummyStatsSerialized = new SerializedObject(dummyStats);
        dummyStatsSerialized.FindProperty("eventBusSourceBehaviour").objectReferenceValue = eventRoot.GetComponent<EventBusSourceAdapter>();
        dummyStatsSerialized.ApplyModifiedPropertiesWithoutUndo();

        var canvas = new GameObject("Canvas", typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
        var canvasComponent = canvas.GetComponent<Canvas>();
        canvasComponent.renderMode = RenderMode.ScreenSpaceOverlay;
        var scaler = canvas.GetComponent<CanvasScaler>();
        scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(1600f, 900f);

        var textGo = new GameObject("Readout", typeof(Text));
        textGo.transform.SetParent(canvas.transform, false);
        var text = textGo.GetComponent<Text>();
        text.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
        text.fontSize = 22;
        text.alignment = TextAnchor.UpperLeft;
        text.color = Color.white;
        var textRt = text.rectTransform;
        textRt.anchorMin = new Vector2(0f, 1f);
        textRt.anchorMax = new Vector2(0f, 1f);
        textRt.pivot = new Vector2(0f, 1f);
        textRt.anchoredPosition = new Vector2(24f, -24f);
        textRt.sizeDelta = new Vector2(720f, 260f);

        var controller = new GameObject("AbilitiesDemoController").AddComponent<AbilitiesDemoController>();
        var controllerSo = new SerializedObject(controller);
        controllerSo.FindProperty("runner").objectReferenceValue = runner;
        controllerSo.FindProperty("actorRoot").objectReferenceValue = actor;
        controllerSo.FindProperty("targetRoot").objectReferenceValue = dummy;
        controllerSo.FindProperty("readout").objectReferenceValue = text;
        controllerSo.ApplyModifiedPropertiesWithoutUndo();

        Directory.CreateDirectory(Path.GetDirectoryName(TempScenePath) ?? "Assets");
        EditorSceneManager.SaveScene(scene, TempScenePath);
        AssetDatabase.Refresh();

        var sourceAbsolutePath = Path.GetFullPath(Path.Combine(Application.dataPath, "..", TempScenePath));
        var targetAbsolutePath = Path.GetFullPath(Path.Combine(Application.dataPath, "..", ScenePath));
        Directory.CreateDirectory(Path.GetDirectoryName(targetAbsolutePath) ?? Path.GetFullPath(Path.Combine(Application.dataPath, "..")));
        File.Copy(sourceAbsolutePath, targetAbsolutePath, true);

        var sourceMetaPath = $"{sourceAbsolutePath}.meta";
        var targetMetaPath = $"{targetAbsolutePath}.meta";
        if (File.Exists(sourceMetaPath))
        {
            File.Copy(sourceMetaPath, targetMetaPath, true);
        }

        AssetDatabase.DeleteAsset(TempScenePath);
        AssetDatabase.DeleteAsset(TempSceneDirectory);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log($"Abilities demo scene written to {ScenePath}");
    }

    private static AbilityEffectData EnsureEffect(string path, string id, string displayName, AbilityEffectType effectType, float value, float radius, float forwardOffset, Color color)
    {
        var asset = AssetDatabase.LoadAssetAtPath<AbilityEffectData>(path);
        if (asset == null)
        {
            asset = ScriptableObject.CreateInstance<AbilityEffectData>();
            AssetDatabase.CreateAsset(asset, path);
        }

        asset.Id = id;
        asset.DisplayName = displayName;
        asset.EffectType = effectType;
        asset.Value = value;
        asset.Radius = radius;
        asset.ForwardOffset = forwardOffset;
        asset.ThemeColor = color;
        EditorUtility.SetDirty(asset);
        return asset;
    }

    private static AbilityData EnsureAbility(string path, string id, string displayName, string description, float cooldown, float cost, AbilityTargetType targetType, string activationStatus, string failureStatus, Color color, params AbilityEffectData[] effects)
    {
        var asset = AssetDatabase.LoadAssetAtPath<AbilityData>(path);
        if (asset == null)
        {
            asset = ScriptableObject.CreateInstance<AbilityData>();
            AssetDatabase.CreateAsset(asset, path);
        }

        asset.Id = id;
        asset.DisplayName = displayName;
        asset.Description = description;
        asset.Cooldown = cooldown;
        asset.Cost = cost;
        asset.TargetType = targetType;
        asset.ActivationStatus = activationStatus;
        asset.FailureStatus = failureStatus;
        asset.ThemeColor = color;
        asset.Effects = new System.Collections.Generic.List<AbilityEffectData>(effects);
        EditorUtility.SetDirty(asset);
        return asset;
    }
}
#endif
