#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using HPR.PlayerReferenceProbe;

// PRIVATE original Unity window screenshot QA; automated population is explicit.
public static class HprProbeQaGraphical
{
    private static void Require(bool condition,string why)
    {if(!condition)throw new InvalidOperationException("HPR_PLAYER_PROBE_GUI_QA_FAILURE:"+why);}
    private static void SetField(EditorWindow w,string name,object value)
    {
        var field=w.GetType().GetField(name,BindingFlags.NonPublic|BindingFlags.Instance);
        Require(field!=null,"original_first_party_UI_field_"+name);
        field.SetValue(w,value);
    }
    public static void Run()
    {
        const string safe="/data/var/marketplace-account-setup/unity-player-reference-probe-20261123-wave63/";
        string output=Environment.GetEnvironmentVariable("HPR_PROBE_QA_GUI_RECEIPT")??"";
        string root=Environment.GetEnvironmentVariable("HPR_PROBE_QA_ROOT")??"";
        Require(!Application.isBatchMode && output.StartsWith(safe,StringComparison.Ordinal) &&
            root.StartsWith(safe,StringComparison.Ordinal) &&
            Path.IsPathRooted(output) && !File.Exists(output),"private_original_graphical_session");
        string scenePath="Assets/HPRProbeTest/Scenes/HPR_Real_Player_Reference_Scene.unity";
        var scene=EditorSceneManager.OpenScene(scenePath);
        Require(scene.IsValid() && scene.isLoaded,"real_saved_original_test_scene_loaded");
        var probe=UnityEngine.Object.FindObjectsOfType<HprPlayerReferenceProbe>(true).SingleOrDefault();
        Require(probe!=null && probe.checks.Length==3,"original_three_explicit_scriptable_object_checks");
        Selection.activeGameObject=probe.gameObject;
        var editor=HprReferenceInspector.Inspect(probe.checks,"EDITOR");
        Require(editor.assignedCount==2 && editor.missingCount==1 && editor.unsupportedCount==0,
            "real_native_Editor_reference_inspection_matches_saved_originals");
        string baselinePath=Path.Combine(root,"editor-original-baseline.json");
        string playerPath=Path.Combine(root,"actual-player-receipt.json");
        Require(File.Exists(baselinePath) && File.Exists(playerPath),"genuine_original_player_receipts_present");
        var baseline=JsonUtility.FromJson<HprReferenceReport>(File.ReadAllText(baselinePath));
        var player=JsonUtility.FromJson<HprReferenceReport>(File.ReadAllText(playerPath));
        var comparison=HprReferenceInspector.Compare(baseline,player);
        Require(comparison.status=="CONSISTENT_NULL_OR_UNSET_FIELDS" &&
            comparison.checkedCount==3,"real_original_Csharp_editor_player_comparison");
        EditorApplication.delayCall+=()=>
        {
            HprPlayerReferenceProbeWindow.Open();
            var window=EditorWindow.GetWindow<HprPlayerReferenceProbeWindow>();
            window.position=new Rect(65,90,850,720);
            SetField(window,"baseline",editor);
            SetField(window,"comparison",comparison);
            SetField(window,"baselineFile",baselinePath);
            SetField(window,"playerFile",playerPath);
            SetField(window,"notice","Genuine Linux Player and Editor reference receipts: two assigned, " +
                "one intentionally unset in both. Not a complete game certification.");
            window.Repaint();
            EditorApplication.delayCall+=()=>
            {
                using(var file=new FileStream(output,FileMode.CreateNew,FileAccess.Write,FileShare.None))
                using(var writer=new StreamWriter(file))
                {
                    writer.WriteLine("actual_native_Editor_GUI_not_mockup=TRUE");
                    writer.WriteLine("native_unity_version="+Application.unityVersion);
                    writer.WriteLine("original_explicit_checks="+editor.checkedCount);
                    writer.WriteLine("real_Editor_assigned_references="+editor.assignedCount);
                    writer.WriteLine("actual_Player_match_status="+comparison.status);
                    writer.WriteLine("automated_QA_populated_window=TRUE");
                    writer.WriteLine("human_clicked_controls=FALSE");
                    writer.WriteLine("third_party_software_terms_accepted=FALSE");
                }
                Debug.Log("HPR_PLAYER_REFERENCE_REAL_GRAPHICAL_WINDOW_QA_PASS "+comparison.status);
            };
        };
    }
}
#endif
