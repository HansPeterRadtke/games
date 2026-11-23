#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace HPR.PlayerReferenceProbe
{
    // Buyer-visible, read-only diagnostics for an explicitly selected opt-in scene probe.
    public sealed class HprPlayerReferenceProbeWindow : EditorWindow
    {
        private HprReferenceReport baseline;
        private HprReferenceComparison comparison;
        private string baselineFile="",playerFile="";
        private string notice="Select a scene GameObject with HprPlayerReferenceProbe to scan selected fields.";
        private Vector2 scroll;

        [MenuItem("Tools/HPR/Player Reference Probe")]
        public static void Open()
        {
            var w=GetWindow<HprPlayerReferenceProbeWindow>("Player Reference Probe");
            w.minSize=new Vector2(720f,460f);w.Show();
        }
        private static HprReferenceReport ReadReport(string absolutePath)
        {
            if(string.IsNullOrEmpty(absolutePath) || !Path.IsPathRooted(absolutePath) ||
                !File.Exists(absolutePath) || new FileInfo(absolutePath).Length>1048576L)
                throw new ArgumentException("Choose an existing bounded original report.");
            var report=JsonUtility.FromJson<HprReferenceReport>(File.ReadAllText(absolutePath));
            HprReferenceInspector.Validate(report);
            return report;
        }
        private static string Label(string file)
        {
            return string.IsNullOrEmpty(file) ? "Not selected" : Path.GetFileName(file);
        }
        private void OnGUI()
        {
            GUILayout.Label("PLAYER REFERENCE PROBE",EditorStyles.boldLabel);
            EditorGUILayout.HelpBox("Inspect selected ScriptableObject prefab fields, then compare " +
                "the Editor result with a real built Player. No assets are changed.",MessageType.Info);
            var selected=Selection.activeGameObject;
            var probe=selected==null ? null : selected.GetComponent<HprPlayerReferenceProbe>();
            EditorGUILayout.LabelField("Selected scene probe: "+
                (probe==null ? "None — add HprPlayerReferenceProbe to a scene object and configure checks" :
                 selected.name+" ("+(probe.checks==null?0:probe.checks.Length)+" checks)"),
                EditorStyles.wordWrappedLabel);
            if(GUILayout.Button("Inspect selected scene probe — read only",GUILayout.Height(30)))
            {
                baseline=null;comparison=null;
                try
                {
                    if(probe==null)throw new ArgumentException("Select a scene GameObject with a configured probe.");
                    baseline=HprReferenceInspector.Inspect(probe.checks,"EDITOR");
                    notice="Editor: "+baseline.assignedCount+" assigned; "+baseline.missingCount+
                        " null or unset; "+baseline.unsupportedCount+" unsupported. " +
                        "Build and run an actual Player separately to compare.";
                }
                catch(Exception ex){notice="Scan incomplete: "+ex.Message;}
            }
            if(baseline!=null && GUILayout.Button("Export NEW Editor baseline JSON"))
            {
                var path=EditorUtility.SaveFilePanel("Create new original Editor baseline","",
                    "hpr-editor-reference-baseline.json","json");
                if(!string.IsNullOrEmpty(path))try
                {
                    HprReferenceInspector.WriteNew(baseline,path);
                    baselineFile=path;notice="Created original Editor baseline; no source assets changed.";
                }
                catch(Exception error){notice="Cannot export: "+error.Message;}
            }
            EditorGUILayout.LabelField("Existing Editor baseline: "+Label(baselineFile),EditorStyles.wordWrappedLabel);
            if(GUILayout.Button("Choose existing Editor baseline"))
            {
                var path=EditorUtility.OpenFilePanel("Editor baseline","","json");
                if(!string.IsNullOrEmpty(path)){baselineFile=path;comparison=null;}
            }
            EditorGUILayout.LabelField("Actual built Player report: "+Label(playerFile),EditorStyles.wordWrappedLabel);
            if(GUILayout.Button("Choose actual built Player JSON report"))
            {
                var path=EditorUtility.OpenFilePanel("Original Player report","","json");
                if(!string.IsNullOrEmpty(path)){playerFile=path;comparison=null;}
            }
            if(GUILayout.Button("Compare Editor and actual Player references",GUILayout.Height(30)))
            {
                comparison=null;
                try
                {
                    comparison=HprReferenceInspector.Compare(ReadReport(baselineFile),ReadReport(playerFile));
                    notice=comparison.status+" — "+comparison.playerMissingCaseIds.Length+
                        " selected fields lost in Player; "+comparison.playerSourceMissingCaseIds.Length+
                        " ScriptableObject sources not loaded; "+comparison.otherDifferences.Length+
                        " other differences. A null field may be intentional.";
                }
                catch(Exception ex){notice="Comparison incomplete: "+ex.Message;}
            }
            scroll=EditorGUILayout.BeginScrollView(scroll,GUILayout.ExpandHeight(true));
            EditorGUILayout.HelpBox(notice,notice.Contains("incomplete") ||
                notice.Contains("REFERENCE_LOSS") || notice.Contains("UNSET") ?
                MessageType.Warning:MessageType.Info);
            if(baseline!=null)
            {
                EditorGUILayout.LabelField("Editor source checks (selected only)",EditorStyles.boldLabel);
                foreach(var v in baseline.cases.Take(24))
                    EditorGUILayout.LabelField(v.id+" / "+v.fieldName+" ("+v.sourceLookup+") — "+v.status,
                        EditorStyles.wordWrappedLabel);
            }
            if(comparison!=null)
            {
                EditorGUILayout.LabelField("Comparison: "+comparison.status,EditorStyles.boldLabel);
                foreach(var id in comparison.playerMissingCaseIds.Take(24))
                    EditorGUILayout.LabelField("Lost in Player: "+id,EditorStyles.wordWrappedLabel);
                foreach(var id in comparison.playerSourceMissingCaseIds.Take(24))
                    EditorGUILayout.LabelField("ScriptableObject not loaded in Player: "+id,
                        EditorStyles.wordWrappedLabel);
                foreach(var id in comparison.otherDifferences.Take(24))
                    EditorGUILayout.LabelField("Review: "+id,EditorStyles.wordWrappedLabel);
            }
            EditorGUILayout.HelpBox("Limited to selected direct, serialized Unity Object fields. " +
                "Null values may be intentional. For Resources assets, prefer path-only checks " +
                "to avoid forcing asset inclusion. See README for full limitations.",MessageType.Info);
            EditorGUILayout.EndScrollView();
        }
    }
}
#endif
