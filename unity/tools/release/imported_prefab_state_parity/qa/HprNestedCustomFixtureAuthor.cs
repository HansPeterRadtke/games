#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using HPR.NestedCustomFixture;

// PRIVATE first-party nested/variant fixture author. Operates solely in a disposable project.
public static class HprNestedCustomFixtureAuthor
{
    public const string Root="Assets/HPRNestedCustomAcceptance";
    public const string Base=Root+"/Prefabs/OriginalMachine.prefab";
    public const string Variant=Root+"/Prefabs/OriginalMachineVariant.prefab";
    public const string Nested=Root+"/Prefabs/OriginalMachineAssembly.prefab";
    private static void Require(bool yes,string why)
    {if(!yes)throw new InvalidOperationException("HPR_NESTED_FIXTURE_AUTHOR_FAIL:"+why);}

    public static void Run()
    {
        const string allowed="/data/var/marketplace-account-setup/unity-nested-custom-20261123-wave62/";
        string output=Environment.GetEnvironmentVariable("HPR_NESTED_FIXTURE_PACKAGE")??"";
        Require(Application.isBatchMode && Path.IsPathRooted(output) &&
            output.StartsWith(allowed,StringComparison.Ordinal) && !File.Exists(output),
            "original_private_disposable_create_only_archive");
        Require(AssetDatabase.IsValidFolder(Root) &&
            AssetDatabase.IsValidFolder(Root+"/Prefabs") &&
            AssetDatabase.IsValidFolder(Root+"/Scripts") &&
            AssetDatabase.LoadAssetAtPath<MonoScript>(Root+"/Scripts/HprNestedCustomSample.cs")!=null,
            "first_party_original_custom_script_imported");
        Require(!new[]{Base,Variant,Nested}.Any(p=>File.Exists(p)),
            "no_replayed_fixture_source_save");

        var machine=new GameObject("OriginalMachine");
        var sample=machine.AddComponent<HprNestedCustomSample>();
        sample.speedLimit=2.5f;
        var sensor=new GameObject("OriginalSensor");sensor.transform.SetParent(machine.transform,false);
        sensor.transform.localPosition=new Vector3(0f,1.5f,0f);
        var saved=PrefabUtility.SaveAsPrefabAsset(machine,Base);
        Require(saved!=null,"base_prefab_created");
        UnityEngine.Object.DestroyImmediate(machine);
        Require(PrefabUtility.GetPrefabAssetType(saved)==PrefabAssetType.Regular,"real_regular_base");

        var variant=(GameObject)PrefabUtility.InstantiatePrefab(saved);
        Require(variant!=null && PrefabUtility.IsAnyPrefabInstanceRoot(variant),"genuine_prefab_instance_before_variant_save");
        var variantScript=variant.GetComponent<HprNestedCustomSample>();
        Require(variantScript!=null,"custom_script_present_on_instance");
        variantScript.SetForVariant(8.75f,"variant private threshold overrides base");
        PrefabUtility.RecordPrefabInstancePropertyModifications(variantScript);
        variantScript.speedLimit=6.5f;
        PrefabUtility.RecordPrefabInstancePropertyModifications(variantScript);
        variant.transform.localScale=new Vector3(1.4f,1.1f,1f);
        PrefabUtility.RecordPrefabInstancePropertyModifications(variant.transform);
        var asVariant=PrefabUtility.SaveAsPrefabAsset(variant,Variant);
        Require(asVariant!=null,"variant_prefab_saved");
        UnityEngine.Object.DestroyImmediate(variant);
        Require(PrefabUtility.GetPrefabAssetType(asVariant)==PrefabAssetType.Variant,
            "saved_variant_is_actual_Unity_PrefabVariant");

        var assembly=new GameObject("OriginalMachineAssembly");
        var nested=(GameObject)PrefabUtility.InstantiatePrefab(asVariant);
        Require(nested!=null,"variant_nested_instance_created");
        nested.transform.SetParent(assembly.transform,false);
        nested.transform.localPosition=new Vector3(0f,0f,2f);
        PrefabUtility.RecordPrefabInstancePropertyModifications(nested.transform);
        var savedAssembly=PrefabUtility.SaveAsPrefabAsset(assembly,Nested);
        Require(savedAssembly!=null,"nested_prefab_saved");
        UnityEngine.Object.DestroyImmediate(assembly);
        Require(PrefabUtility.GetPrefabAssetType(savedAssembly)==PrefabAssetType.Regular,
            "outer_nesting_is_normal_prefab_asset");
        Require(AssetDatabase.GetDependencies(Nested,true).Contains(Variant),
            "nested_variant_link_is_stable_AssetDatabase_dependency");
        Require(AssetDatabase.GetDependencies(Variant,true).Contains(Base),
            "variant_original_base_dependency_is_retained");
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
        AssetDatabase.ExportPackage(new[]{Root},output,ExportPackageOptions.Recurse);
        Require(File.Exists(output) && new FileInfo(output).Length>500,
            "real_first_party_variant_and_nested_original_unitypackage_exported");
        Debug.Log("HPR_NESTED_CUSTOM_FIXTURE_AUTHOR_PASS original_base_variant_nested_and_script="+
            "4 exported_bytes="+new FileInfo(output).Length);
    }
}
#endif
