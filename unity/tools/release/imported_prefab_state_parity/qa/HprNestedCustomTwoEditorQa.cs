#if UNITY_EDITOR
using System;
using System.IO;
using UnityEngine;
using HPR.ImportedPrefabParity;

// PRIVATE authentic two-editor difference check against actual native receipt bytes.
public static class HprNestedCustomTwoEditorQa
{
    private static void Require(bool yes,string why)
    {if(!yes)throw new InvalidOperationException("HPR_NESTED_CUSTOM_TWO_EDITOR_QA_FAILURE:"+why);}
    public static void Run()
    {
        string a=Environment.GetEnvironmentVariable("HPR_NESTED_FIRST_RECEIPT")??"";
        string b=Environment.GetEnvironmentVariable("HPR_NESTED_SECOND_RECEIPT")??"";
        string output=Environment.GetEnvironmentVariable("HPR_NESTED_TWO_EDITOR_OUT")??"";
        const string safe="/data/var/marketplace-account-setup/unity-nested-custom-20261123-wave62/";
        Require(Application.isBatchMode && a.StartsWith(safe,StringComparison.Ordinal) &&
            b.StartsWith(safe,StringComparison.Ordinal) && output.StartsWith(safe,StringComparison.Ordinal) &&
            Path.IsPathRooted(output) && !File.Exists(output),"immutable_native_editor_inputs");
        var first=HprPrefabStateCompare.ReadReceipt(a);
        var second=HprPrefabStateCompare.ReadReceipt(b);
        Require(first.unityVersion=="2022.3.22f1" && second.unityVersion=="6000.6.8f1" &&
            first.inputs.Length==3 && second.inputs.Length==3 &&
            first.unsupportedComponents==3 && second.unsupportedComponents==3 &&
            first.valuesCaptured==69 && second.valuesCaptured==69,
            "genuine_original_prefabs_in_real_two_editors");
        var compare=HprPrefabStateCompare.Compare(first,second);
        Require(compare.status=="COVERED_VALUES_MATCH_UNINSPECTED_COMPONENTS" &&
            compare.unsupportedComponents==6 &&
            compare.sourceDifferences.Length==0 && compare.dependencyDifferences.Length==0 &&
            compare.unverifiedDependencyPaths.Length==0 &&
            compare.changedValueKeys.Length==0 &&
            compare.addedValueKeys.Length==0 && compare.removedValueKeys.Length==0,
            "genuine_original_custom_scripts_yield_caution_not_full_parity");
        HprPrefabStateCompare.ExportNew(compare,output);
        bool refused=false;
        try{HprPrefabStateCompare.ExportNew(compare,output);}catch(IOException){refused=true;}
        Require(refused,"create_only_comparison_rejects_repeated_write");
        Debug.Log("HPR_NESTED_CUSTOM_TWO_REAL_EDITOR_PASS "+compare.status+
            " values="+first.valuesCaptured+"/"+second.valuesCaptured+
            " changed="+compare.changedValueKeys.Length+
            " added="+compare.addedValueKeys.Length+
            " removed="+compare.removedValueKeys.Length+
            " dependency_changes="+compare.dependencyDifferences.Length+
            " unverified_dependencies="+compare.unverifiedDependencyPaths.Length+
            " unsupported="+compare.unsupportedComponents);
    }
}
#endif
