#if UNITY_EDITOR
using System;
using UnityEditor;
using UnityEngine;
namespace HPR.FbxSourceTakeVisibility
{
    /// <summary>Read-only source take mismatch preview for modified FBX clip lists.</summary>
    public sealed class HprFbxSourceTakeWindow : EditorWindow
    {
        private UnityEngine.Object model;
        private SourceTakeScanReport report;
        private Vector2 scroll;
        private bool working;
        private string notice = "Select an FBX or try the included original Blender two-take example.";

        [MenuItem("Tools/HPR/FBX Source Take Visibility")]
        public static void Open()
        {
            var w = GetWindow<HprFbxSourceTakeWindow>("HPR FBX Source Takes");
            w.minSize = new Vector2(670f,440f);
            w.Show();
        }
        private void OnGUI()
        {
            GUILayout.Label("FBX SOURCE TAKE VISIBILITY — READ ONLY", EditorStyles.boldLabel);
            EditorGUILayout.HelpBox("Unity can stop importing new source animations when clip definitions " +
                "were manually customized. Compare current source take names to the saved custom clip list. " +
                "This does not add takes or modify imported files.", MessageType.Info);
            EditorGUI.BeginDisabledGroup(working);
            if (GUILayout.Button("Inspect included original two-take example", GUILayout.Height(30)))
            {
                report = HprFbxSourceTakeAudit.ScanSingle(HprFbxSourceTakeAudit.ExampleFbxPath);
                notice = "First-party sample checked, not your project's models. It has no intentional missing take.";
            }
            if (GUILayout.Button("Inspect sample with a deliberately omitted source take", GUILayout.Height(30)))
            {
                report = HprFbxSourceTakeAudit.ScanSingle(HprFbxSourceTakeAudit.ExampleOmittedTakeFbxPath);
                notice = "Included original negative example: intentionally configured with only one " +
                    "of two Blender source actions. This is not a defect in your project.";
            }
            model = EditorGUILayout.ObjectField("Selected FBX model",model,typeof(UnityEngine.Object),false);
            string selected = AssetDatabase.GetAssetPath(model);
            EditorGUI.BeginDisabledGroup(string.IsNullOrEmpty(selected) ||
                !selected.EndsWith(".fbx",StringComparison.OrdinalIgnoreCase));
            if (GUILayout.Button("Inspect selected model without changes",GUILayout.Height(32)))
            {
                report = HprFbxSourceTakeAudit.ScanSingle(selected);
                notice = "Selected model checked, no importer settings changed.";
            }
            EditorGUI.EndDisabledGroup();
            if (GUILayout.Button("Scan all customer FBX models (cancelable)",GUILayout.Height(32)))
            {
                working=true;report=null;notice="Scanning actual customer FBX models...";Repaint();
                EditorApplication.delayCall += () =>
                {
                    try
                    {
                        if(this==null)return;
                        report=HprFbxSourceTakeAudit.ScanAssets((i,n) =>
                            EditorUtility.DisplayCancelableProgressBar("HPR Source Take Visibility",
                                "Checking model " +(i+1)+" of "+n,n>0?(float)i/n:0f));
                        notice=report.incomplete ? "INCOMPLETE: scan canceled, truncated or unsupported." :
                            "Project scan complete. Review statuses before editing your import settings.";
                    }
                    catch(Exception ex){ report=null;notice="Scan stopped: "+ex.Message; }
                    finally{EditorUtility.ClearProgressBar();working=false;if(this!=null)Repaint();}
                };
            }
            EditorGUI.EndDisabledGroup();
            EditorGUILayout.HelpBox(notice,report!=null && report.incomplete ? MessageType.Error : MessageType.None);
            if(report==null)return;
            GUILayout.Label("Status: "+report.status,EditorStyles.boldLabel);
            GUILayout.Label("Models checked: "+report.modelsChecked+
                "   |   Models with possibly hidden source takes: "+report.modelsWithMissingSourceTakes+
                "   |   Source takes not listed: "+report.sourceTakesMissing);
            if(report.incomplete)
                EditorGUILayout.HelpBox("Incomplete report. Do not treat as a pass.",MessageType.Error);
            else if(report.sourceTakesMissing>0)
                EditorGUILayout.HelpBox("First check Unity's built-in Import Unreferenced Takes " +
                    "option if your Editor provides it. Otherwise open this FBX's Animation tab, " +
                    "click + and select the missing Source Take. This diagnostic never modifies " +
                    "your model or imported clip list.",MessageType.Warning);
            else if(report.modelsChecked==0)
                EditorGUILayout.HelpBox("No customer FBX models scanned. The bundled sample is excluded.",MessageType.Warning);
            if(GUILayout.Button("Export JSON into a NEW report file"))
            {
                string path=EditorUtility.SaveFilePanel("Save source take visibility report","","fbx-source-take-visibility.json","json");
                if(!string.IsNullOrEmpty(path))
                {
                    try{HprFbxSourceTakeAudit.ExportNew(report,path);notice="New JSON report written.";}
                    catch(Exception ex){notice="No report overwritten: "+ex.Message;}
                }
            }
            scroll=EditorGUILayout.BeginScrollView(scroll);
            foreach(var entry in report.models)
            {
                EditorGUILayout.LabelField(entry.assetPath+" — "+entry.status,EditorStyles.boldLabel);
                EditorGUILayout.LabelField(entry.detail,EditorStyles.wordWrappedLabel);
                if(entry.missingSourceTakes!=null && entry.missingSourceTakes.Length>0)
                    EditorGUILayout.LabelField("Potential missing take names: "+
                        string.Join(", ",entry.missingSourceTakes),EditorStyles.wordWrappedLabel);
                GUILayout.Space(10f);
            }
            EditorGUILayout.HelpBox(report.limitation,MessageType.Warning);
            EditorGUILayout.EndScrollView();
        }
    }
}
#endif
