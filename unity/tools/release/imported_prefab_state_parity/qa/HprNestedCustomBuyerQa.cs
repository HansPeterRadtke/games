#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using HPR.ImportedPrefabParity;
using HPR.NestedCustomFixture;

// PRIVATE real native buyer acceptance. Only reads original imported prefab asset bytes.
public static class HprNestedCustomBuyerQa
{
    private const string Root="Assets/HPRNestedCustomAcceptance";
    private const string Base=Root+"/Prefabs/OriginalMachine.prefab";
    private const string Variant=Root+"/Prefabs/OriginalMachineVariant.prefab";
    private const string Nested=Root+"/Prefabs/OriginalMachineAssembly.prefab";
    private static void Require(bool yes,string why)
    {if(!yes)throw new InvalidOperationException("HPR_NESTED_CUSTOM_BUYER_FAIL:"+why);}
    public static void Run()
    {
        const string safe="/data/var/marketplace-account-setup/unity-nested-custom-20261123-wave62/";
        string output=Environment.GetEnvironmentVariable("HPR_NESTED_BUYER_RECEIPT")??"";
        Require(Application.isBatchMode && output.StartsWith(safe,StringComparison.Ordinal) &&
            Path.IsPathRooted(output) && !File.Exists(output),"private_create_only_receipt");
        string originals=Base+";"+
            Variant+";"+Nested;
        Require(PrefabUtility.GetPrefabAssetType(AssetDatabase.LoadAssetAtPath<GameObject>(
            Base))==PrefabAssetType.Regular,"genuine_regular_base");
        Require(PrefabUtility.GetPrefabAssetType(AssetDatabase.LoadAssetAtPath<GameObject>(
            Variant))==PrefabAssetType.Variant,"genuine_variant_import");
        Require(AssetDatabase.GetDependencies(Nested,true).Contains(
            Variant),"genuine_nested_variant_dependency");
        Require(AssetDatabase.GetDependencies(Variant,true).Contains(
            Base),"genuine_inherited_base_dependency");
        GameObject actual=null;
        try
        {
            actual=PrefabUtility.LoadPrefabContents(Nested);
            Require(actual!=null && actual.transform.childCount>0,"nested_asset_really_loaded_in_isolated_scene");
            var script=actual.GetComponentInChildren<HprNestedCustomSample>(true);
            Require(script!=null,"actual_custom_script_component_recovered");
            Require(Mathf.Abs(script.AuthoredThreshold-8.75f)<.0001f &&
                script.PrivateSafetyLabel=="variant private threshold overrides base" &&
                Mathf.Abs(script.speedLimit-6.5f)<.0001f,
                "real_nested_serialized_original_variant_overrides_loaded_correctly");
        }
        finally{if(actual!=null)PrefabUtility.UnloadPrefabContents(actual);}
        var native=HprPrefabStateScan.Scan(originals);
        Require(!native.incomplete && native.schema==2 && native.inputs.Length==3 &&
            native.unsupportedComponents>=3 && native.valuesCaptured>20 &&
            native.dependencies.Any(x=>x.path==Root+
                "/Scripts/HprNestedCustomSample.cs") &&
            native.dependencies.Any(x=>x.path==Base) == false,
            "native_original_unsupported_script_and_referenced_CSharp_source_are_explicit");
        Require(native.values.Any(v=>v.key.EndsWith("/coverage") &&
            v.value=="COMPONENT_TYPE_RECORDED_VALUES_NOT_COVERED"),
            "read_only_scanner_must_not_silently_certify_custom_script_fields");
        var copy=JsonUtility.FromJson<HprPrefabReceipt>(JsonUtility.ToJson(native));
        copy.unityVersion="synthetic-second-Editor-private-negative";
        // Deliberately remove any unknown built-in/package inputs in the PRIVATE
        // synthetic comparator only; the authentic original receipt is retained intact.
        var originalUnverified=native.unverifiedDependencyPaths;
        native.unverifiedDependencyPaths=new string[0];
        copy.unverifiedDependencyPaths=new string[0];
        var simulated=HprPrefabStateCompare.Compare(native,copy);
        native.unverifiedDependencyPaths=originalUnverified;
        Require(simulated.status=="COVERED_VALUES_MATCH_UNINSPECTED_COMPONENTS" &&
            simulated.unsupportedComponents>=6,
            "uninspected_real_custom_script_values_get_cautionary_verdict");
        HprPrefabStateScan.ExportNew(native,output);
        Debug.Log("HPR_NESTED_CUSTOM_NATIVE_BUYER_PASS "+Application.unityVersion+
            " original_prefabs="+native.inputs.Length+
            " verified_dependencies="+native.dependencies.Length+
            " unverified_paths="+native.unverifiedDependencyPaths.Length+
            " custom_uninspected_occurrences="+native.unsupportedComponents+
            " actual_inherited_serialized_threshold="+8.75f);
    }
}
#endif
