#if UNITY_EDITOR
using System;
using System.IO;
using System.Reflection;
using UnityEditor;
using UnityEngine;
using HPR.ImportedPrefabParity;

// PRIVATE actual graphical Unity Editor screenshot QA. Reflection is only on our own windows.
// Never shipped as a buyer script; no source prefab or project settings writes.
public static class HprNestedCustomGraphicalQa
{
    private static void Require(bool okay,string rule)
    {if(!okay)throw new InvalidOperationException("HPR_NESTED_CUSTOM_GUI_QA_FAILURE:"+rule);}
    private static void Populate(EditorWindow window,string field,object value)
    {
        var member=window.GetType().GetField(field,BindingFlags.Instance|BindingFlags.NonPublic);
        Require(member!=null,"own_private_window_field_"+field);
        member.SetValue(window,value);
    }
    public static void Run()
    {
        const string safe="/data/var/marketplace-account-setup/unity-nested-custom-20261123-wave62/";
        string receipt=Environment.GetEnvironmentVariable("HPR_NESTED_GUI_RECEIPT")??"";
        string first=Environment.GetEnvironmentVariable("HPR_NESTED_GUI_FIRST")??"";
        string second=Environment.GetEnvironmentVariable("HPR_NESTED_GUI_SECOND")??"";
        Require(!Application.isBatchMode && receipt.StartsWith(safe,StringComparison.Ordinal) &&
            Path.IsPathRooted(receipt) && !File.Exists(receipt) && File.Exists(first) && File.Exists(second),
            "isolated_original_Unity_graphical_setup");
        string paths="Assets/HPRNestedCustomAcceptance/Prefabs/OriginalMachine.prefab;"+
            "Assets/HPRNestedCustomAcceptance/Prefabs/OriginalMachineVariant.prefab;"+
            "Assets/HPRNestedCustomAcceptance/Prefabs/OriginalMachineAssembly.prefab";
        var original=HprPrefabStateScan.Scan(paths);
        Require(!original.incomplete && original.inputs.Length==3 &&
            original.unsupportedComponents>=3,"real_nested_original_custom_fields_uninspected");
        var comparison=HprPrefabStateCompare.Compare(
            HprPrefabStateCompare.ReadReceipt(first),
            HprPrefabStateCompare.ReadReceipt(second));
        Require(comparison.status=="COVERED_VALUES_MATCH_UNINSPECTED_COMPONENTS" &&
            comparison.unsupportedComponents>=6,
            "original_custom_scripts_must_never_get_silent_all_clean_verdict");
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
            Populate(window,"notice","Covered values match; custom serialized script fields remain UNINSPECTED. Review required.");
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
                    writer.WriteLine("uninspected_custom_component_occurrences="+comparison.unsupportedComponents);
                    writer.WriteLine("actual_real_window_not_a_mockup=TRUE");
                    writer.WriteLine("private_harness_populated_window=TRUE");
                    writer.WriteLine("human_clicked_controls=FALSE");
                    writer.WriteLine("software_terms_accepted=FALSE");
                }
                Debug.Log("HPR_NESTED_CUSTOM_GRAPHICAL_NATIVE_PASS "+comparison.status);
            };
        };
    }
}
#endif
