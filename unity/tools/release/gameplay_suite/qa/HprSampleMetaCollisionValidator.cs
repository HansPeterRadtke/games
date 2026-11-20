// Private QA-only safety experiment for an already present buyer-owned .meta
// file without its associated asset. Operates only in a disposable Unity project.
#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEngine;
using HPR.GameplaySuite;

public static class HprSampleMetaCollisionValidator
{
    public static void Run()
    {
        string receipt = Environment.GetEnvironmentVariable("HPR_SAMPLE_META_COLLISION_RECEIPT");
        if (string.IsNullOrWhiteSpace(receipt) || File.Exists(receipt))
            throw new InvalidOperationException("Expected a new private safety-research receipt.");
        const string source = "Assets/HPRGameplaySuite/Samples/DemoRifle.asset";
        const string folder = "Assets/HprPrivateMetaCollisionQA";
        const string dest = folder + "/ReservedIdentity.asset";
        const string desiredGuid = "12341234123412341234123412341234";

        if (AssetDatabase.IsValidFolder(folder) ||
            AssetDatabase.LoadMainAssetAtPath(dest) != null ||
            File.Exists(Path.Combine(Application.dataPath, "HprPrivateMetaCollisionQA/ReservedIdentity.asset")))
            throw new InvalidOperationException("Expected a clean disposable QA destination.");
        if (AssetDatabase.CreateFolder("Assets", "HprPrivateMetaCollisionQA") == "")
            throw new InvalidOperationException("Could not create private test folder.");
        string physical = Path.Combine(Application.dataPath,
            "HprPrivateMetaCollisionQA/ReservedIdentity.asset");
        string metadata = physical + ".meta";
        string originalMeta = "fileFormatVersion: 2\nguid: " + desiredGuid + "\n";
        File.WriteAllText(metadata, originalMeta);
        if (File.Exists(physical))
            throw new InvalidOperationException("Unexpected pre-existing target asset.");

        bool rejected = false;
        string rejection = "";
        try
        {
            HprSuiteIntegrationGuide.CopySampleToCustomerPath(source, dest);
        }
        catch (IOException ex)
        {
            rejected = true;
            rejection = ex.GetType().Name;
        }
        catch (ArgumentException ex)
        {
            rejected = true;
            rejection = ex.GetType().Name;
        }
        string afterMeta = File.Exists(metadata) ? File.ReadAllText(metadata) : "[MISSING]";
        bool fileWasCreated = File.Exists(physical);
        bool metadataPreserved = afterMeta == originalMeta;

        File.WriteAllText(receipt,
            "preexisting_orphan_meta_file=yes\n" +
            "copy_rejected=" + rejected + "\n" +
            "rejection_type=" + rejection + "\n" +
            "preexisting_metadata_preserved=" + metadataPreserved + "\n" +
            "target_asset_was_created=" + fileWasCreated + "\n");

        if (!rejected || !metadataPreserved || fileWasCreated)
            throw new InvalidOperationException(
                "Customer metadata reservation was not treated as a hard no-write boundary.");
        Debug.Log("HPR_META_COLLISION_SAFE_REJECTION_PASS");
    }
}
#endif
