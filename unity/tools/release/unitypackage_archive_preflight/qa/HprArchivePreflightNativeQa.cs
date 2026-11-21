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
        Check(Application.isBatchMode && !string.IsNullOrEmpty(evidence) &&
            evidence.StartsWith("/data/var/marketplace-account-setup/unity-20261121-wave50/",StringComparison.Ordinal) &&
            !Directory.Exists(evidence) && !File.Exists(evidence), "fresh_private_evidence");
        Check(new[]{oldArchive,newArchive,badMeta,changedGuid,unsafePath,truncated,link}
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
        Check(AssetDatabase.IsValidFolder("Assets/HPRArchivePreflight") &&
            AssetDatabase.LoadMainAssetAtPath("Assets/HPRArchivePreflight/Editor/HprUnitypackageArchiveReader.cs")!=null &&
            AssetDatabase.LoadMainAssetAtPath("Assets/HPRArchivePreflight/Editor/HprUnitypackageArchiveWindow.cs")!=null,
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
                "actual_unity_editor_scanner_and_window_installed=PASS"})writer.WriteLine(line);
            writer.WriteLine("unity_version="+Application.unityVersion);
        }
        Debug.Log("HPR_ARCHIVE_PREFLIGHT_NATIVE_PASS "+Application.unityVersion+
                  " changed_contents="+preview.sourceChanges);
    }
}
#endif
