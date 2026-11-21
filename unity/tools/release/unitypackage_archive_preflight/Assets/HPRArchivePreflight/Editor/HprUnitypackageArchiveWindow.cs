#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace HPR.ArchivePreflight
{
    /// <summary>Read-only two-file pre-import comparison. No AssetDatabase import.</summary>
    public sealed class HprUnitypackageArchiveWindow : EditorWindow
    {
        private string previousPath = "";
        private string updatedPath = "";
        private string notice = "Choose existing and proposed .unitypackage files. Nothing is imported.";
        private HprArchiveUpgradePreview preview;
        private HprArchiveInspection previous;
        private HprArchiveInspection updated;
        private Vector2 scroll;
        private bool scanning;

        [MenuItem("Tools/HPR/Unitypackage Upgrade Preflight")]
        public static void Open()
        {
            var view = GetWindow<HprUnitypackageArchiveWindow>("Unitypackage Preflight");
            view.minSize = new Vector2(740, 460);
            view.Show();
        }

        private void OnGUI()
        {
            GUILayout.Label("BEFORE IMPORT — PACKAGE UPGRADE PREFLIGHT", EditorStyles.boldLabel);
            EditorGUILayout.HelpBox("Choose two local .unitypackage archives. This scans their TAR/GZIP members " +
                "in memory, compares paths, GUIDs, source bytes and importer settings. No Unity import, " +
                "asset changes, extraction or network requests occur. A clean identity result is NOT proof " +
                "of API, serialized subasset or runtime compatibility.", MessageType.Info);
            EditorGUI.BeginDisabledGroup(scanning);
            GUILayout.Label("TRY ORIGINAL INCLUDED EXAMPLES", EditorStyles.boldLabel);
            EditorGUILayout.HelpBox("The included sample archives were exported by Unity from original " +
                "educational text assets. They demonstrate additions and an intentionally changed " +
                "GUID; they do NOT reproduce a Unity engine defect or approve a real upgrade.", MessageType.Info);
            EditorGUILayout.BeginHorizontal();
            if (GUILayout.Button("Try example: additions only", GUILayout.Height(32)))
                TryIncludedExample(false);
            if (GUILayout.Button("Try example: replaced GUID", GUILayout.Height(32)))
                TryIncludedExample(true);
            EditorGUILayout.EndHorizontal();
            GUILayout.Space(8);
            EditorGUILayout.BeginHorizontal();
            if (GUILayout.Button("Choose existing package", GUILayout.Width(215), GUILayout.Height(31)))
            {
                string selected = EditorUtility.OpenFilePanel("Existing Unitypackage", "", "unitypackage");
                if (!string.IsNullOrEmpty(selected)) { previousPath = selected; preview = null; }
            }
            EditorGUILayout.SelectableLabel(string.IsNullOrEmpty(previousPath) ? "No existing archive selected" :
                previousPath, GUILayout.Height(38));
            EditorGUILayout.EndHorizontal();
            EditorGUILayout.BeginHorizontal();
            if (GUILayout.Button("Choose updated package", GUILayout.Width(215), GUILayout.Height(31)))
            {
                string selected = EditorUtility.OpenFilePanel("Proposed Unitypackage", "", "unitypackage");
                if (!string.IsNullOrEmpty(selected)) { updatedPath = selected; preview = null; }
            }
            EditorGUILayout.SelectableLabel(string.IsNullOrEmpty(updatedPath) ? "No updated archive selected" :
                updatedPath, GUILayout.Height(38));
            EditorGUILayout.EndHorizontal();
            EditorGUI.BeginDisabledGroup(string.IsNullOrEmpty(previousPath) || string.IsNullOrEmpty(updatedPath));
            if (GUILayout.Button("Compare without importing (read only)", GUILayout.Height(38)))
                BeginScan();
            EditorGUI.EndDisabledGroup();
            EditorGUI.EndDisabledGroup();
            if (scanning) EditorGUILayout.HelpBox("Inspecting package archives. Cancel via the Unity progress panel.", MessageType.Warning);
            EditorGUILayout.HelpBox(notice, preview != null && preview.incomplete ? MessageType.Error : MessageType.None);
            if (preview == null) return;
            GUILayout.Label("UPGRADE VERDICT — " + preview.status, EditorStyles.boldLabel);
            GUILayout.Label("Old assets: " + preview.legacyAssets + " | New assets: " + preview.updatedAssets +
                " | Added: " + preview.addedPaths + " | Removed: " + preview.removedPaths +
                " | Replaced GUID: " + preview.replacedGuids);
            GUILayout.Label("Same-GUID source changes: " + preview.sourceChanges +
                " | Import settings changes: " + preview.importerChanges +
                " | Moved paths: " + preview.movedPaths);
            if (preview.incomplete)
                EditorGUILayout.HelpBox("INCOMPLETE — do not use this result to approve installation.", MessageType.Error);
            EditorGUI.BeginDisabledGroup(scanning);
            if (GUILayout.Button("Export result to a NEW JSON file"))
            {
                string destination = EditorUtility.SaveFilePanel("Save upgrade preview (new file)", "",
                    "unitypackage-upgrade-preview.json", "json");
                if (!string.IsNullOrEmpty(destination))
                {
                    try { HprUnitypackageArchiveReader.ExportNew(preview, destination); notice = "New report saved."; }
                    catch (Exception e) { notice = "Report was not written: " + e.Message; }
                }
            }
            EditorGUI.EndDisabledGroup();
            scroll = EditorGUILayout.BeginScrollView(scroll);
            if (previous != null && previous.status == "INCOMPLETE")
                EditorGUILayout.HelpBox("Existing archive invalid: " + previous.reason, MessageType.Error);
            if (updated != null && updated.status == "INCOMPLETE")
                EditorGUILayout.HelpBox("Proposed archive invalid: " + updated.reason, MessageType.Error);
            foreach (var finding in preview.findings ?? new HprArchiveDifference[0])
            {
                GUILayout.Label(finding.kind, EditorStyles.boldLabel);
                EditorGUILayout.LabelField("Before: " + finding.before, EditorStyles.wordWrappedLabel);
                EditorGUILayout.LabelField("After: " + finding.after, EditorStyles.wordWrappedLabel);
                EditorGUILayout.LabelField(finding.guidance, EditorStyles.wordWrappedLabel);
                GUILayout.Space(7);
            }
            EditorGUILayout.HelpBox(preview.limitation, MessageType.Warning);
            EditorGUILayout.EndScrollView();
        }

        private void TryIncludedExample(bool deliberateGuidChange)
        {
            const string root = "Assets/HPRArchivePreflight/Samples";
            string projectRoot = Directory.GetParent(Application.dataPath).FullName;
            string source = Path.Combine(projectRoot, root, "HprExample-baseline.unitypackage");
            string proposed = Path.Combine(projectRoot, root,
                deliberateGuidChange ? "HprExample-changed_guid.unitypackage" :
                    "HprExample-additions_only.unitypackage");
            if (!File.Exists(source) || !File.Exists(proposed))
            {
                preview = null;
                notice = "The original example archives are missing. Re-import the complete " +
                    "package or choose two existing local .unitypackage files yourself.";
                return;
            }
            previousPath = source;
            updatedPath = proposed;
            BeginScan();
        }

        private void BeginScan()
        {
            if (scanning) return;
            scanning = true;
            preview = null;
            notice = "Scanning old and new archives. The progress panel supports cancellation.";
            Repaint();
            string oldFile = previousPath;
            string newFile = updatedPath;
            EditorApplication.delayCall += () =>
            {
                try
                {
                    if (this == null) return;
                    Func<bool> cancelOld = () => EditorUtility.DisplayCancelableProgressBar(
                        "HPR Upgrade Preflight", "Reading existing archive", 0.28f);
                    Func<bool> cancelNew = () => EditorUtility.DisplayCancelableProgressBar(
                        "HPR Upgrade Preflight", "Reading proposed archive", 0.72f);
                    previous = HprUnitypackageArchiveReader.Inspect(oldFile, cancelOld);
                    updated = previous.status == "INCOMPLETE" ? null :
                        HprUnitypackageArchiveReader.Inspect(newFile, cancelNew);
                    preview = HprUnitypackageArchiveReader.Compare(previous, updated);
                    notice = preview.incomplete ? "Cannot approve: incomplete/malformed archive or canceled scan." :
                        "Comparison finished. Review all modifications and test populated buyer projects.";
                }
                catch (Exception e) { preview = null; notice = "Scan stopped: " + e.Message; }
                finally { EditorUtility.ClearProgressBar(); scanning = false; if (this != null) Repaint(); }
            };
        }
    }
}
#endif
