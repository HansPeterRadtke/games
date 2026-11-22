#if UNITY_EDITOR
using System;
using System.IO;
using System.Text;
using UnityEditor;
using UnityEngine;
using HPR.FbxClipIdentity;
using HPR.FbxSourceTakeVisibility;

namespace HPR.AnimationImportPreflight
{
    [Serializable]
    public sealed class HprAnimationImportReport
    {
        public string unityVersion;
        public string status;
        public bool incomplete;
        public int customerModelsChecked;
        public int repeatedClipIds;
        public int unreferencedSourceTakes;
        public FbxClipIdentityReport clipIdentities;
        public SourceTakeScanReport sourceTakes;
        public string limitation;
    }

    /// <summary>
    /// Two independent original first-party FBX importer diagnostics presented
    /// as a single read-only buyer workflow. No auto-fix, reimport, network or
    /// editor setting mutation. Both source scanners must be present.
    /// </summary>
    /// <summary>One matched customer FBX with model-specific, read-only scan evidence.</summary>
    public sealed class HprAnimationImportRow
    {
        public string path;
        public string clipStatus;
        public string sourceTakeStatus;
        public int repeatedClipIds;
        public int missingSourceTakes;
        public string[] missingSourceTakeNames;
        public FbxClipIdentityFinding[] clipFindings;
    }

    public static class HprAnimationImportScan
    {
        private const string Limitations =
            "This preflight checks configured FBX AnimationClip local IDs and source " +
            "take names in importer metadata only. No findings does not prove safe " +
            "animation playback, exact fileID reference consistency, importer " +
            "compatibility, or behavior on future Unity versions. Always validate " +
            "a change in a disposable project before modifying customer files.";

        /// <summary>
        /// The independently developed scanners must inspect the SAME exact
        /// customer FBX paths, not merely coincidentally equal counts. This
        /// is a pure read-only validation; uncertainty produces INCOMPLETE.
        /// </summary>
        public static bool SameCustomerModels(FbxClipIdentityReport ids,
            SourceTakeScanReport takes)
        {
            if(ids == null || takes == null || ids.models == null || takes.models == null ||
                ids.modelsChecked != takes.modelsChecked || ids.models.Length != ids.modelsChecked ||
                takes.models.Length != takes.modelsChecked)
                return false;
            var seen = new System.Collections.Generic.HashSet<string>(StringComparer.OrdinalIgnoreCase);
            for(int i=0;i<ids.modelsChecked;i++)
            {
                var left=ids.models[i];var right=takes.models[i];
                if(left == null || right == null || string.IsNullOrWhiteSpace(left.path) ||
                    string.IsNullOrWhiteSpace(right.assetPath) ||
                    !left.path.StartsWith("Assets/",StringComparison.Ordinal) ||
                    !right.assetPath.StartsWith("Assets/",StringComparison.Ordinal) ||
                    !string.Equals(left.path,right.assetPath,StringComparison.Ordinal) ||
                    !seen.Add(left.path))
                    return false;
            }
            return true;
        }

        public static HprAnimationImportReport ScanProject(Func<string,int,int,bool> canceled = null)
        {
            var output = new HprAnimationImportReport
            { unityVersion = Application.unityVersion, status = "INCOMPLETE", incomplete = true,
              limitation = Limitations };
            var clip = HprFbxClipIdentityAudit.ScanAssets((i,n) =>
                canceled != null && canceled("Clip identity",i,n));
            output.clipIdentities = clip;
            if(clip == null || clip.incomplete)
            {
                output.customerModelsChecked = clip == null ? 0 : clip.modelsChecked;
                return output;
            }
            var takes = HprFbxSourceTakeAudit.ScanAssets((i,n) =>
                canceled != null && canceled("Source takes",i,n));
            output.sourceTakes = takes;
            if(takes == null || takes.incomplete || !SameCustomerModels(clip,takes) ||
                clip.unityVersion != takes.unityVersion)
                return output;
            output.customerModelsChecked = clip.modelsChecked;
            output.repeatedClipIds = clip.definiteDuplicateIds;
            output.unreferencedSourceTakes = takes.sourceTakesMissing;
            output.incomplete = false;
            if(clip.modelsChecked == 0)
                output.status = "NO_CUSTOMER_FBX_MODELS_SCANNED";
            else if(clip.definiteDuplicateIds > 0 || takes.sourceTakesMissing > 0)
                output.status = "POTENTIAL_ANIMATION_IMPORT_ISSUES";
            else if(clip.status == "NO_ANIMATION_CLIPS_IN_CHECKED_MODELS" &&
                takes.status == "NO_ENABLED_SOURCE_ANIMATIONS_CHECKED")
                output.status = "NO_IMPORTABLE_ANIMATION_INSPECTED";
            else
                output.status = "NO_TARGETED_FINDINGS_IN_INSPECTED_MODELS";
            return output;
        }

        /// <summary>
        /// Prepare an issue-first, searchable result list from two aligned scans.
        /// Never combine unmatched/partial reports into a misleading clean result.
        /// This method does not load or change any customer asset.
        /// </summary>
        public static HprAnimationImportRow[] BuildRows(HprAnimationImportReport report,
            bool findingsOnly, string pathFilter)
        {
            if(report == null || report.incomplete || report.clipIdentities == null ||
                report.sourceTakes == null ||
                !SameCustomerModels(report.clipIdentities,report.sourceTakes))
                return new HprAnimationImportRow[0];
            string query = (pathFilter ?? "").Trim();
            var rows = new System.Collections.Generic.List<HprAnimationImportRow>();
            for(int i=0;i<report.clipIdentities.modelsChecked;i++)
            {
                var clip = report.clipIdentities.models[i];
                var takes = report.sourceTakes.models[i];
                if(clip.incomplete || takes.incomplete)
                    return new HprAnimationImportRow[0];
                if(query.Length>0 && clip.path.IndexOf(query,StringComparison.OrdinalIgnoreCase)<0)
                    continue;
                bool hasFinding = clip.duplicateClipIds>0 || takes.missingSourceTakeCount>0;
                if(findingsOnly && !hasFinding) continue;
                rows.Add(new HprAnimationImportRow
                {
                    path=clip.path, clipStatus=clip.status,
                    sourceTakeStatus=takes.status, repeatedClipIds=clip.duplicateClipIds,
                    missingSourceTakes=takes.missingSourceTakeCount,
                    missingSourceTakeNames=takes.missingSourceTakes ?? new string[0],
                    clipFindings=clip.findings ?? new FbxClipIdentityFinding[0]
                });
            }
            return rows.ToArray();
        }

        public static void ExportNew(HprAnimationImportReport report, string absolutePath)
        {
            if(report == null || string.IsNullOrWhiteSpace(absolutePath) ||
                !Path.IsPathRooted(absolutePath))
                throw new ArgumentException("An existing report and absolute new output path are required");
            using(var file = new FileStream(absolutePath,FileMode.CreateNew,FileAccess.Write,FileShare.None))
            using(var writer = new StreamWriter(file,new UTF8Encoding(false)))
                writer.Write(JsonUtility.ToJson(report,true));
        }
    }

    public sealed class HprAnimationImportWindow : EditorWindow
    {
        private bool working;
        private Vector2 scroll;
        private bool findingsOnly = true;
        private string pathFilter = "";
        private HprAnimationImportReport report;
        private string exampleNotice = "";
        private string notice = "Inspect your own FBX models or the bundled first-party examples.";

        [MenuItem("Tools/HPR/Combined Animation Import Audit")]
        public static void Open()
        {
            var window = GetWindow<HprAnimationImportWindow>("Animation Import Audit");
            window.minSize = new Vector2(700f,430f);
            window.Show();
        }
        private void OnGUI()
        {
            GUILayout.Label("FBX ANIMATION IMPORT PREFLIGHT", EditorStyles.boldLabel);
            EditorGUILayout.HelpBox("Two read-only checks in one report: duplicated AnimationClip " +
                "importer IDs and original source takes omitted from customized clip lists. " +
                "No automatic changes to an FBX or Unity project.", MessageType.Info);
            EditorGUI.BeginDisabledGroup(working);
            if(GUILayout.Button("Try included original healthy and warning examples",GUILayout.Height(28)))
            {
                var ids = HprFbxClipIdentityAudit.ScanSingle(HprFbxClipIdentityAudit.ExampleFbxPath);
                var sourceHealthy = HprFbxSourceTakeAudit.ScanSingle(HprFbxSourceTakeAudit.ExampleFbxPath);
                var sourceWarning = HprFbxSourceTakeAudit.ScanSingle(HprFbxSourceTakeAudit.ExampleOmittedTakeFbxPath);
                exampleNotice = "Original clip-ID demo: " + ids.status +
                    "\nOriginal healthy source-take demo: " + sourceHealthy.status +
                    "\nOriginal deliberately omitted source-take demo: " + sourceWarning.status +
                    " (missing " + sourceWarning.sourceTakesMissing + ")";
                notice = "The three examples are not your customer FBX models. " +
                    "Run the project scan separately to inspect your own content.";
            }
            if(GUILayout.Button("Scan all customer FBX models (cancelable)",GUILayout.Height(34)))
            {
                working=true;report=null;notice="Running both original importer checks...";Repaint();
                EditorApplication.delayCall += () =>
                {
                    try
                    {
                        if(this==null) return;
                        report = HprAnimationImportScan.ScanProject((which,i,n) =>
                            EditorUtility.DisplayCancelableProgressBar("HPR Animation Import Preflight",
                              which + " — model "+(i+1)+" of "+n,
                              n>0 ? (float)i/n : 0f));
                        notice = report.incomplete ?
                            "INCOMPLETE. No release verdict; review the model/scan limits." :
                            "Both checks finished without modifying your FBX import settings.";
                    }
                    catch(Exception error) {report=null;notice="Scan stopped: "+error.Message;}
                    finally {EditorUtility.ClearProgressBar();working=false;if(this!=null)Repaint();}
                };
            }
            EditorGUI.EndDisabledGroup();
            EditorGUILayout.HelpBox(notice,report!=null && report.incomplete ? MessageType.Error : MessageType.None);
            if(!string.IsNullOrEmpty(exampleNotice))
                EditorGUILayout.HelpBox(exampleNotice,MessageType.Info);
            if(report==null)return;
            GUILayout.Label("Combined status: "+report.status,EditorStyles.boldLabel);
            GUILayout.Label("Customer FBX models: "+report.customerModelsChecked+
                "  |  Repeated clip IDs: "+report.repeatedClipIds+
                "  |  Unlisted source takes: "+report.unreferencedSourceTakes);
            if(report.incomplete)
                EditorGUILayout.HelpBox("INCOMPLETE. Never treat a partial scan as clean.",MessageType.Error);
            else if(report.customerModelsChecked==0)
                EditorGUILayout.HelpBox("Only bundled examples, or no customer FBX models, were found.",MessageType.Warning);
            else if(report.status=="POTENTIAL_ANIMATION_IMPORT_ISSUES")
                EditorGUILayout.HelpBox("Inspect the separate vendor windows to locate actual affected FBX models. " +
                    "In newer Unity versions, prefer the native Import Unreferenced Takes action for " +
                    "missing source animations. Never edit imported IDs directly.",MessageType.Warning);
            if(GUILayout.Button("Export report into a NEW JSON file"))
            {
                string path = EditorUtility.SaveFilePanel("Save combined FBX import audit", "",
                    "fbx-animation-preflight.json", "json");
                if(!string.IsNullOrEmpty(path))
                {
                    try{HprAnimationImportScan.ExportNew(report,path);notice="New JSON report created.";}
                    catch(Exception ex){notice="No report overwritten: "+ex.Message;}
                }
            }
            if(report.clipIdentities!=null)
                EditorGUILayout.LabelField("Local-ID check: "+report.clipIdentities.status,
                    EditorStyles.wordWrappedLabel);
            if(report.sourceTakes!=null)
                EditorGUILayout.LabelField("Source take coverage: "+report.sourceTakes.status,
                    EditorStyles.wordWrappedLabel);
            if(!report.incomplete)
            {
                findingsOnly = EditorGUILayout.ToggleLeft("Show only FBX models with detected issues",findingsOnly);
                pathFilter = EditorGUILayout.TextField("Find FBX path",pathFilter);
                var rows = HprAnimationImportScan.BuildRows(report,findingsOnly,pathFilter);
                if(rows.Length==0)
                    EditorGUILayout.HelpBox(report.customerModelsChecked==0 ?
                        "No customer FBX models to inspect. The bundled examples are excluded." :
                        "No models match these filters. Turn off 'issues only' to browse every inspected FBX.",
                        MessageType.Info);
                else
                    EditorGUILayout.LabelField("Matching customer FBX models: "+rows.Length,
                        EditorStyles.boldLabel);
                scroll=EditorGUILayout.BeginScrollView(scroll);
                foreach(var row in rows)
                {
                    EditorGUILayout.BeginVertical(EditorStyles.helpBox);
                    EditorGUILayout.BeginHorizontal();
                    GUILayout.Label(row.path,EditorStyles.boldLabel);
                    if(GUILayout.Button("Select FBX",GUILayout.Width(95f)))
                    {
                        var asset=AssetDatabase.LoadMainAssetAtPath(row.path);
                        if(asset==null) notice="The scanned FBX no longer exists at this path. Run another scan.";
                        else { Selection.activeObject=asset; EditorGUIUtility.PingObject(asset); }
                    }
                    EditorGUILayout.EndHorizontal();
                    EditorGUILayout.LabelField("Clip local IDs: "+row.clipStatus+
                        " (repeated "+row.repeatedClipIds+") | Source takes: "+
                        row.sourceTakeStatus+" (unlisted "+row.missingSourceTakes+")",
                        EditorStyles.wordWrappedLabel);
                    if(row.missingSourceTakeNames.Length>0)
                    {
                        int shown=Math.Min(6,row.missingSourceTakeNames.Length);
                        var names=new string[shown];
                        Array.Copy(row.missingSourceTakeNames,names,shown);
                        string extra=row.missingSourceTakeNames.Length>shown ?
                            " (and "+(row.missingSourceTakeNames.Length-shown)+" more in the JSON report)" : "";
                        EditorGUILayout.LabelField("Unlisted source take names: "+
                            string.Join(", ",names)+extra,EditorStyles.wordWrappedLabel);
                    }
                    for(int i=0;i<Math.Min(3,row.clipFindings.Length);i++)
                        EditorGUILayout.LabelField("Local-ID finding: "+row.clipFindings[i].rule+
                            " — "+row.clipFindings[i].detail,EditorStyles.wordWrappedLabel);
                    if(row.clipFindings.Length>3)
                        EditorGUILayout.LabelField("Additional local-ID findings are in the JSON report.",
                            EditorStyles.wordWrappedLabel);
                    EditorGUILayout.EndVertical();
                }
                EditorGUILayout.EndScrollView();
            }
            EditorGUILayout.HelpBox(report.limitation,MessageType.Warning);
        }
    }
}
#endif
