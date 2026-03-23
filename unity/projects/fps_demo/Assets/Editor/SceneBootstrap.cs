using System.IO;
using HPR.Foundation.Utils;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

public static class SceneBootstrap
{
    private const string ScenePath = "Assets/Scenes/Main.unity";

    public static void CreateScene()
    {
        Directory.CreateDirectory("Assets/Scenes");
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        RenderSettings.ambientMode = AmbientMode.Flat;
        RenderSettings.ambientLight = new Color(0.6f, 0.65f, 0.7f);

        var lightGo = new GameObject("Directional Light");
        var light = GameObjectUtils.GetOrAddComponent<Light>(lightGo);
        light.type = LightType.Directional;
        light.intensity = 1.2f;
        light.transform.rotation = Quaternion.Euler(50f, -30f, 0f);

        var ground = GameObject.CreatePrimitive(PrimitiveType.Cube);
        ground.name = "Ground";
        ground.transform.position = new Vector3(0f, -0.5f, 0f);
        ground.transform.localScale = new Vector3(60f, 1f, 60f);
        ApplyColor(ground, new Color(0.28f, 0.32f, 0.34f));

        for (int i = 0; i < 12; i++)
        {
            var wall = GameObject.CreatePrimitive(PrimitiveType.Cube);
            wall.name = $"Wall_{i}";
            wall.transform.position = new Vector3(-18f + i * 3.5f, 1.5f, 10f + (i % 2 == 0 ? 0f : 4f));
            wall.transform.localScale = new Vector3(2f, 3f + (i % 3), 2f);
            ApplyColor(wall, new Color(0.55f, 0.25f + 0.02f * i, 0.2f));
        }

        for (int i = 0; i < 8; i++)
        {
            var pillar = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            pillar.name = $"Pillar_{i}";
            pillar.transform.position = new Vector3(-12f + i * 4f, 1f, -10f);
            pillar.transform.localScale = new Vector3(1f, 2f + 0.3f * (i % 2), 1f);
            ApplyColor(pillar, new Color(0.2f, 0.45f + 0.05f * i, 0.7f));
        }

        var player = new GameObject("Player");
        player.transform.position = new Vector3(0f, 1.8f, -16f);
        var controller = player.AddComponent<CharacterController>();
        controller.height = 1.8f;
        controller.radius = 0.35f;
        controller.center = new Vector3(0f, 0.9f, 0f);
        player.AddComponent<FirstPersonController>();

        var cameraGo = new GameObject("Main Camera");
        cameraGo.tag = "MainCamera";
        cameraGo.transform.SetParent(player.transform, false);
        cameraGo.transform.ResetLocalPose();
        cameraGo.transform.localPosition = new Vector3(0f, 0.65f, 0f);
        var camera = cameraGo.AddComponent<Camera>();
        camera.nearClipPlane = 0.03f;
        camera.fieldOfView = 75f;
        cameraGo.AddComponent<AudioListener>();

        EditorSceneManager.SaveScene(scene, ScenePath);
        AssetDatabase.SaveAssets();
        Debug.Log($"Created {ScenePath}");
    }

    public static void BuildLinux()
    {
        if (!File.Exists(ScenePath))
        {
            CreateScene();
        }

        Directory.CreateDirectory("Build/Linux");
        var report = BuildPipeline.BuildPlayer(new[] { ScenePath }, "Build/Linux/FPSDemo.x86_64", BuildTarget.StandaloneLinux64, BuildOptions.StrictMode);
        if (report.summary.result != UnityEditor.Build.Reporting.BuildResult.Succeeded)
        {
            throw new System.Exception($"Build failed: {report.summary.result}");
        }
        Debug.Log("Build succeeded");
    }

    private static void ApplyColor(GameObject go, Color color)
    {
        var renderer = go.GetComponent<Renderer>();
        if (renderer == null) return;
        var material = new Material(Shader.Find("Standard"));
        material.color = color;
        renderer.sharedMaterial = material;
    }
}
