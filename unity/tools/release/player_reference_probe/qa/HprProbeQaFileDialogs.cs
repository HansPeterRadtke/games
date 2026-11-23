#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using HPR.PlayerReferenceProbe;

// PRIVATE QA. Observes original UI native file dialogs and real mouse clicks; does not forge UI state.
public static class HprProbeQaFileDialogs
{
    private const string Safe="/data/var/marketplace-account-setup/unity-player-reference-probe-20261123-wave65/";
    private const string Demo="Assets/HPRPlayerReferenceProbe/Demo/Scenes/HPR_Player_Reference_Probe_Demo.unity";
    private static string dir,exportPath,editorPath,playerPath;
    private static HprPlayerReferenceProbeWindow win;
    private static FieldInfo baseline,selectedEditor,selectedPlayer,comparison;
    private static bool inspected,exported,editorSelected,playerSelected;
    private static int loops;

    private static void Require(bool yes,string why)
    {if(!yes)throw new InvalidOperationException("HPR_REAL_FILE_DIALOG_QA_FAILURE:"+why);}
    private static void WriteOnce(string file,string contents)
    {
        using(var s=new FileStream(Path.Combine(dir,file),FileMode.CreateNew,FileAccess.Write,FileShare.None))
        using(var w=new StreamWriter(s))w.WriteLine(contents);
    }
    private static FieldInfo Field(string name)
    {
        var f=typeof(HprPlayerReferenceProbeWindow).GetField(name,
            BindingFlags.NonPublic|BindingFlags.Instance);
        Require(f!=null,"missing_original_native_UI_field_"+name);return f;
    }
    public static void Run()
    {
        dir=Environment.GetEnvironmentVariable("HPR_DIALOG_QA_ROOT")??"";
        exportPath=Environment.GetEnvironmentVariable("HPR_DIALOG_EXPORTED_FILE")??"";
        editorPath=Environment.GetEnvironmentVariable("HPR_DIALOG_BASELINE_FILE")??"";
        playerPath=Environment.GetEnvironmentVariable("HPR_DIALOG_PLAYER_FILE")??"";
        Require(!Application.isBatchMode && dir.StartsWith(Safe,StringComparison.Ordinal) &&
            Path.IsPathRooted(dir) && Directory.Exists(dir) &&
            Path.GetDirectoryName(exportPath)==dir && !File.Exists(exportPath) &&
            File.Exists(editorPath) && File.Exists(playerPath) &&
            !File.Exists(Path.Combine(dir,"ready.txt")),"unique_original_private_file_dialog_test");
        var scene=EditorSceneManager.OpenScene(Demo,OpenSceneMode.Single);
        Require(scene.isLoaded && scene.IsValid() && scene.rootCount==13,
            "real_imported_original_buyer_scene_loaded");
        var probe=scene.GetRootGameObjects().SelectMany(
            g=>g.GetComponentsInChildren<HprPlayerReferenceProbe>(true)).Single();
        Require(probe.checks.Length==2 &&
            probe.checks.All(c=>c.source==null && !string.IsNullOrEmpty(c.resourcesPath)),
            "no_direct_asset_scene_pin");
        Selection.activeGameObject=probe.gameObject;
        baseline=Field("baseline");selectedEditor=Field("baselineFile");
        selectedPlayer=Field("playerFile");comparison=Field("comparison");
        EditorApplication.delayCall+=()=>
        {
            HprPlayerReferenceProbeWindow.Open();
            win=EditorWindow.GetWindow<HprPlayerReferenceProbeWindow>();
            win.minSize=new Vector2(850f,600f);win.position=new Rect(100,65,1020,730);
            Require(baseline.GetValue(win)==null,"native_scan_must_be_genuinely_clicked");
            WriteOnce("ready.txt","REAL_UNITY2022_NATIVE_FILE_DIALOG_UI_READY");
            EditorApplication.update+=Poll;
        };
    }
    private static void Poll()
    {
        if(win==null || loops++>100000){EditorApplication.update-=Poll;return;}
        try
        {
            if(!inspected && baseline.GetValue(win)!=null)
            {
                var r=(HprReferenceReport)baseline.GetValue(win);
                HprReferenceInspector.Validate(r);
                Require(r.origin=="EDITOR" && r.checkedCount==2 && r.assignedCount==1 &&
                    r.missingCount==1 && r.unsupportedCount==0,"native_scan_actual_click_wrong_result");
                inspected=true;WriteOnce("inspected.txt","REAL_INSPECT_BUTTON_CLICK_PASS");
                Debug.Log("HPR_REAL_FILE_DIALOG_INSPECT_CLICK_PASS");
            }
            else if(inspected && !exported && File.Exists(exportPath))
            {
                var r=JsonUtility.FromJson<HprReferenceReport>(File.ReadAllText(exportPath));
                HprReferenceInspector.Validate(r);
                Require(r.unityVersion==Application.unityVersion && r.origin=="EDITOR" &&
                    r.checkedCount==2 && r.assignedCount==1 && r.missingCount==1 &&
                    (string)selectedEditor.GetValue(win)==exportPath,
                    "actual_native_SaveFilePanel_and_original_create_only_export");
                exported=true;WriteOnce("exported.txt","REAL_EXPORT_BUTTON_AND_NATIVE_SAVE_FILE_DIALOG_PASS");
                Debug.Log("HPR_REAL_FILE_DIALOG_EXPORT_PASS");
            }
            else if(exported && !editorSelected &&
                (string)selectedEditor.GetValue(win)==editorPath)
            {
                editorSelected=true;
                WriteOnce("existing-baseline-selected.txt","REAL_NATIVE_OPEN_FILE_DIALOG_EDITOR_REPORT_SELECTED");
                Debug.Log("HPR_REAL_FILE_DIALOG_EDITOR_SELECTED_PASS");
            }
            else if(editorSelected && !playerSelected &&
                (string)selectedPlayer.GetValue(win)==playerPath)
            {
                playerSelected=true;
                WriteOnce("actual-player-selected.txt","REAL_NATIVE_OPEN_FILE_DIALOG_PLAYER_REPORT_SELECTED");
                Debug.Log("HPR_REAL_FILE_DIALOG_PLAYER_SELECTED_PASS");
            }
            else if(playerSelected && comparison.GetValue(win)!=null)
            {
                var r=(HprReferenceComparison)comparison.GetValue(win);
                Require(r.status=="CONSISTENT_NULL_OR_UNSET_FIELDS" &&
                    r.checkedCount==3 && !EditorSceneManager.GetActiveScene().isDirty,
                    "native_real_buyer_compare_and_scene_preservation");
                WriteOnce("comparison-complete.txt",
                    "REAL_BOTH_NATIVE_FILE_CHOOSERS_COMPARE_CLICK_PASS; SCENE_UNMODIFIED=TRUE");
                Debug.Log("HPR_REAL_FILE_DIALOG_COMPLETE_PASS");
                EditorApplication.update-=Poll;
            }
            if(!EditorSceneManager.GetActiveScene().isDirty)
                return;
            throw new InvalidOperationException("buyer_scene_modified_in_readonly_file_dialog_qa");
        }
        catch(Exception error)
        {
            if(!File.Exists(Path.Combine(dir,"error.txt")))WriteOnce("error.txt",error.ToString());
            Debug.LogError(error);EditorApplication.update-=Poll;
        }
    }
}
#endif
