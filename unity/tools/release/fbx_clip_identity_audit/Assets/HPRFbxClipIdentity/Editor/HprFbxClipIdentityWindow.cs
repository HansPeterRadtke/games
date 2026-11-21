#if UNITY_EDITOR
using System;
using UnityEditor;
using UnityEngine;

namespace HPR.FbxClipIdentity
{
    /// <summary>One-click, read-only FBX animation importer local-ID diagnostic.</summary>
    public sealed class HprFbxClipIdentityWindow : EditorWindow
    {
        private FbxClipIdentityReport report;
        private UnityEngine.Object chosenModel;
        private Vector2 scroll;
        private string notice = "Scan your project's FBX animation clip identities.";
        private bool busy;

        [MenuItem("Tools/HPR/FBX Clip Identity Audit")]
        public static void Open()
        {
            var w = GetWindow<HprFbxClipIdentityWindow>("HPR FBX Clip IDs");
            w.minSize = new Vector2(660f, 390f);
            w.Show();
        }

        private void OnGUI()
        {
            GUILayout.Label("FBX ANIMATION CLIP IDENTITY", EditorStyles.boldLabel);
            EditorGUILayout.HelpBox("Read-only check for duplicated AnimationClip local IDs in imported " +
                "FBX ModelImporter metadata. Does not repair or modify files. " +
                "No findings does not prove clips or future reimports are safe.", MessageType.Info);
            EditorGUI.BeginDisabledGroup(busy);
            EditorGUILayout.Space(5f);
            GUILayout.Label("QUICK CHECK", EditorStyles.boldLabel);
            chosenModel = EditorGUILayout.ObjectField("Selected model asset", chosenModel,
                typeof(UnityEngine.Object), false);
            EditorGUILayout.BeginHorizontal();
            if (GUILayout.Button("Check included animated FBX", GUILayout.Height(30)))
            {
                report = HprFbxClipIdentityAudit.ScanSingle(HprFbxClipIdentityAudit.ExampleFbxPath);
                notice = "Included original animation inspected. This example contains no deliberate ID collision.";
            }
            string chosenPath = AssetDatabase.GetAssetPath(chosenModel);
            EditorGUI.BeginDisabledGroup(string.IsNullOrEmpty(chosenPath) ||
                !chosenPath.EndsWith(".fbx", StringComparison.OrdinalIgnoreCase));
            if (GUILayout.Button("Check selected FBX", GUILayout.Height(30)))
            {
                report = HprFbxClipIdentityAudit.ScanSingle(chosenPath);
                notice = report.incomplete ? "Selected model scan incomplete; review the findings." :
                    "Selected model checked without changing source or importer settings.";
            }
            EditorGUI.EndDisabledGroup();
            EditorGUILayout.EndHorizontal();
            EditorGUILayout.Space(4f);
            GUILayout.Label("PROJECT-WIDE CHECK", EditorStyles.boldLabel);
            if (GUILayout.Button("Scan all FBX models (read only)", GUILayout.Height(34)))
            {
                busy = true; report = null; notice = "Scanning. Use the Unity Editor progress dialog to cancel."; Repaint();
                EditorApplication.delayCall += () =>
                {
                    try
                    {
                        if (this == null) return;
                        report = HprFbxClipIdentityAudit.ScanAssets((done, total) =>
                            EditorUtility.DisplayCancelableProgressBar("HPR FBX Clip Identity", "Scanning model " +
                                (done + 1) + " of " + total, total < 1 ? 0f : (float)done / total));
                        notice = report.incomplete ? "Scan incomplete: cancellation, missing metadata, or limit." :
                            "Scan completed. Inspect findings and their source models.";
                    }
                    catch (Exception ex) { report = null; notice = "Scan failed: " + ex.Message; }
                    finally { EditorUtility.ClearProgressBar(); busy = false; if (this != null) Repaint(); }
                };
            }
            EditorGUI.EndDisabledGroup();
            EditorGUILayout.HelpBox(notice, MessageType.None);
            if (report == null) return;
            GUILayout.Label("Status: " + report.status, EditorStyles.boldLabel);
            GUILayout.Label("FBX models checked: " + report.modelsChecked +
                " | duplicated models: " + report.duplicateModels +
                " | repeated IDs: " + report.definiteDuplicateIds);
            if (report.incomplete)
                EditorGUILayout.HelpBox("INCOMPLETE: never use this report as a release pass.", MessageType.Error);
            else if (report.modelsChecked == 0)
                EditorGUILayout.HelpBox("No FBX models under Assets were scanned. This is not a verified clean project.",
                    MessageType.Warning);
            else if (report.status == "NO_ANIMATION_CLIPS_IN_CHECKED_MODELS")
                EditorGUILayout.HelpBox("No animation clips were imported in the checked model(s). " +
                    "There are no animation IDs to validate in this selection.", MessageType.Warning);
            if (GUILayout.Button("Export JSON as NEW file"))
            {
                string dest = EditorUtility.SaveFilePanel("Save FBX local-ID audit", "", "fbx-clip-ids.json", "json");
                if (!string.IsNullOrEmpty(dest))
                {
                    try { HprFbxClipIdentityAudit.ExportNew(report, dest); notice = "New report created."; }
                    catch (Exception ex) { notice = "Report not saved: " + ex.Message; }
                }
            }
            scroll = EditorGUILayout.BeginScrollView(scroll);
            foreach (var model in report.models)
            {
                if (model.incomplete || model.duplicateClipIds > 0)
                {
                    EditorGUILayout.LabelField(model.status + " — " + model.path, EditorStyles.boldLabel);
                    foreach (var finding in model.findings)
                    {
                        EditorGUILayout.LabelField(finding.rule, EditorStyles.wordWrappedLabel);
                        EditorGUILayout.LabelField(finding.detail, EditorStyles.wordWrappedLabel);
                    }
                    GUILayout.Space(6);
                }
            }
            EditorGUILayout.HelpBox(report.limitation, MessageType.Warning);
            EditorGUILayout.EndScrollView();
        }
    }
}
#endif
