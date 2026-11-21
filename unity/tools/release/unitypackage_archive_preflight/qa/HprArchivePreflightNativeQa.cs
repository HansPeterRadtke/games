#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Security.Cryptography;
using HPR.ArchivePreflight;
using UnityEditor;
using UnityEngine;

// Private original real native Editor QA. NEVER part of the buyer package.
public static class HprArchivePreflightNativeQa
{
    private static void Check(bool okay, string what)
    { if (!okay) throw new InvalidOperationException("HPR_ARCHIVE_QA_FAIL " + what); }

    private static string Hash(string path)
    {
        using (var h = SHA256.Create())
        using (var file = File.OpenRead(path))
            return BitConverter.ToString(h.ComputeHash(file));
    }

    public static void Run()
    {
        var evidence = Environment.GetEnvironmentVariable("HPR_ARCHIVE_PREFLIGHT_QA_OUT");
        string oldArchive = Environment.GetEnvironmentVariable("HPR_ARCHIVE_PREFLIGHT_OLD");
        string newArchive = Environment.GetEnvironmentVariable("HPR_ARCHIVE_PREFLIGHT_NEW");
        string badMeta = Environment.GetEnvironmentVariable("HPR_ARCHIVE_PREFLIGHT_BAD_META");
        string changedGuid = Environment.GetEnvironmentVariable("HPR_ARCHIVE_PREFLIGHT_CHANGED_GUID");
        string unsafePath = Environment.GetEnvironmentVariable("HPR_ARCHIVE_PREFLIGHT_UNSAFE_PATH");
        string truncated = Environment.GetEnvironmentVariable("HPR_ARCHIVE_PREFLIGHT_TRUNCATED");
        string link = Environment.GetEnvironmentVariable("HPR_ARCHIVE_PREFLIGHT_SYMLINK");
        string movedArchive = Environment.GetEnvironmentVariable("HPR_COEXISTENCE_MOVED_ARCHIVE");
        string caseArchive = Environment.GetEnvironmentVariable("HPR_COEXISTENCE_CASE_ARCHIVE");
        Check(Application.isBatchMode && !string.IsNullOrEmpty(evidence) &&
            evidence.StartsWith("/data/var/marketplace-account-setup/unity-20261121-wave52/",StringComparison.Ordinal) &&
            !Directory.Exists(evidence) && !File.Exists(evidence), "fresh_private_evidence");
        Check(new[]{oldArchive,newArchive,badMeta,changedGuid,unsafePath,truncated,link,movedArchive,caseArchive}
                .All(path=>!string.IsNullOrEmpty(path) && Path.IsPathRooted(path) && File.Exists(path)),
                "existing_read_only_real_archives_and_negative_fixtures_required");
        string oldDigest = Hash(oldArchive);
        string newDigest = Hash(newArchive);
        var older = HprUnitypackageArchiveReader.Inspect(oldArchive);
        var newer = HprUnitypackageArchiveReader.Inspect(newArchive);
        Debug.Log("HPR_ARCHIVE_DEBUG legacy="+older.status+" reason="+older.reason+
            " count="+older.pathsChecked+" updated="+newer.status+" reason="+newer.reason+
            " count="+newer.pathsChecked);
        Check(older.status == "READABLE_STRICT_ARCHIVE" && older.pathsChecked == 5 &&
              newer.status == "READABLE_STRICT_ARCHIVE" && newer.pathsChecked == 6 &&
              older.assets.All(a=>a.guid.Length==32 && a.importerHash.Length==64),
              "real_Unity_packages_strict_readable");
        var preview = HprUnitypackageArchiveReader.Compare(older,newer);
        Check(!preview.incomplete && preview.addedPaths==1 && preview.replacedGuids==0 &&
            preview.removedPaths==0 && preview.movedPaths==0 && preview.sourceChanges>=1 &&
            preview.status=="REVIEW_CONTENT_OR_IMPORT_CHANGES" &&
            preview.findings.Any(f=>f.kind=="ADDED_ASSET") &&
            preview.findings.Any(f=>f.kind=="SOURCE_BYTES_CHANGED"),
            "real_existing_buyer_upgrade_exposes_content_changes_not_just_GUIDs");
        var replaced = HprUnitypackageArchiveReader.Compare(older,
            HprUnitypackageArchiveReader.Inspect(changedGuid));
        Check(!replaced.incomplete && replaced.replacedGuids==1 &&
            replaced.status=="REVIEW_POTENTIAL_REFERENCE_BREAKAGE" &&
            replaced.findings.Any(f=>f.kind=="GUID_REPLACED_AT_PATH"),
            "genuine_archive_GUID_change_warns_before_import");
        Check(HprUnitypackageArchiveReader.Inspect(badMeta).status=="INCOMPLETE",
            "metadata_GUID_mismatch_fails_closed");
        Check(HprUnitypackageArchiveReader.Inspect(unsafePath).status=="INCOMPLETE",
            "path_traversal_fails_closed");
        Check(HprUnitypackageArchiveReader.Inspect(truncated).status=="INCOMPLETE",
            "truncated_gzip_tar_fails_closed");
        Check(HprUnitypackageArchiveReader.Inspect(link).status=="INCOMPLETE",
            "symlink_tar_member_rejected");
        var cancel = HprUnitypackageArchiveReader.Inspect(newArchive,()=>true);
        Check(cancel.status=="INCOMPLETE" && cancel.reason.Contains("canceled"),
            "user_cancelled_scan_cannot_pass");
        string output = Path.Combine(evidence,"actual-native-upgrade-preview.json");
        Directory.CreateDirectory(evidence);
        HprUnitypackageArchiveReader.ExportNew(preview,output);
        string exported = File.ReadAllText(output);
        bool refused=false;
        try { HprUnitypackageArchiveReader.ExportNew(preview,output); }
        catch (IOException) { refused=true; }
        Check(refused && exported==File.ReadAllText(output) &&
            exported.Contains("REVIEW_CONTENT_OR_IMPORT_CHANGES"),
            "result_export_create_only_and_readable");
        Check(oldDigest==Hash(oldArchive) && newDigest==Hash(newArchive),
            "both_archives_unchanged_by_scanning");
        // The exact three small buyer samples must really be present,
        // inspector-readable, and unmodified after both scan modes.
        string sampleFolder = Path.Combine(Directory.GetParent(Application.dataPath).FullName,
            "Assets/HPRArchivePreflight/Samples");
        string[] labels={"baseline","additions_only","changed_guid"};
        string[] sampleFiles=labels.Select(name=>Path.Combine(sampleFolder,
            "HprExample-"+name+".unitypackage")).ToArray();
        Check(sampleFiles.All(File.Exists), "all_three_first_party_archives_installed");
        string[] sampleBeforeHash=sampleFiles.Select(Hash).ToArray();
        var sampleBefore=HprUnitypackageArchiveReader.Inspect(sampleFiles[0]);
        var sampleAdd=HprUnitypackageArchiveReader.Inspect(sampleFiles[1]);
        var sampleRisk=HprUnitypackageArchiveReader.Inspect(sampleFiles[2]);
        Check(sampleBefore.status=="READABLE_STRICT_ARCHIVE" && sampleBefore.pathsChecked==3 &&
            sampleAdd.status=="READABLE_STRICT_ARCHIVE" && sampleAdd.pathsChecked==4 &&
            sampleRisk.status=="READABLE_STRICT_ARCHIVE" && sampleRisk.pathsChecked==3,
            "three_genuine_unity_authored_example_archives_parse");
        var safeSample=HprUnitypackageArchiveReader.Compare(sampleBefore,sampleAdd);
        Check(!safeSample.incomplete && safeSample.status=="ADDITIONS_ONLY" &&
            safeSample.addedPaths==1 && safeSample.replacedGuids==0 &&
            safeSample.removedPaths==0 && safeSample.sourceChanges==0 &&
            safeSample.importerChanges==0,
            "included_example_explains_one_addition_not_an_engine_error");
        var riskSample=HprUnitypackageArchiveReader.Compare(sampleBefore,sampleRisk);
        Check(!riskSample.incomplete && riskSample.status=="REVIEW_POTENTIAL_REFERENCE_BREAKAGE" &&
            riskSample.replacedGuids==1 && riskSample.findings.Any(f=>f.kind=="GUID_REPLACED_AT_PATH"),
            "included_example_warns_about_intentionally_replaced_guid");
        // Genuine first-party separately exported packages can coexist or
        // collide. A valid UPGRADE move is an unsafe independent-PACK collision.
        string movedHash = Hash(movedArchive);
        var moved=HprUnitypackageArchiveReader.Inspect(movedArchive);
        Check(moved.status=="READABLE_STRICT_ARCHIVE" && moved.pathsChecked==3,
            "actual_unity_export_with_path_moved_guid_preserved_parses");
        var coexistSafe=HprArchiveCoexistence.Compare(sampleBefore,sampleAdd);
        Check(!coexistSafe.incomplete &&
            coexistSafe.status=="NO_OVERLAP_CONFLICTS_IN_CHECKED_ARCHIVES" &&
            coexistSafe.identicalSharedAssets==3 && coexistSafe.guidCollisions==0 &&
            coexistSafe.pathCollisions==0 && coexistSafe.overwriteRisks==0,
            "same_identity_and_bytes_are_not_false_independent_collisions");
        var coexistPath=HprArchiveCoexistence.Compare(sampleBefore,sampleRisk);
        Check(!coexistPath.incomplete &&
            coexistPath.status=="REVIEW_INDEPENDENT_PACKAGE_COLLISIONS" &&
            coexistPath.pathCollisions==1 && coexistPath.guidCollisions==0 &&
            coexistPath.findings.Any(f=>f.kind=="PATH_REUSED_WITH_DIFFERENT_GUID"),
            "two_independent_packages_different_guids_at_same_path_warn");
        var coexistGuid=HprArchiveCoexistence.Compare(sampleBefore,moved);
        Check(!coexistGuid.incomplete &&
            coexistGuid.status=="REVIEW_INDEPENDENT_PACKAGE_COLLISIONS" &&
            coexistGuid.guidCollisions==1 && coexistGuid.pathCollisions==0 &&
            coexistGuid.findings.Any(f=>f.kind=="GUID_REUSED_AT_DIFFERENT_PATH"),
            "genuine_renamed_path_reusing_guid_is_collision_if_both_installed");
        var movedUpgrade=HprUnitypackageArchiveReader.Compare(sampleBefore,moved);
        Check(!movedUpgrade.incomplete && movedUpgrade.status=="REVIEW_PATH_MIGRATION" &&
            movedUpgrade.movedPaths==1 && movedUpgrade.replacedGuids==0,
            "same_renamed_guid_can_be_upgrade_migration_not_safe_coexistence");
        var coexistDifferentBytes=HprArchiveCoexistence.Compare(older,newer);
        Check(!coexistDifferentBytes.incomplete &&
            coexistDifferentBytes.status=="REVIEW_INDEPENDENT_PACKAGE_COLLISIONS" &&
            coexistDifferentBytes.overwriteRisks>=1 &&
            coexistDifferentBytes.findings.Any(f=>f.kind=="SHARED_GUID_PATH_DIFFERENT_BYTES"),
            "two_real_versions_as_independent_products_could_silently_overwrite");
        Check(HprArchiveCoexistence.Compare(HprUnitypackageArchiveReader.Inspect(badMeta),sampleBefore)
            .status=="INCOMPLETE" &&
            HprArchiveCoexistence.Compare(null,sampleBefore).incomplete,
            "malformed_or_null_release_fails_closed_for_coexistence");
        string coexistFile=Path.Combine(evidence,"actual-independent-coexistence-preview.json");
        HprArchiveCoexistence.ExportNew(coexistGuid,coexistFile);
        bool coexistOverwriteBlocked=false;
        try { HprArchiveCoexistence.ExportNew(coexistGuid,coexistFile); }
        catch (IOException) { coexistOverwriteBlocked=true; }
        Check(coexistOverwriteBlocked && File.ReadAllText(coexistFile).Contains("GUID_REUSED_AT_DIFFERENT_PATH"),
            "independent_collision_report_export_create_only");
        // Unity AssetDatabase paths are case-insensitive; comparing as Ordinal
        // previously missed genuinely distinct archive paths differing only
        // by letter case and GUID. Use a real Editor-exported first-party file.
        string caseHash=Hash(caseArchive);
        var changedCase=HprUnitypackageArchiveReader.Inspect(caseArchive);
        Check(changedCase.status=="READABLE_STRICT_ARCHIVE" && changedCase.pathsChecked==3,
            "actual_Unity_case_only_path_fixture_parses");
        var caseCollision=HprArchiveCoexistence.Compare(sampleBefore,changedCase);
        Check(!caseCollision.incomplete &&
            caseCollision.status=="REVIEW_INDEPENDENT_PACKAGE_COLLISIONS" &&
            caseCollision.caseOnlyPathCollisions==1 && caseCollision.pathCollisions==0 &&
            caseCollision.guidCollisions==0 && caseCollision.identicalSharedAssets==2 &&
            caseCollision.findings.Any(f=>f.kind=="CASE_ONLY_ASSET_PATH_COLLISION") &&
            Hash(caseArchive)==caseHash,
            "actual_Unity_case_only_distinct_guid_collision_warns_and_input_unchanged");
        // Independently guard the publicly callable comparator against an
        // internally inconsistent caller snapshot containing case twins.
        var badCaller=new HprArchiveInspection
        {
            status="READABLE_STRICT_ARCHIVE", pathsChecked=2,
            assets=new [] {sampleBefore.assets.First(a=>a.assetPath.EndsWith("Example.txt")),
                changedCase.assets.First(a=>a.assetPath.EndsWith("example.TXT"))}
        };
        Check(HprArchiveCoexistence.Compare(badCaller,sampleBefore).status=="INCOMPLETE",
            "case_only_duplicate_paths_in_serialized_caller_snapshot_fail_closed");
        Check(Hash(movedArchive)==movedHash && sampleBeforeHash.SequenceEqual(sampleFiles.Select(Hash)),
            "genuine_guid_collision_fixtures_remain_unmodified");
        Check(sampleBeforeHash.SequenceEqual(sampleFiles.Select(Hash)),
            "included_genuine_sample_archive_bytes_not_edited_by_comparison");
        Check(AssetDatabase.IsValidFolder("Assets/HPRArchivePreflight") &&
            AssetDatabase.LoadMainAssetAtPath("Assets/HPRArchivePreflight/Editor/HprUnitypackageArchiveReader.cs")!=null &&
            AssetDatabase.LoadMainAssetAtPath("Assets/HPRArchivePreflight/Editor/HprUnitypackageArchiveWindow.cs")!=null &&
            AssetDatabase.LoadMainAssetAtPath("Assets/HPRArchivePreflight/Editor/HprArchiveCoexistence.cs")!=null,
            "real_original_scanner_and_GUI_installed_in_project");
        using (var stream=new FileStream(Path.Combine(evidence,"native-receipt.txt"),FileMode.CreateNew,FileAccess.Write,FileShare.None))
        using (var writer=new StreamWriter(stream,new UTF8Encoding(false)))
        {
            foreach(var line in new []{
                "real_old_and_new_unitypackage_archives_parsed=PASS",
                "read_only_real_content_and_added_script_report=PASS",
                "real_archive_with_changed_guids_risk_flagged=PASS",
                "metadata_guid_mismatch_fails_closed=PASS",
                "archive_path_traversal_fails_closed=PASS",
                "truncated_gzip_tar_fails_closed=PASS",
                "tar_symlink_is_rejected=PASS",
                "cancel_scan_fails_closed=PASS",
                "create_only_report_export=PASS",
                "real_old_and_new_archive_hashes_unchanged=PASS",
                "actual_unity_editor_scanner_and_window_installed=PASS",
                "all_three_original_unity_exported_archives_imported=PASS",
                "included_additions_only_sample_explains_no_identity_breakage=PASS",
                "included_changed_guid_sample_warns_accurately=PASS",
                "included_original_archive_bytes_unchanged=PASS",
                "real_moved_guid_archive_parsed=PASS",
                "independent_identical_overlap_does_not_false_alert=PASS",
                "independent_path_collision_detected=PASS",
                "independent_guid_reused_different_path_detected=PASS",
                "upgrade_migration_distinct_from_coexistence_collision=PASS",
                "independent_packages_different_bytes_warn_overwrite=PASS",
                "invalid_coexistence_input_fails_closed=PASS",
                "coexistence_report_create_only_export=PASS",
                "coexistence_moved_original_archive_unchanged=PASS",
                "real_Unity_case_only_path_collision_warns=PASS",
                "case_only_duplicate_caller_snapshot_rejected=PASS"})writer.WriteLine(line);
            writer.WriteLine("unity_version="+Application.unityVersion);
        }
        Debug.Log("HPR_ARCHIVE_PREFLIGHT_NATIVE_PASS "+Application.unityVersion+
                  " changed_contents="+preview.sourceChanges);
    }
}
#endif
