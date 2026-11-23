#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using HPR.PlayerReferenceProbe;

// PRIVATE author-owned UI interaction test only; not part of the buyer package.
// It observes genuine Unity Editor button clicks instead of invoking OnGUI or scan handlers.
public static class HprProbeQaActualClicks
{
    private const string Root="/data/var/marketplace-account-setup/unity-player-reference-probe-20261123-wave65/";
    private const string Demo="Assets/HPRPlayerReferenceProbe/Demo/Scenes/HPR_Player_Reference_Probe_Demo.unity";
    private static HprPlayerReferenceProbeWindow window;
    private static FieldInfo baseline,comparison,editorFile,playerFile;
    private static string dir,sourceBaseline,sourcePlayer;
    private static int count;
    private static bool scanned;

    private static void Require(bool b,string reason)
    {if(!b)throw new InvalidOperationException("HPR_ACTUAL_UI_CLICK_QA_FAILURE:"+reason);}

    private static void CreateReceipt(string name,string value)
    {
        var path=Path.Combine(dir,name);
        using(var file=new FileStream(path,FileMode.CreateNew,FileAccess.Write,FileShare.None))
        using(var writer=new StreamWriter(file))writer.WriteLine(value);
    }
    private static FieldInfo PrivateField(string name)
    {
        var f=typeof(HprPlayerReferenceProbeWindow).GetField(name,
            BindingFlags.Instance|BindingFlags.NonPublic);
        Require(f!=null,"expected_real_UI_state_"+name);return f;
    }
    public static void Run()
    {
        dir=Environment.GetEnvironmentVariable("HPR_ACTUAL_UI_ROOT")??"";
        sourceBaseline=Environment.GetEnvironmentVariable("HPR_ACTUAL_UI_BASELINE")??"";
        sourcePlayer=Environment.GetEnvironmentVariable("HPR_ACTUAL_UI_PLAYER")??"";
        Require(!Application.isBatchMode && Path.IsPathRooted(dir) &&
            dir.StartsWith(Root,StringComparison.Ordinal) && Directory.Exists(dir) &&
            !File.Exists(Path.Combine(dir,"ready.txt")) &&
            File.Exists(sourceBaseline) && File.Exists(sourcePlayer),
            "separate_private_authorized_original_paths");
        var scene=EditorSceneManager.OpenScene(Demo,OpenSceneMode.Single);
        Require(scene.IsValid() && scene.isLoaded,"real_untouched_original_demo_scene_opened");
        var probes=scene.GetRootGameObjects()
            .SelectMany(o=>o.GetComponentsInChildren<HprPlayerReferenceProbe>(true)).ToArray();
        Require(probes.Length==1 && probes[0].checks.Length==2 &&
            probes[0].checks.All(v=>v.source==null && !string.IsNullOrEmpty(v.resourcesPath)),
            "actual_two_unpinned_Resources_demo_cases");
        Selection.activeGameObject=probes[0].gameObject;
        baseline=PrivateField("baseline");comparison=PrivateField("comparison");
        editorFile=PrivateField("baselineFile");playerFile=PrivateField("playerFile");
        EditorApplication.delayCall+=()=>
        {
            HprPlayerReferenceProbeWindow.Open();
            window=EditorWindow.GetWindow<HprPlayerReferenceProbeWindow>();
            window.minSize=new Vector2(850f,600f);
            window.position=new Rect(100,65,1020f,730f);
            Require(baseline.GetValue(window)==null && comparison.GetValue(window)==null,
                "no_reflection_forged_scan_or_comparison");
            CreateReceipt("ready.txt","ACTUAL_REAL_EDITOR_WINDOW_READY; VERSION="+
                Application.unityVersion+"; SCANNED=FALSE; CLICK_REQUIRED=TRUE");
            Debug.Log("HPR_ACTUAL_UI_CLICK_READY_FOR_HUMAN_INPUT_EMULATION");
            EditorApplication.update+=Poll;
        };
    }
    private static void Poll()
    {
        if(window==null){EditorApplication.update-=Poll;return;}
        count++;
        if(count>50000){EditorApplication.update-=Poll;return;}
        try
        {
            if(!scanned && baseline.GetValue(window)!=null)
            {
                var found=(HprReferenceReport)baseline.GetValue(window);
                HprReferenceInspector.Validate(found);
                Require(found.origin=="EDITOR" && found.schema==2 &&
                    found.checkedCount==2 && found.assignedCount==1 &&
                    found.missingCount==1 && found.unsupportedCount==0,
                    "actual_GUI_inspect_button_did_not_produce_expected_original_result");
                Require(!EditorSceneManager.GetActiveScene().isDirty,
                    "real_button_modified_customer_scene_instead_of_read_only");
                scanned=true;
                CreateReceipt("scanned-by-actual-click.txt",
                    "ACTUAL_SCAN_BUTTON_CLICK_PASS; VERSION="+Application.unityVersion+
                    "; CHECKS=2; ASSIGNED=1; INTENTIONALLY_EMPTY=1; SCENE_DIRTY=FALSE");
                Debug.Log("HPR_ACTUAL_UI_INSPECT_BUTTON_CLICK_PASS");
                editorFile.SetValue(window,sourceBaseline);
                playerFile.SetValue(window,sourcePlayer);
                window.Repaint();
            }
            else if(scanned && comparison.GetValue(window)!=null)
            {
                var found=(HprReferenceComparison)comparison.GetValue(window);
                Require(found.status=="CONSISTENT_NULL_OR_UNSET_FIELDS" &&
                    found.checkedCount==3 && found.playerMissingCaseIds.Length==0 &&
                    found.playerSourceMissingCaseIds.Length==0,
                    "real_GUI_comparison_did_not_match_original_independent_Player_data");
                Require(!EditorSceneManager.GetActiveScene().isDirty,
                    "actual_compare_button_modified_buyer_scene");
                CreateReceipt("compared-by-actual-click.txt",
                    "ACTUAL_COMPARE_BUTTON_CLICK_PASS; ORIGINAL_TWO_RECEIPTS=TRUE; " +
                    "STATUS="+found.status+"; SCENE_DIRTY=FALSE");
                Debug.Log("HPR_ACTUAL_UI_COMPARE_BUTTON_CLICK_PASS");
                EditorApplication.update-=Poll;
            }
        }
        catch(Exception ex)
        {
            if(!File.Exists(Path.Combine(dir,"error.txt")))
                CreateReceipt("error.txt",ex.ToString());
            Debug.LogError("HPR_ACTUAL_UI_CLICK_QA_ERROR "+ex);
            EditorApplication.update-=Poll;
        }
    }
}
#endif
