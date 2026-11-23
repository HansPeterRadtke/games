#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;
using HPR.PlayerReferenceProbe;

// PRIVATE first-party actual Unity2022 Player QA. Never packaged for customers.
public static class HprProbeQa2022ActualPlayer
{
    private static void Check(bool valid,string context)
    {if(!valid)throw new InvalidOperationException("HPR_UNITY2022_NATIVE_PLAYER_QA_FAILURE:"+context);}
    public static void Run()
    {
        const string safe="/data/var/marketplace-account-setup/unity-player-reference-probe-20261123-wave63/";
        var folder=Environment.GetEnvironmentVariable("HPR_UNITY2022_PLAYER_QA")??"";
        Check(Application.isBatchMode && Application.unityVersion=="2022.3.22f1" &&
            Path.IsPathRooted(folder) && folder.StartsWith(safe,StringComparison.Ordinal),
            "expected_firstparty_unity2022_and_private_root");
        string executable=Path.Combine(folder,"PrivateOriginalDemo2022.x86_64");
        string receipt=Path.Combine(folder,"private-Editor2022-baseline.json");
        string clonedScene="Assets/HPRPrivateQa/OriginalDemo2022_Autoexit.unity";
        Check(!File.Exists(executable) && !File.Exists(receipt) &&
              !File.Exists(clonedScene),"create_only_native_build");
        const string sourceScene="Assets/HPRPlayerReferenceProbe/Demo/Scenes/HPR_Player_Reference_Probe_Demo.unity";
        var scene=EditorSceneManager.OpenScene(sourceScene,OpenSceneMode.Single);
        Check(scene.IsValid() && scene.isLoaded && scene.rootCount==13,"unmodified_firstparty_demo_source");
        var probes=scene.GetRootGameObjects().SelectMany(
            go=>go.GetComponentsInChildren<HprPlayerReferenceProbe>(true)).ToArray();
        Check(probes.Length==1 && probes[0].checks.Length==2 &&
            probes[0].checks.All(c=>c.source==null && !string.IsNullOrWhiteSpace(c.resourcesPath)),
            "nonpinning_actual_original_scriptableobject_lookup");
        var baseline=HprReferenceInspector.Inspect(probes[0].checks,"EDITOR");
        Check(baseline.schema==2 && baseline.checkedCount==2 && baseline.assignedCount==1 &&
              baseline.missingCount==1 && baseline.unsupportedCount==0,
              "real_Unity2022_original_demo_editor_values");
        HprReferenceInspector.WriteNew(baseline,receipt);
        Check(AssetDatabase.IsValidFolder("Assets/HPRPrivateQa"),"isolated_QA_scene_folder");
        var stop=new GameObject("HPR_PRIVATE_ONLY_LINUX_PLAYER_AUTOSTOP");
        stop.AddComponent<HprProbeQaAutoExit>();
        Check(EditorSceneManager.SaveScene(scene,clonedScene,true),
              "save_only_a_copy_not_the_original_customer_demo");
        var build=BuildPipeline.BuildPlayer(new BuildPlayerOptions{
            scenes=new[]{clonedScene},locationPathName=executable,
            target=BuildTarget.StandaloneLinux64,options=BuildOptions.Development
        });
        Check(build!=null && build.summary.result==BuildResult.Succeeded &&
              File.Exists(executable),"real_Unity2022_Linux64_player_build");
        Debug.Log("HPR_REAL_UNITY2022_BUILT_PLAYER_PASS exe_bytes="+
             new FileInfo(executable).Length+" original_cases="+baseline.checkedCount);
    }
}
#endif
