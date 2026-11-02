// Private, never-shipped Unity 6.6 Editor QA. All changes are confined to a
// disposable buyer project. Exercise a genuine unsaved customer ScriptableObject
// while copying an HPR sample: the copy must NEVER save unrelated dirty assets.
#if UNITY_EDITOR
using System;
using System.IO;
using System.Security.Cryptography;
using UnityEditor;
using UnityEngine;
using HPR;
using HPR.GameplaySuite;

public static class HprUnrelatedDirtyAssetValidator
{
    private const string UnrelatedDirty =
        "Assets/ExternalCustomerGame/IntegrationDemos/CustomerHealing.asset";
    private const string OriginalScene =
        "Assets/ExternalCustomerGame/Scenes/OriginalCustomerScene.unity";
    private const string SourceVendor =
        "Assets/HPRGameplaySuite/Samples/RepairAbility.asset";
    private const string NewBuyerCopy =
        "Assets/ExternalCustomerGame/IntegrationDemos/ScopedCopyOnly.asset";
    private const string NewBuyerEffect =
        "Assets/ExternalCustomerGame/IntegrationDemos/ScopedCopyOnly__HPR_RepairEffect.asset";

    public static void Run()
    {
        string receipt = Environment.GetEnvironmentVariable("HPR_DIRTY_ASSET_ISOLATION_RECEIPT");
        if (string.IsNullOrWhiteSpace(receipt) || File.Exists(receipt))
            throw new InvalidOperationException("A unique private QA receipt is required.");
        if (File.Exists(Physical(NewBuyerCopy)) || File.Exists(Physical(NewBuyerCopy + ".meta")) ||
            File.Exists(Physical(NewBuyerEffect)) ||
            AssetDatabase.LoadMainAssetAtPath(NewBuyerCopy) != null)
            throw new InvalidOperationException("Refusing to overwrite a previous test's assets.");

        var unrelated = AssetDatabase.LoadAssetAtPath<AbilityData>(UnrelatedDirty);
        var vendor = AssetDatabase.LoadAssetAtPath<AbilityData>(SourceVendor);
        if (unrelated == null || vendor == null ||
            AssetDatabase.GetAssetPath(unrelated) != UnrelatedDirty)
            throw new InvalidOperationException("Buyer or vendor source asset not found.");

        string diskBefore = SHA256(Physical(UnrelatedDirty));
        string metaBefore = SHA256(Physical(UnrelatedDirty + ".meta"));
        string sceneBefore = SHA256(Physical(OriginalScene));
        string vendorBefore = SHA256(Physical(SourceVendor));
        string originalName = unrelated.DisplayName;
        bool originalDirty = EditorUtility.IsDirty(unrelated);
        if (originalDirty)
            throw new InvalidOperationException("Fresh buyer fixture already has unsaved changes.");
        string uniqueName = "UNRELATED_CUSTOMER_UNSAVED_QA_" + Guid.NewGuid().ToString("N");
        bool copyMade = false;
        try
        {
            // Deliberately dirty a CUSTOMER asset but do not save it.
            // This simulates the user's unrelated in-progress Inspector edits.
            unrelated.DisplayName = uniqueName;
            EditorUtility.SetDirty(unrelated);
            if (!EditorUtility.IsDirty(unrelated) ||
                SHA256(Physical(UnrelatedDirty)) != diskBefore)
                throw new InvalidOperationException("Customer asset did not remain unsaved.");

            var created = HprSuiteIntegrationGuide.CopySampleToCustomerPath(
                SourceVendor, NewBuyerCopy) as AbilityData;
            if (created == null || created.Effects == null ||
                created.Effects.Count != 1 ||
                AssetDatabase.GetAssetPath(created.Effects[0]) != NewBuyerEffect ||
                created.Id == vendor.Id)
                throw new InvalidOperationException("Selected sample copy did not retain dependencies.");
            copyMade = true;

            bool savedUnrelated = SHA256(Physical(UnrelatedDirty)) != diskBefore;
            bool originalSceneChanged = SHA256(Physical(OriginalScene)) != sceneBefore;
            bool vendorChanged = SHA256(Physical(SourceVendor)) != vendorBefore;
            bool metaChanged = SHA256(Physical(UnrelatedDirty + ".meta")) != metaBefore;
            bool stillDirtyInMemory = unrelated.DisplayName == uniqueName &&
                                      EditorUtility.IsDirty(unrelated);
            File.WriteAllText(receipt,
                "new_customer_owned_copy_and_effect_created=" + copyMade + "\n" +
                "unrelated_customer_asset_saved_to_disk=" + savedUnrelated + "\n" +
                "original_scene_mutated=" + originalSceneChanged + "\n" +
                "vendor_original_mutated=" + vendorChanged + "\n" +
                "customer_asset_metadata_mutated=" + metaChanged + "\n" +
                "unrelated_customer_edit_remains_unsaved=" + stillDirtyInMemory + "\n");
            if (savedUnrelated || originalSceneChanged || vendorChanged || metaChanged ||
                !stillDirtyInMemory)
                throw new InvalidOperationException("HPR asset copier saved unrelated customer changes.");
            Debug.Log("HPR_UNRELATED_DIRTY_CUSTOMER_ASSET_REMAINS_UNSAVED_PASS");
        }
        finally
        {
            // Restore only the deliberately mutated QA object IN MEMORY.
            // The real product never writes or clears another user's dirty asset.
            unrelated.DisplayName = originalName;
            EditorUtility.ClearDirty(unrelated);
        }
    }

    private static string Physical(string path) =>
        Path.Combine(Directory.GetParent(Application.dataPath).FullName, path);

    private static string SHA256(string path)
    {
        using (var input = File.OpenRead(path))
        using (var sha = System.Security.Cryptography.SHA256.Create())
            return Convert.ToBase64String(sha.ComputeHash(input));
    }
}
#endif
