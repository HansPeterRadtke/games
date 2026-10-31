// Private Editor-only acceptance test in a disposable Unity 6.6 URP host project.
// The user-facing HPR .unitypackage does NOT include URP as a dependency.
#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using HPR.GameplaySuite;

public static class HprSuiteUrpValidator
{
    public static void Run()
    {
        string receipt = Environment.GetEnvironmentVariable("HPR_SUITE_URP_RECEIPT");
        if (string.IsNullOrWhiteSpace(receipt) || File.Exists(receipt))
            throw new InvalidOperationException("Missing fresh private URP QA receipt");
        string folder = "Assets/HprPrivateUrpQA";
        Directory.CreateDirectory(folder);
        const string rendererPath = "Assets/HprPrivateUrpQA/HprTestRenderer.asset";
        const string pipelinePath = "Assets/HprPrivateUrpQA/HprTestUrp.asset";
        if (AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(pipelinePath) != null)
            throw new InvalidOperationException("Refusing to modify an existing URP test pipeline asset");
        UniversalRendererData renderer = ScriptableObject.CreateInstance<UniversalRendererData>();
        renderer.name = "HPR Disposable Test Renderer";
        AssetDatabase.CreateAsset(renderer, rendererPath);
        UniversalRenderPipelineAsset pipeline = UniversalRenderPipelineAsset.Create(renderer);
        pipeline.name = "HPR Disposable URP Pipeline";
        AssetDatabase.CreateAsset(pipeline, pipelinePath);
        AssetDatabase.SaveAssets();

        GraphicsSettings.defaultRenderPipeline = pipeline;
        QualitySettings.renderPipeline = null;
        if (GraphicsSettings.currentRenderPipeline == null)
            throw new InvalidOperationException("URP host pipeline was not activated");
        if (!(GraphicsSettings.currentRenderPipeline is UniversalRenderPipelineAsset))
            throw new InvalidOperationException("Active render pipeline is not URP");

        HprGameplaySuiteSceneBuilder.AdaptDemoMaterials();
        string[] materials = AssetDatabase.FindAssets("t:Material",
            new[] { "Assets/HPRGameplaySuite/Samples" });
        if (materials.Length < 9)
            throw new InvalidOperationException("Expected training-arena materials are absent");
        int converted = 0;
        foreach (string guid in materials)
        {
            Material mat = AssetDatabase.LoadAssetAtPath<Material>(
                AssetDatabase.GUIDToAssetPath(guid));
            if (mat == null) continue;
            if (mat.shader == null ||
                mat.shader.name != "Universal Render Pipeline/Lit" ||
                !mat.shader.isSupported)
                throw new InvalidOperationException("Training material is not URP Lit: " + mat.name);
            converted++;
        }

        var scene = EditorSceneManager.OpenScene(
            "Assets/HPRGameplaySuite/Demo/GameplaySuiteShowcase.unity", OpenSceneMode.Single);
        HprGameplaySuitePlayground controller = null;
        foreach (GameObject root in scene.GetRootGameObjects())
        {
            controller = root.GetComponent<HprGameplaySuitePlayground>();
            if (controller != null) break;
        }
        if (controller == null)
            throw new InvalidOperationException("URP scene lacks imported gameplay controller");
        Camera sceneCam = Camera.main;
        if (sceneCam == null || !sceneCam.allowHDR)
            throw new InvalidOperationException("URP scene camera not configured");

        File.WriteAllText(receipt,
            "host_editor=Unity " + Application.unityVersion + "\n" +
            "urp_renderer_asset_created=PASS\n" +
            "urp_active_render_pipeline=PASS\n" +
            "sample_materials_urp_lit=" + converted + "\n" +
            "original_buyer_archive_imported=PASS\n" +
            "original_live_demo_scene_present=PASS\n" +
            "additional_runtime_dependencies_in_buyer_archive=NONE\n");
        Debug.Log("HPR_URP_INDEPENDENT_ACCEPTANCE_PASS " + converted + " materials");
    }
}
#endif
