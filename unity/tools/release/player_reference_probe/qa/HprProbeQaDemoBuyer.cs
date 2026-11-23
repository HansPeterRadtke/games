#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;
using HPR.PlayerReferenceProbe;
using HPR.PlayerReferenceProbe.Demo;

// PRIVATE native consumer test; not part of the buyer package.
public static class HprProbeQaDemoBuyer
{
    const string Demo="Assets/HPRPlayerReferenceProbe/Demo/Scenes/HPR_Player_Reference_Probe_Demo.unity";
    const string Root="Assets/HPRPlayerReferenceProbe/Demo/Resources/HPRSample/";
    private static void Require(bool pass,string message)
    {if(!pass)throw new InvalidOperationException("HPR_REAL_DEMO_BUYER_QA_FAILURE:"+message);}
    public static void Run()
    {
        const string safe="/data/var/marketplace-account-setup/unity-player-reference-probe-20261123-wave63/";
        string output=Environment.GetEnvironmentVariable("HPR_DEMO_BUYER_ROOT")??"";
        Require(Application.isBatchMode && Path.IsPathRooted(output) &&
            output.StartsWith(safe,StringComparison.Ordinal),"private_original_test_directory");
        string baseline=Path.Combine(output,"actual-original-demo-editor-baseline.json");
        string exe=Path.Combine(output,"OriginalDemoLinux64.x86_64");
        bool build=Environment.GetEnvironmentVariable("HPR_DEMO_BUYER_BUILD")=="1";
        Require(!File.Exists(baseline) && !File.Exists(exe),"no_replay_or_overwrite_of_any_receipt");

        Require(AssetDatabase.LoadAssetAtPath<SceneAsset>(Demo)!=null,
            "actual_original_unity_demo_scene_imported");
        var assigned=AssetDatabase.LoadAssetAtPath<HprPlayerReferenceDemoItem>(Root+"AssignedItem.asset");
        var empty=AssetDatabase.LoadAssetAtPath<HprPlayerReferenceDemoItem>(Root+"OptionalItem.asset");
        var prefab=AssetDatabase.LoadAssetAtPath<GameObject>(Root+"HPR_Demo_Reference.prefab");
        Require(assigned!=null && empty!=null && prefab!=null &&
            assigned.itemPrefab==prefab && empty.itemPrefab==null,
            "original_serialized_scriptableobject_sample_references");
        var scene=EditorSceneManager.OpenScene(Demo,OpenSceneMode.Single);
        Require(scene.IsValid() && scene.isLoaded && scene.rootCount>5,
            "actual_nonempty_renderable_scene_with_objects");
        var probes=scene.GetRootGameObjects()
            .SelectMany(v=>v.GetComponentsInChildren<HprPlayerReferenceProbe>(true)).ToArray();
        Require(probes.Length==1 && probes[0].checks!=null && probes[0].checks.Length==2,
            "explicit_sample_probe_component_unique");
        var configured=probes[0].checks;
        Require(configured.All(v=>v.source==null) &&
            configured[0].resourcesPath=="HPRSample/AssignedItem" &&
            configured[1].resourcesPath=="HPRSample/OptionalItem" &&
            configured[0].fieldName=="itemPrefab" &&
            configured[1].fieldName=="itemPrefab",
            "sample_resources_lookup_never_pins_original_direct_scriptableobjects");
        var report=HprReferenceInspector.Inspect(configured,"EDITOR");
        HprReferenceInspector.Validate(report);
        Require(report.schema==2 && report.checkedCount==2 &&
            report.assignedCount==1 && report.missingCount==1 &&
            report.unsupportedCount==0 &&
            report.cases[0].referencedName=="HPR_Demo_Reference" &&
            report.cases[1].status=="REFERENCE_NULL_OR_UNSET",
            "read_only_original_customer_editor_path_only_reference_probe");
        Require(scene.GetRootGameObjects().Any(v=>v.GetComponent<Camera>()!=null) &&
            scene.GetRootGameObjects().Any(v=>v.GetComponent<Light>()!=null),
            "real_visible_scene_camera_and_light_exist");
        var labels=scene.GetRootGameObjects()
            .SelectMany(go=>go.GetComponentsInChildren<TextMesh>(true)).ToArray();
        Require(labels.Length==5 && labels.Count(x=>x.text=="ASSIGNED")==1 &&
            labels.Count(x=>x.text=="EMPTY")==1,
            "actual_short_distinct_status_labels_in_native_renderable_scene");
        HprReferenceInspector.WriteNew(report,baseline);
        Debug.Log("HPR_PLAYER_REFERENCE_ORIGINAL_DEMO_BUYER_NATIVE_PASS version="+
            Application.unityVersion+" root_objects="+scene.rootCount+
            " assigned="+report.assignedCount+" intentionally_null="+report.missingCount);
        if(!build)return;
        bool releaseScreenshot=Environment.GetEnvironmentVariable("HPR_DEMO_RELEASE_PLAYER")=="1";
        var reportBuild=BuildPipeline.BuildPlayer(new BuildPlayerOptions{
            scenes=new[]{Demo},locationPathName=exe,
            target=BuildTarget.StandaloneLinux64,
            options=releaseScreenshot ? BuildOptions.None : BuildOptions.Development});
        Require(reportBuild!=null && reportBuild.summary.result==BuildResult.Succeeded &&
            File.Exists(exe),"actual_original_sample_scene_built_into_real_Linux64_Player");
        Debug.Log("HPR_PLAYER_REFERENCE_ORIGINAL_DEMO_ACTUAL_LINUX_PLAYER_BUILD_PASS mode="+
            (releaseScreenshot ? "RELEASE" : "DEVELOPMENT")+" bytes="+new FileInfo(exe).Length);
    }
}
#endif
