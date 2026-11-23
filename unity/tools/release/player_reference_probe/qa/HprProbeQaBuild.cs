#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;
using HPR.PlayerReferenceProbe;

// PRIVATE first-party genuine Editor scene+Linux Player build; executed only in disposable projects.
public static class HprProbeQaBuild
{
    private static void Require(bool good,string why)
    {if(!good)throw new InvalidOperationException("HPR_PROBE_BUILD_QA_FAILURE:"+why);}
    public static void Run()
    {
        const string safe="/data/var/marketplace-account-setup/unity-player-reference-probe-20261123-wave63/";
        var root=Environment.GetEnvironmentVariable("HPR_PROBE_QA_ROOT")??"";
        Require(Application.isBatchMode && Path.IsPathRooted(root) &&
            root.StartsWith(safe,StringComparison.Ordinal),"private_buyer_root");
        var exe=Path.Combine(root,"PlayerSmoke.x86_64");
        var baseline=Path.Combine(root,"editor-original-baseline.json");
        Require(!File.Exists(exe) && !File.Exists(baseline) &&
            !AssetDatabase.IsValidFolder("Assets/HPRProbeTest"),"no_replayed_fixture_or_build");
        AssetDatabase.CreateFolder("Assets","HPRProbeTest");
        AssetDatabase.CreateFolder("Assets/HPRProbeTest","Resources");
        AssetDatabase.CreateFolder("Assets/HPRProbeTest","Scenes");
        var prefabSource=new GameObject("HPR_Original_Private_Prefab");
        var prefab=PrefabUtility.SaveAsPrefabAsset(prefabSource,
            "Assets/HPRProbeTest/Resources/HPR_ProbePrefab.prefab");
        UnityEngine.Object.DestroyImmediate(prefabSource);
        Require(prefab!=null,"real_prefab_saved");

        var good=ScriptableObject.CreateInstance<HprProbeQaItem>();
        good.name="OriginalAssignedItem";good.itemPrefab=prefab;good.SetPrivate(prefab);
        var unset=ScriptableObject.CreateInstance<HprProbeQaItem>();
        unset.name="OriginalEmptyItem";unset.itemPrefab=null;
        AssetDatabase.CreateAsset(good,"Assets/HPRProbeTest/Resources/OriginalAssignedItem.asset");
        AssetDatabase.CreateAsset(unset,"Assets/HPRProbeTest/Resources/OriginalEmptyItem.asset");
        AssetDatabase.SaveAssets();
        Require(AssetDatabase.LoadAssetAtPath<HprProbeQaItem>(
            "Assets/HPRProbeTest/Resources/OriginalAssignedItem.asset").itemPrefab!=null,
            "real_serialized_scriptableobject_prefab_link_saved");
        var scene=EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);
        var node=new GameObject("HPR_Reference_Test_Object");
        var probe=node.AddComponent<HprPlayerReferenceProbe>();
        probe.checks=new[]{
            new HprReferenceCase{id="assigned-prefab",source=good,fieldName="itemPrefab"},
            new HprReferenceCase{id="private-serialized",source=good,fieldName="privatePrefab"},
            new HprReferenceCase{id="intentionally-null",source=unset,fieldName="itemPrefab"}
        };
        probe.writePrivateLocalReport=true;
        node.AddComponent<HprProbeQaAutoExit>();
        bool intentionallyDropInPlayer=
            Environment.GetEnvironmentVariable("HPR_PROBE_QA_PLAYER_DROP")=="1";
        bool lateManualCapture=
            Environment.GetEnvironmentVariable("HPR_PROBE_QA_MANUAL_LATE")=="1";
        if(lateManualCapture && intentionallyDropInPlayer)
            throw new InvalidOperationException("Distinct Player-only QA modes cannot overlap.");
        if(lateManualCapture)
        {
            probe.manualOnly=true; // A normal scene Start must not create a misleading early receipt.
            probe.maxCaptures=1;   // Second actual call verifies the output bound.
            var trigger=node.AddComponent<HprProbeQaManualTrigger>();
            trigger.probe=probe;
            trigger.source=good;
        }
        if(intentionallyDropInPlayer)
        {
            var drop=node.AddComponent<HprProbeQaPlayerOnlyClear>();
            drop.source=good;
        }
        var scenePath="Assets/HPRProbeTest/Scenes/HPR_Real_Player_Reference_Scene.unity";
        Require(EditorSceneManager.SaveScene(scene,scenePath),"private_original_scene_saved");
        AssetDatabase.SaveAssets();
        // Inspect the real original reloaded serialized source, not in-memory
        // ScriptableObject instances that have not completed their asset refresh.
        AssetDatabase.Refresh(ImportAssetOptions.ForceSynchronousImport);
        var realGood=AssetDatabase.LoadAssetAtPath<HprProbeQaItem>(
            "Assets/HPRProbeTest/Resources/OriginalAssignedItem.asset");
        var realUnset=AssetDatabase.LoadAssetAtPath<HprProbeQaItem>(
            "Assets/HPRProbeTest/Resources/OriginalEmptyItem.asset");
        Require(realGood!=null && realUnset!=null && realGood.itemPrefab!=null &&
            realGood.PrivatePrefab!=null,"both_actual_original_saved_prefab_references_reloaded");
        probe.checks[0].source=realGood;
        probe.checks[1].source=realGood;
        probe.checks[2].source=realUnset;
        bool resourcesOnly=Environment.GetEnvironmentVariable("HPR_PROBE_QA_RESOURCES_ONLY")=="1";
        if(resourcesOnly)
        {
            if(intentionallyDropInPlayer)
                throw new InvalidOperationException("Path-only QA must not silently pin source via negative fixture.");
            probe.checks[0].source=null;
            probe.checks[1].source=null;
            probe.checks[2].source=null;
            probe.checks[0].resourcesPath="OriginalAssignedItem";
            probe.checks[1].resourcesPath="OriginalAssignedItem";
            probe.checks[2].resourcesPath="OriginalEmptyItem";
        }
        if(intentionallyDropInPlayer)node.GetComponent<HprProbeQaPlayerOnlyClear>().source=realGood;
        if(lateManualCapture)node.GetComponent<HprProbeQaManualTrigger>().source=realGood;
        Require(EditorSceneManager.SaveScene(scene,scenePath),"persist_reloaded_scene_contract");
        var editor=HprReferenceInspector.Inspect(probe.checks,"EDITOR");
        Debug.Log("HPR_PROBE_QA_RELOADED_EDITOR_FIELDS "+JsonUtility.ToJson(editor));
        Require(editor.status=="NULL_OR_UNSET_SELECTED_REFERENCE" && editor.assignedCount==2 &&
            editor.missingCount==1 && editor.unsupportedCount==0 && editor.checkedCount==3,
            "real_in_editor_ScriptableObject_direct_and_private_serializefield_inspection");
        HprReferenceInspector.WriteNew(editor,baseline);
        Debug.Log("HPR_PLAYER_REFERENCE_EDITOR_BASELINE_NATIVE_PASS "+JsonUtility.ToJson(editor));
        if(Environment.GetEnvironmentVariable("HPR_PROBE_QA_EDITOR_ONLY")=="1")
        {
            Debug.Log("HPR_PROBE_PRIVATE_REAL_EDITOR_ONLY_ACCEPTANCE_PASS "+Application.unityVersion);
            return; // No Player result is implied by this GUI-only buyer fixture.
        }
        var options=new BuildPlayerOptions{
            scenes=new[]{scenePath},locationPathName=exe,
            target=BuildTarget.StandaloneLinux64,options=BuildOptions.Development};
        BuildReport report=BuildPipeline.BuildPlayer(options);
        Require(report!=null && report.summary.result==BuildResult.Succeeded &&
            File.Exists(exe),"real_Linux64_Player_build_completed");
        Debug.Log("HPR_PLAYER_REFERENCE_ACTUAL_LINUX64_BUILT_PASS exe_bytes="+
            new FileInfo(exe).Length+" build_size="+report.summary.totalSize);
    }
}
#endif
