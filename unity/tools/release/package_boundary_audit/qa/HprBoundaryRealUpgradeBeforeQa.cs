#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using UnityEditor;
using UnityEngine;

// Private genuine buyer-upgrade test only; not part of any vendor package.
[Serializable]
public sealed class HprRealUpgradeAssetIdentity
{
    public string path;
    public string guid;
}

[Serializable]
public sealed class HprRealUpgradeBuyerHash
{
    public string path;
    public string sha256;
}

[Serializable]
public sealed class HprRealUpgradeBaseline
{
    public string unityVersion;
    public HprRealUpgradeAssetIdentity[] vendor;
    public HprRealUpgradeBuyerHash[] customerFiles;
}

public static class HprBoundaryRealUpgradeBeforeQa
{
    public const string VendorRoot = "Assets/HPRPackageBoundary";
    public const string CustomerRoot = "Assets/HprBoundaryUpgradeCustomerFixture";
    private static void Check(bool valid, string message)
    { if (!valid) throw new InvalidOperationException("HPR_REAL_UPGRADE_BEFORE_FAIL " + message); }

    public static string Hash(string path)
    {
        using (var sha = SHA256.Create())
            return BitConverter.ToString(sha.ComputeHash(File.ReadAllBytes(path))).Replace("-", "");
    }

    public static void Run()
    {
        string evidence = Environment.GetEnvironmentVariable("HPR_BOUNDARY_UPGRADE_EVIDENCE_ROOT");
        Check(Application.isBatchMode && !string.IsNullOrWhiteSpace(evidence) &&
            Path.IsPathRooted(evidence) && evidence.StartsWith(
                "/data/var/marketplace-account-setup/unity-20261121-wave49/", StringComparison.Ordinal) &&
            Directory.Exists(evidence), "owned_existing_private_evidence_directory_required");
        string before = Path.Combine(evidence, "before-native-vendor-identity.json");
        Check(!File.Exists(before) && AssetDatabase.IsValidFolder(CustomerRoot) &&
            AssetDatabase.LoadAssetAtPath<MonoScript>(CustomerRoot +
                "/HprRealUpgradeBuyerReference.cs") != null &&
            AssetDatabase.LoadMainAssetAtPath(CustomerRoot + "/BuyerReferences.asset") == null,
            "fresh_runtime_customer_script_and_no_uncertain_replay");
        string[] oldPaths = new[]
        {
            VendorRoot, VendorRoot + "/Editor", VendorRoot + "/README.md",
            VendorRoot + "/LICENSE.md", VendorRoot + "/Editor/HprPackageBoundaryWindow.cs"
        };
        Check(oldPaths.All(p => AssetDatabase.LoadMainAssetAtPath(p) != null),
            "all_original_old_package_assets_are_present");
        Check(AssetDatabase.LoadMainAssetAtPath(VendorRoot + "/Editor/HprBoundaryUpgradeReview.cs") == null,
            "updated_script_must_not_already_be_installed");
        var ids = oldPaths.Select(path => new HprRealUpgradeAssetIdentity
            { path = path, guid = AssetDatabase.AssetPathToGUID(path) }).ToArray();
        Check(ids.All(x => x.guid != null && x.guid.Length == 32) &&
            ids.Select(x => x.guid).Distinct(StringComparer.Ordinal).Count() == ids.Length,
            "valid_distinct_legacy_vendor_guids");
        string readme = VendorRoot + "/README.md";
        var referenced = AssetDatabase.LoadMainAssetAtPath(readme);
        Check(referenced != null, "vendor_readme_can_be_referenced_by_actual_buyer_data");
        var buyer = ScriptableObject.CreateInstance<HprRealUpgradeBuyerReference>();
        buyer.vendorReadme = referenced;
        string buyerAsset = CustomerRoot + "/BuyerReferences.asset";
        AssetDatabase.CreateAsset(buyer, buyerAsset);
        string project = Directory.GetParent(Application.dataPath).FullName;
        string customerNote = CustomerRoot + "/buyer-owned-note.txt";
        File.WriteAllText(Path.Combine(project, customerNote), "Original buyer file must remain unchanged after vendor package update.\n");
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        var persisted = AssetDatabase.LoadAssetAtPath<HprRealUpgradeBuyerReference>(buyerAsset);
        Check(persisted != null && persisted.vendorReadme != null &&
            AssetDatabase.GetAssetPath(persisted.vendorReadme) == readme,
            "real_serialized_buyer_reference_to_vendor_asset_created");
        string directory = Path.Combine(project, CustomerRoot);
        var files = Directory.GetFiles(directory, "*", SearchOption.AllDirectories)
            .Where(p => !p.EndsWith(".tmp", StringComparison.OrdinalIgnoreCase))
            .OrderBy(p => p, StringComparer.Ordinal).Select(full => new HprRealUpgradeBuyerHash
            { path = full.Substring(project.Length + 1).Replace('\\','/'), sha256 = Hash(full) }).ToArray();
        Check(files.Length >= 3, "buyer_asset_and_metadata_really_exist");
        var snapshot = new HprRealUpgradeBaseline
        { unityVersion = Application.unityVersion, vendor = ids, customerFiles = files };
        using (var stream = new FileStream(before, FileMode.CreateNew, FileAccess.Write, FileShare.None))
        using (var writer = new StreamWriter(stream)) writer.Write(JsonUtility.ToJson(snapshot, true));
        Debug.Log("HPR_REAL_UPGRADE_BEFORE_NATIVE_PASS " + Application.unityVersion +
                  " preserved_customer_files=" + files.Length);
    }
}
#endif
