#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using HPR.PlayerReferenceProbe;

// PRIVATE real Unity Editor window acceptance: never shipped in buyer product.
public static class HprProbeQaDemoGraphical
{
    const string Demo="Assets/HPRPlayerReferenceProbe/Demo/Scenes/HPR_Player_Reference_Probe_Demo.unity";
    private static void Require(bool okay,string reason)
    {if(!okay)throw new InvalidOperationException("HPR_REAL_EDITOR_WINDOW_QA_FAIL:"+reason);}
    private static void SetField(HprPlayerReferenceProbeWindow window,string name,object value)
    {
        var field=window.GetType().GetField(name,BindingFlags.Instance|BindingFlags.NonPublic);
        Require(field!=null,"expected_buyer_window_field_"+name);
        field.SetValue(window,value);
    }
    public static void Run()
    {
        const string safe="/data/var/marketplace-account-setup/unity-player-reference-probe-20261123-wave63/";
        var receipt=Environment.GetEnvironmentVariable("HPR_REAL_DEMO_GUI_RECEIPT")??"";
        Require(!Application.isBatchMode && Path.IsPathRooted(receipt) &&
            receipt.StartsWith(safe,StringComparison.Ordinal) && !File.Exists(receipt),
            "original_private_real_graphical_preview_only");
        var scene=EditorSceneManager.OpenScene(Demo,OpenSceneMode.Single);
        Require(scene.isLoaded && scene.rootCount==13,"original_scene_imported_in_true_Editor");
        var probes=scene.GetRootGameObjects()
            .SelectMany(x=>x.GetComponentsInChildren<HprPlayerReferenceProbe>(true)).ToArray();
        Require(probes.Length==1 && probes[0].checks.Length==2,
            "actual_demo_probe_component_selected_unique");
        var probe=probes[0];
        Require(probe.checks.All(c=>c.source==null && !string.IsNullOrEmpty(c.resourcesPath)),
            "source_lookups_not_pinned_by_test");
        var report=HprReferenceInspector.Inspect(probe.checks,"EDITOR");
        HprReferenceInspector.Validate(report);
        Require(report.schema==2 && report.checkedCount==2 && report.assignedCount==1 &&
            report.missingCount==1 && report.unsupportedCount==0,
            "actual_in_Editor_probe_works_before_any_capture");
        Selection.activeGameObject=probe.gameObject;
        EditorApplication.delayCall+=()=>
        {
            HprPlayerReferenceProbeWindow.Open();
            var window=EditorWindow.GetWindow<HprPlayerReferenceProbeWindow>();
            window.minSize=new Vector2(830,580);
            window.position=new Rect(60,60,1000,720);
            SetField(window,"baseline",report);
            SetField(window,"comparison",null);
            SetField(window,"notice","Actual Editor demo: one assigned reference and one intentionally " +
                "empty field. Build and run a Player separately for comparison.");
            window.Repaint();
            EditorApplication.delayCall+=()=>
            {
                using(var writer=new StreamWriter(new FileStream(receipt,FileMode.CreateNew,
                    FileAccess.Write,FileShare.None)))
                {
                    writer.WriteLine("actual_Unity_Editor_GUI_not_mockup=TRUE");
                    writer.WriteLine("unity_version="+Application.unityVersion);
                    writer.WriteLine("source_probe_assigned_count="+report.assignedCount);
                    writer.WriteLine("source_probe_intentionally_null_count="+report.missingCount);
                    writer.WriteLine("source_probes_use_only_Resources_paths=TRUE");
                    writer.WriteLine("automated_qa_populated_window=TRUE");
                    writer.WriteLine("user_clicked_controls_in_this_session=FALSE");
                    writer.WriteLine("editor_software_terms_accepted_in_this_session=FALSE");
                }
                Debug.Log("HPR_ORIGINAL_REAL_EDITOR_PRODUCT_WINDOW_QA_PASS "+Application.unityVersion);
            };
        };
    }
}
#endif
