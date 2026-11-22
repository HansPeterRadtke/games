#if UNITY_EDITOR
using System;
using System.IO;
using UnityEngine;
using HPR.ImportedPrefabParity;

// PRIVATE authentic two-editor difference check against actual native receipt bytes.
public static class HprPrefabParityTwoEditorQa
{
    private static void Require(bool yes,string why)
    {if(!yes)throw new InvalidOperationException("HPR_PREFAB_TWO_EDITOR_QA_FAILURE:"+why);}
    public static void Run()
    {
        string a=Environment.GetEnvironmentVariable("HPR_PREFAB_FIRST_RECEIPT")??"";
        string b=Environment.GetEnvironmentVariable("HPR_PREFAB_SECOND_RECEIPT")??"";
        string output=Environment.GetEnvironmentVariable("HPR_PREFAB_TWO_EDITOR_OUT")??"";
        const string safe="/data/var/marketplace-account-setup/unity-prefab-state-parity-20261122-wave59/";
        Require(Application.isBatchMode && a.StartsWith(safe,StringComparison.Ordinal) &&
            b.StartsWith(safe,StringComparison.Ordinal) && output.StartsWith(safe,StringComparison.Ordinal) &&
            Path.IsPathRooted(output) && !File.Exists(output),"immutable_native_editor_inputs");
        var first=HprPrefabStateCompare.ReadReceipt(a);
        var second=HprPrefabStateCompare.ReadReceipt(b);
        Require(first.unityVersion=="2022.3.22f1" && second.unityVersion=="6000.6.8f1" &&
            first.inputs.Length==3 && second.inputs.Length==3,
            "genuine_original_prefabs_in_real_two_editors");
        var compare=HprPrefabStateCompare.Compare(first,second);
        Require(compare.status!="SOURCE_BYTES_DIFFER_NO_EDITOR_INFERENCE",
            "same_original_vendor_source_proven");
        HprPrefabStateCompare.ExportNew(compare,output);
        bool refused=false;
        try{HprPrefabStateCompare.ExportNew(compare,output);}catch(IOException){refused=true;}
        Require(refused,"create_only_comparison_rejects_repeated_write");
        Debug.Log("HPR_PREFAB_PARITY_TWO_REAL_EDITOR_PASS "+compare.status+
            " values="+first.valuesCaptured+"/"+second.valuesCaptured+
            " changed="+compare.changedValueKeys.Length+
            " added="+compare.addedValueKeys.Length+
            " removed="+compare.removedValueKeys.Length+
            " unsupported="+compare.unsupportedComponents);
    }
}
#endif
