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
            if (GUILayout.Button("Scan FBX models (read only)", GUILayout.Height(36)))
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
