#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using HPR.PackageBoundary;
using UnityEditor;
using UnityEngine;

// Private independent native buyer-upgrade validation, never shipped.
public static class HprBoundaryRealUpgradeAfterQa
{
    private static void Check(bool valid, string message)
    { if (!valid) throw new InvalidOperationException("HPR_REAL_UPGRADE_AFTER_FAIL " + message); }

    public static void Run()
    {
        string evidence = Environment.GetEnvironmentVariable("HPR_BOUNDARY_UPGRADE_EVIDENCE_ROOT");
        Check(Application.isBatchMode && !string.IsNullOrWhiteSpace(evidence) &&
            evidence.StartsWith("/data/var/marketplace-account-setup/unity-20261121-wave49/",
                StringComparison.Ordinal) && Directory.Exists(evidence),
            "private_owned_evidence_location_required");
        string saved = Path.Combine(evidence, "before-native-vendor-identity.json");
        string receipt = Path.Combine(evidence, "after-native-upgrade-receipt.txt");
        Check(File.Exists(saved) && !File.Exists(receipt), "baseline_required_no_replay");
        var snapshot = JsonUtility.FromJson<HprRealUpgradeBaseline>(File.ReadAllText(saved));
        Check(snapshot != null && snapshot.vendor != null && snapshot.vendor.Length == 5 &&
              snapshot.customerFiles != null && snapshot.customerFiles.Length >= 3 &&
              snapshot.unityVersion == Application.unityVersion,
            "complete_matching_editor_before_snapshot_required");
        foreach (var original in snapshot.vendor)
        {
            Check(AssetDatabase.LoadMainAssetAtPath(original.path) != null &&
                  AssetDatabase.AssetPathToGUID(original.path) == original.guid &&
                  AssetDatabase.GUIDToAssetPath(original.guid) == original.path,
                "legacy_vendor_path_guid_identity_not_preserved " + original.path);
        }
        string newFile = HprBoundaryRealUpgradeBeforeQa.VendorRoot +
            "/Editor/HprBoundaryUpgradeReview.cs";
        string newGuid = AssetDatabase.AssetPathToGUID(newFile);
        Check(AssetDatabase.LoadMainAssetAtPath(newFile) != null && newGuid.Length == 32 &&
              !snapshot.vendor.Any(x => x.guid == newGuid), "exact_one_new_vendor_editor_script");
        string project = Directory.GetParent(Application.dataPath).FullName;
        string buyerRoot = HprBoundaryRealUpgradeBeforeQa.CustomerRoot;
        foreach (var item in snapshot.customerFiles)
        {
            string path = Path.Combine(project, item.path);
            Check(File.Exists(path) && HprBoundaryRealUpgradeBeforeQa.Hash(path) == item.sha256,
                "buyer_file_bytes_or_meta_changed_on_import " + item.path);
        }
        string[] nowBuyer = Directory.GetFiles(Path.Combine(project,buyerRoot), "*",SearchOption.AllDirectories)
            .Select(path => path.Substring(project.Length + 1).Replace('\\','/'))
            .OrderBy(path => path,StringComparer.Ordinal).ToArray();
        Check(nowBuyer.SequenceEqual(snapshot.customerFiles.Select(x=>x.path).OrderBy(x=>x,StringComparer.Ordinal)),
            "buyer_owned_file_inventory_changed_during_vendor_upgrade");
        var buyerAsset = AssetDatabase.LoadAssetAtPath<HprRealUpgradeBuyerReference>(
            buyerRoot + "/BuyerReferences.asset");
        Check(buyerAsset != null && buyerAsset.vendorReadme != null &&
              AssetDatabase.GetAssetPath(buyerAsset.vendorReadme) ==
                HprBoundaryRealUpgradeBeforeQa.VendorRoot + "/README.md",
            "serialized_customer_asset_reference_still_resolves_after_real_upgrade");
        var previous = new BoundaryReport
        {
            schemaVersion = 1,
            root = HprBoundaryRealUpgradeBeforeQa.VendorRoot,
            status = "NO_RESOLVED_EXTERNAL_DEPENDENCIES_FOUND",
            assetsChecked = snapshot.vendor.Count(x =>
                !AssetDatabase.IsValidFolder(x.path)),
            identities = snapshot.vendor.Where(x => !AssetDatabase.IsValidFolder(x.path))
                .Select(x => new BoundaryIdentity { assetPath = x.path, guid = x.guid }).ToArray(),
            findings = new BoundaryFinding[0], incomplete = false
        };
        var current = HprPackageBoundaryScanner.Scan(previous.root);
        Check(current != null && !current.incomplete && current.identities.Length == 4,
            "new_four_file_vendor_root_scanned_completely");
        var compared = HprBoundaryUpgradeReview.Compare(previous,current);
        Check(!compared.incomplete && compared.status == "ADDITIONS_ONLY" &&
              compared.addedAssets == 1 && compared.replacedGuids == 0 &&
              compared.removedAssets == 0 && compared.movedPaths == 0,
            "real_legacy_to_current_vendor_upgrade_must_preserve_every_old_identity");
        string reportPath = Path.Combine(evidence, "actual-native-upgrade-diff.json");
        HprBoundaryUpgradeReview.ExportNewJson(compared, reportPath);
        using (var stream = new FileStream(receipt, FileMode.CreateNew, FileAccess.Write, FileShare.None))
        using (var writer = new StreamWriter(stream, new UTF8Encoding(false)))
        {
            writer.WriteLine("exact_old_new_archives_installed_in_same_real_buyer_project=PASS");
            writer.WriteLine("five_old_vendor_guids_unchanged=PASS");
            writer.WriteLine("one_new_editor_source_added=PASS");
            writer.WriteLine("all_customer_file_sha256_and_inventory_unchanged=PASS");
            writer.WriteLine("serialized_customer_reference_to_vendor_document_resolves=PASS");
            writer.WriteLine("upgrade_comparison_additions_only=PASS");
            writer.WriteLine("create_only_machine_upgrade_diff=PASS");
            writer.WriteLine("unity_version=" + Application.unityVersion);
        }
        Debug.Log("HPR_REAL_BUYER_UPGRADE_NATIVE_PASS " + Application.unityVersion +
                  " preserved_customer_files=" + snapshot.customerFiles.Length);
    }
}
#endif
