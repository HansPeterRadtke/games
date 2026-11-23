#if UNITY_EDITOR
using System;
using System.IO;
using System.Reflection;
using UnityEditor;
using UnityEngine;
using HPR.ImportedPrefabParity;

// PRIVATE actual graphical Unity Editor screenshot QA. Reflection is only on our own windows.
// Never shipped as a buyer script; no source prefab or project settings writes.
public static class HprPrefabParityGraphicalQa
{
    private static void Require(bool okay,string rule)
    {if(!okay)throw new InvalidOperationException("HPR_PREFAB_GUI_QA_FAILURE:"+rule);}
    private static void Populate(EditorWindow window,string field,object value)
    {
        var member=window.GetType().GetField(field,BindingFlags.Instance|BindingFlags.NonPublic);
        Require(member!=null,"own_private_window_field_"+field);
        member.SetValue(window,value);
    }
    public static void Run()
    {
        const string safe="/data/var/marketplace-account-setup/unity-prefab-dependency-20261123-wave61/";
        string receipt=Environment.GetEnvironmentVariable("HPR_PREFAB_GUI_RECEIPT")??"";
        string first=Environment.GetEnvironmentVariable("HPR_PREFAB_GUI_FIRST")??"";
        string second=Environment.GetEnvironmentVariable("HPR_PREFAB_GUI_SECOND")??"";
        Require(!Application.isBatchMode && receipt.StartsWith(safe,StringComparison.Ordinal) &&
            Path.IsPathRooted(receipt) && !File.Exists(receipt) && File.Exists(first) && File.Exists(second),
            "isolated_original_Unity_graphical_setup");
        string paths="Assets/HPRFbxClipIdentity/Samples/Prefabs/OriginalMotionTeachingPrefab.prefab;"+
            "Assets/HPRFbxSourceTakes/Samples/Prefabs/OriginalAutoTwoTake.prefab;"+
            "Assets/HPRFbxSourceTakes/Samples/Prefabs/OriginalConfiguredMissingTake.prefab";
        var original=HprPrefabStateScan.Scan(paths);
        Require(!original.incomplete && original.inputs.Length==3,"original_real_prefab_fields_loaded");
        var comparison=HprPrefabStateCompare.Compare(
            HprPrefabStateCompare.ReadReceipt(first),
            HprPrefabStateCompare.ReadReceipt(second));
        Require(comparison.status!="SOURCE_BYTES_DIFFER_NO_EDITOR_INFERENCE" &&
            comparison.status!="DEPENDENCY_INPUTS_DIFFER_NO_EDITOR_INFERENCE",
            "verified_unchanged_original_vendor_sources_and_referenced_inputs");
        EditorApplication.delayCall += () =>
        {
            HprPrefabStateParityWindow.Open();
            var window=EditorWindow.GetWindow<HprPrefabStateParityWindow>();
            window.position=new Rect(60,90,850,760);
            Populate(window,"paths",paths.Replace(';','\n'));
            Populate(window,"captured",original);
            Populate(window,"first",first);
            Populate(window,"second",second);
            Populate(window,"comparison",comparison);
            Populate(window,"notice","Genuine imported Unity 2022 and Unity 6 loaded prefab values; source assets unchanged.");
            window.Repaint();
            EditorApplication.delayCall += () =>
            {
                using(var file=new FileStream(receipt,FileMode.CreateNew,FileAccess.Write,FileShare.None))
                using(var writer=new StreamWriter(file))
                {
                    writer.WriteLine("original_native_graphical_Editor=TRUE");
                    writer.WriteLine("native_unity_version="+Application.unityVersion);
                    writer.WriteLine("original_prefabs_loaded="+original.inputs.Length);
                    writer.WriteLine("captured_covered_values="+original.valuesCaptured);
                    writer.WriteLine("comparison_status="+comparison.status);
                    writer.WriteLine("actual_real_window_not_a_mockup=TRUE");
                    writer.WriteLine("private_harness_populated_window=TRUE");
                    writer.WriteLine("human_clicked_controls=FALSE");
                    writer.WriteLine("software_terms_accepted=FALSE");
                }
                Debug.Log("HPR_PREFAB_PARITY_GRAPHICAL_NATIVE_PASS "+comparison.status);
            };
        };
    }
}
#endif
