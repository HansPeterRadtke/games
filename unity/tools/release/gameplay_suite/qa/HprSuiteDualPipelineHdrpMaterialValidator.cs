// PRIVATE cleanroom Editor acceptance, NOT part of the HPR buyer archive.
// Requires a disposable HDRP-active Unity 6.6 project that ALSO has URP
// installed, to reproduce the previous first-discoverable-URP-shader defect.
// DO NOT run on a customer project or original first-party asset checkout.
#if UNITY_EDITOR
using System;
using System.IO;
using System.Security.Cryptography;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using HPR.GameplaySuite;

public static class HprSuiteDualPipelineHdrpMaterialValidator
{
    private const string Samples = "Assets/HPRGameplaySuite/Samples";
    private const string OriginalScene = "Assets/HPRGameplaySuite/Demo/GameplaySuiteShowcase.unity";

    private static string Physical(string relative) =>
        Path.Combine(Directory.GetParent(Application.dataPath).FullName, relative);

    private static string Sha256(string relative)
    {
        using (var input = File.OpenRead(Physical(relative)))
        using (var hash = SHA256.Create())
            return Convert.ToBase64String(hash.ComputeHash(input));
    }

    private static void Require(bool condition, string reason)
    {
        if (!condition) throw new InvalidOperationException("HPR HDRP acceptance: " + reason);
    }

    private static bool SameColor(Color a, Color b)
    {
        const float tolerance = .005f;
        return Mathf.Abs(a.r - b.r) <= tolerance &&
               Mathf.Abs(a.g - b.g) <= tolerance &&
               Mathf.Abs(a.b - b.b) <= tolerance &&
               Mathf.Abs(a.a - b.a) <= tolerance;
    }

    private static Color BaseColor(Material material)
    {
        if (material.HasProperty("_BaseColor")) return material.GetColor("_BaseColor");
        if (material.HasProperty("_Color")) return material.GetColor("_Color");
        throw new InvalidOperationException("Sample material lacks a supported base-color property");
    }

    public static void Run()
    {
        string receipt = Environment.GetEnvironmentVariable("HPR_SUITE_DUAL_PIPELINE_HDRP_RECEIPT");
        if (string.IsNullOrWhiteSpace(receipt) || File.Exists(receipt))
            throw new InvalidOperationException("Provide fresh private cleanroom QA receipt");
        RenderPipelineAsset active = GraphicsSettings.currentRenderPipeline;
        Require(active != null && active.GetType().Name == "HDRenderPipelineAsset",
            "disposable QA host must have an active HDRenderPipelineAsset");
        Shader hdrp = Shader.Find("HDRP/Lit");
        Shader urp = Shader.Find("Universal Render Pipeline/Lit");
        Require(hdrp != null && hdrp.isSupported,
            "the actual HDRP Lit shader must be installed and supported");
        Require(urp != null,
            "this negative regression requires URP shader to be discoverable in the same project");
        string originalSceneSha = Sha256(OriginalScene);
        string originalSceneMetaSha = Sha256(OriginalScene + ".meta");

        string[] assetGuids = AssetDatabase.FindAssets("t:Material", new[] { Samples });
        Require(assetGuids.Length >= 9, "expected real first-party demo materials");
        var materials = new System.Collections.Generic.List<Material>();
        var colors = new System.Collections.Generic.List<Color>();
        int wrongBefore = 0;
        foreach (string guid in assetGuids)
        {
            string path = AssetDatabase.GUIDToAssetPath(guid);
            Require(path.StartsWith(Samples + "/", StringComparison.Ordinal) &&
                    path.EndsWith(".mat", StringComparison.OrdinalIgnoreCase),
                    "Refusing unrelated or non-material asset");
            Material material = AssetDatabase.LoadAssetAtPath<Material>(path);
            Require(material != null, "Missing sample material " + path);
            materials.Add(material);
            colors.Add(BaseColor(material));
            if (material.shader != hdrp) wrongBefore++;
        }
        Require(wrongBefore >= 1,
            "negative regression requires at least one old sample material not yet using HDRP");
        // Exercise the buyer-facing action itself. It must not install packages,
        // modify GraphicsSettings or flush unrelated dirty buyer assets.
        HprGameplaySuiteSceneBuilder.AdaptDemoMaterials();
        Require(GraphicsSettings.currentRenderPipeline == active,
            "conversion changed the chosen renderer");
        for (int i = 0; i < materials.Count; i++)
        {
            Material mat = materials[i];
            Require(mat.shader == hdrp && mat.shader.isSupported,
                "sample used a wrong renderer shader after conversion: " + mat.name);
            Require(mat.HasProperty("_BaseColor"),
                "HDRP sample does not expose _BaseColor: " + mat.name);
            Require(SameColor(BaseColor(mat), colors[i]),
                "sample color changed instead of preserving authoring color: " + mat.name);
        }
        Require(Sha256(OriginalScene) == originalSceneSha &&
                Sha256(OriginalScene + ".meta") == originalSceneMetaSha,
                "sample scene or GUID metadata changed during material-only conversion");
        Require(GraphicsSettings.currentRenderPipeline == active,
                "active HDRP pipeline was changed by buyer material adaptation");

        // This is a receipt of a genuine disposable Unity Editor execution
        // only after it has actually succeeded. Nothing is claimed until then.
        using (var stream = new FileStream(receipt, FileMode.CreateNew,
                                           FileAccess.Write, FileShare.None))
        using (var writer = new StreamWriter(stream))
        {
            writer.WriteLine("HPR_HDRP_DUAL_PIPELINE_CLEANROOM_PASS");
            writer.WriteLine("Editor=" + Application.unityVersion);
            writer.WriteLine("ActivePipeline=" + active.GetType().FullName);
            writer.WriteLine("BothShaderPackagesDiscoverable=YES");
            writer.WriteLine("ConvertedFirstPartyMaterials=" + materials.Count);
            writer.WriteLine("PreviouslyWrongShaderMaterials=" + wrongBefore);
            writer.WriteLine("SceneAndMetaUnchanged=YES");
            writer.WriteLine("OriginalBuyerArchiveOrStorefrontSubmitted=NO");
        }
        Debug.Log("HPR_HDRP_DUAL_PIPELINE_CLEANROOM_PASS " + materials.Count + " materials");
    }
}
#endif
