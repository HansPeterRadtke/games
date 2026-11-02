// Private Unity 6.6 Editor buyer-project QA. NOT shipped with HPR package.
// Explicitly detects unrelated buyer asset writes while adapting ONLY vendor
// demo materials. Run in a unique disposable customer project, never original.
#if UNITY_EDITOR
using System;
using System.IO;
using System.Security.Cryptography;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using HPR;
using HPR.GameplaySuite;

public static class HprDemoMaterialDirtyIsolationValidator
{
    private const string UnrelatedDirty =
        "Assets/ExternalCustomerGame/IntegrationDemos/CustomerHealing.asset";
    private const string OriginalScene =
        "Assets/ExternalCustomerGame/Scenes/OriginalCustomerScene.unity";
    private const string MaterialPath =
        "Assets/HPRGameplaySuite/Samples/ArenaSteel.mat";

    public static void Run()
    {
        string receipt = Environment.GetEnvironmentVariable("HPR_DEMO_MATERIAL_DIRTY_RECEIPT");
        if (string.IsNullOrWhiteSpace(receipt) || File.Exists(receipt))
            throw new InvalidOperationException("Require a fresh independent private QA receipt");

        var buyer = AssetDatabase.LoadAssetAtPath<AbilityData>(UnrelatedDirty);
        var material = AssetDatabase.LoadAssetAtPath<Material>(MaterialPath);
        if (buyer == null || material == null || EditorUtility.IsDirty(buyer))
            throw new InvalidOperationException("Disposable buyer and vendor assets unavailable or previously dirty");
        if (GraphicsSettings.currentRenderPipeline != null)
            throw new InvalidOperationException("This isolated test requires the known Built-in render pipeline");
        Shader unlit = Shader.Find("Unlit/Color");
        Shader standard = Shader.Find("Standard");
        if (unlit == null || standard == null || !standard.isSupported)
            throw new InvalidOperationException("Known test shaders unavailable");

        string customerDisk = SHA256(Physical(UnrelatedDirty));
        string customerMeta = SHA256(Physical(UnrelatedDirty + ".meta"));
        string originalScene = SHA256(Physical(OriginalScene));
        string vendorDisk = SHA256(Physical(MaterialPath));
        string beforeBuyerName = buyer.DisplayName;
        Shader beforeShader = material.shader;
        Color beforeColor = material.color;
        bool buyerEditRemainedDirty = false;
        bool vendorMaterialExplicitlySaved = false;

        try
        {
            // Do NOT save this customer change. The HPR button must preserve it
            // exactly as an unsaved Inspector edit in memory.
            buyer.DisplayName = "UNRELATED_CUSTOMER_UNSAVED_QA_" +
                                Guid.NewGuid().ToString("N");
            EditorUtility.SetDirty(buyer);
            if (!EditorUtility.IsDirty(buyer) ||
                SHA256(Physical(UnrelatedDirty)) != customerDisk)
                throw new InvalidOperationException("Expected buyer asset to be dirty only in RAM");

            // Deliberately make ONLY an HPR sample material need conversion
            // and a targeted disk save. This is not a fake test of the helper.
            material.shader = unlit;
            material.color = new Color(0.39f, 0.17f, 0.32f, 1f);
            EditorUtility.SetDirty(material);
            if (SHA256(Physical(MaterialPath)) != vendorDisk)
                throw new InvalidOperationException("Unsaved material already modified the source file");

            HprGameplaySuiteSceneBuilder.AdaptDemoMaterials();

            buyerEditRemainedDirty = EditorUtility.IsDirty(buyer) &&
                                    buyer.DisplayName.StartsWith("UNRELATED_CUSTOMER_UNSAVED_QA_") &&
                                    SHA256(Physical(UnrelatedDirty)) == customerDisk;
            vendorMaterialExplicitlySaved = material.shader == standard &&
                                           SHA256(Physical(MaterialPath)) != vendorDisk;
            bool customerMetaPreserved =
                SHA256(Physical(UnrelatedDirty + ".meta")) == customerMeta;
            bool customerScenePreserved =
                SHA256(Physical(OriginalScene)) == originalScene;

            // Even if the checker fails, keep actual observed negative
            // evidence instead of manufacturing a positive receipt.
            using (var output = new FileStream(receipt, FileMode.CreateNew,
                                               FileAccess.Write, FileShare.None))
            using (var writer = new StreamWriter(output))
            {
                writer.Write(
                    "HPR_REAL_UNITY_DEMO_MATERIAL_CONVERSION_EXECUTED=YES\n" +
                    "unrelated_customer_dirty_edit_unsaved=" + buyerEditRemainedDirty + "\n" +
                    "vendor_demo_material_saved_as_intended=" + vendorMaterialExplicitlySaved + "\n" +
                    "original_customer_scene_unmodified=" + customerScenePreserved + "\n" +
                    "original_customer_meta_guid_unmodified=" + customerMetaPreserved + "\n" +
                    "not_a_publisher_release=YES\n");
            }
            if (!buyerEditRemainedDirty || !vendorMaterialExplicitlySaved ||
                !customerMetaPreserved || !customerScenePreserved)
                throw new InvalidOperationException("AdaptDemoMaterials changed unrelated customer data or did not save the intended HPR material");
            Debug.Log("HPR_DEMO_MATERIAL_DIRTY_CUSTOMER_ISOLATION_PASS");
        }
        finally
        {
            // Revert only this validator's synthetic in-memory changes.
            // No global AssetDatabase.SaveAssets may occur here.
            buyer.DisplayName = beforeBuyerName;
            EditorUtility.ClearDirty(buyer);
            // Keep the material's intentionally saved new state inside the
            // disposable project for independent disk-file verification.
        }
    }

    private static string Physical(string relative) =>
        Path.Combine(Directory.GetParent(Application.dataPath).FullName, relative);

    private static string SHA256(string path)
    {
        using (var input = File.OpenRead(path))
        using (var digest = System.Security.Cryptography.SHA256.Create())
            return Convert.ToBase64String(digest.ComputeHash(input));
    }
}
#endif
