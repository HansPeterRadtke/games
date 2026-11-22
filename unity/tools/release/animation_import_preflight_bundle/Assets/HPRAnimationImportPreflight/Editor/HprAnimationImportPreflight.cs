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
            scroll=EditorGUILayout.BeginScrollView(scroll);
            if(report.clipIdentities!=null)
                EditorGUILayout.LabelField("Local-ID check: "+report.clipIdentities.status,
                    EditorStyles.wordWrappedLabel);
            if(report.sourceTakes!=null)
                EditorGUILayout.LabelField("Source take coverage: "+report.sourceTakes.status,
                    EditorStyles.wordWrappedLabel);
            EditorGUILayout.HelpBox(report.limitation,MessageType.Warning);
            EditorGUILayout.EndScrollView();
        }
    }
}
#endif
