#if UNITY_EDITOR
using System;
using System.IO;
using System.Reflection;
using UnityEditor;
using UnityEngine;
using HPR.PublisherVersionMatrix;

// PRIVATE installed-Editor graphical evidence helper. Not a shipped buyer asset.
// Uses real scan/comparison outputs, never invents or paints a mock window.
public static class HprPublisherVersionGraphicalQa
{
    private static void Require(bool passed,string rule)
    { if(!passed)throw new InvalidOperationException("HPR_VERSION_GUI_QA_FAILURE:"+rule); }

    private static void SetField(object instance,string name,object value)
    {
        var field=instance.GetType().GetField(name,BindingFlags.Instance|BindingFlags.NonPublic);
        Require(field!=null,"original_private_editor_window_field_"+name);
        field.SetValue(instance,value);
    }

    public static void Run()
    {
        string output=Environment.GetEnvironmentVariable("HPR_VERSION_GUI_QA_RECEIPT")??"";
        string first=Environment.GetEnvironmentVariable("HPR_VERSION_GUI_FIRST")??"";
        string second=Environment.GetEnvironmentVariable("HPR_VERSION_GUI_SECOND")??"";
        const string safe="/data/var/marketplace-account-setup/unity-publisher-matrix-20261122-wave58/";
        Require(!Application.isBatchMode && Path.IsPathRooted(output) &&
            output.StartsWith(safe,StringComparison.Ordinal) && !File.Exists(output),
            "real_graphical_unmodified_disposable_editor");
        string roots="Assets/HPRAnimationImportPreflight;Assets/HPRFbxClipIdentity;Assets/HPRFbxSourceTakes";
        var scan=HprPublisherVersionScan.Scan(roots);
        Require(!scan.incomplete && scan.schema==2 && scan.assetCount==18 &&
            scan.assets[0].sourceFileSha256.Length==64 &&
            scan.assets[0].metaFileSha256.Length==64,
            "real_current_native_Editor_scan_with_source_fingerprints");
        Require(File.Exists(first) && File.Exists(second),"original_real_Unity_version_receipts");
        var comparison=HprVersionReceiptCompare.Compare(
            HprVersionReceiptCompare.ReadReceipt(first),
            HprVersionReceiptCompare.ReadReceipt(second));
        Require(comparison.status=="MATCHED_IMPORT_INPUT_BYTES_AND_METADATA" &&
            comparison.sourceFileChanges.Length==0 && comparison.importerMetaChanges.Length==0,
            "original_two_real_versions_byte_identical");
        EditorApplication.delayCall += () =>
        {
            HprPublisherVersionMatrixWindow.Open();
            var window=EditorWindow.GetWindow<HprPublisherVersionMatrixWindow>();
            window.position=new Rect(36,112,750,720);
            SetField(window,"roots",roots);
            SetField(window,"result",scan);
            SetField(window,"notice","Real imported Unity files and SHA-256 source/.meta bytes verified. No asset was modified.");
            window.Repaint();
            HprVersionCompareWindow.Open();
            var compareWindow=EditorWindow.GetWindow<HprVersionCompareWindow>();
            compareWindow.position=new Rect(800,112,750,720);
            SetField(compareWindow,"sourceOne",first);
            SetField(compareWindow,"sourceTwo",second);
            SetField(compareWindow,"result",comparison);
            SetField(compareWindow,"notice","Both actual installed Unity Editor versions have matching original input bytes and metadata; runtime not proven.");
            compareWindow.Repaint();
            EditorApplication.delayCall += () =>
            {
                using(var file=new FileStream(output,FileMode.CreateNew,FileAccess.Write,FileShare.None))
                using(var writer=new StreamWriter(file))
                {
                    writer.WriteLine("native_unity_version="+Application.unityVersion);
                    writer.WriteLine("editor_is_graphical=TRUE");
                    writer.WriteLine("native_editor_publisher_scan_assets="+scan.assetCount);
                    writer.WriteLine("native_editor_comparison_status="+comparison.status);
                    writer.WriteLine("original_editor_windows_real_not_mockup=TRUE");
                    writer.WriteLine("human_clicked_buttons_or_accepted_terms=FALSE");
                    writer.WriteLine("screenshots_are_graphical_window_evidence_not_manual_usability_acceptance=TRUE");
                }
                Debug.Log("HPR_VERSION_GRAPHICAL_NATIVE_QA_PASS");
            };
        };
    }
}
#endif
