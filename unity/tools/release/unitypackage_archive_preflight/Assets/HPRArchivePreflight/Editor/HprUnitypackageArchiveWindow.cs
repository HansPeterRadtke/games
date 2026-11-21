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
        private HprArchiveCoexistencePreview coexistencePreview;
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
            GUILayout.Label("BEFORE IMPORT — PACKAGE UPGRADE & COEXISTENCE PREFLIGHT", EditorStyles.boldLabel);
            EditorGUILayout.HelpBox("Choose two local .unitypackage archives, then select Upgrade " +
                "(one version replaces another) or Coexistence (two independent packages installed together). " +
                "Both scan TAR/GZIP members in memory; no Unity import, " +
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
            if (GUILayout.Button("Try coexistence: competing packages use the same path", GUILayout.Height(30)))
                TryCoexistenceExample();
            GUILayout.Space(8);
            EditorGUILayout.BeginHorizontal();
            if (GUILayout.Button("Choose existing package", GUILayout.Width(215), GUILayout.Height(31)))
            {
                string selected = EditorUtility.OpenFilePanel("Existing Unitypackage", "", "unitypackage");
                if (!string.IsNullOrEmpty(selected)) { previousPath = selected; preview = null; coexistencePreview = null; }
            }
            EditorGUILayout.SelectableLabel(string.IsNullOrEmpty(previousPath) ? "No existing archive selected" :
                previousPath, GUILayout.Height(38));
            EditorGUILayout.EndHorizontal();
            EditorGUILayout.BeginHorizontal();
            if (GUILayout.Button("Choose updated package", GUILayout.Width(215), GUILayout.Height(31)))
            {
                string selected = EditorUtility.OpenFilePanel("Proposed Unitypackage", "", "unitypackage");
                if (!string.IsNullOrEmpty(selected)) { updatedPath = selected; preview = null; coexistencePreview = null; }
            }
            EditorGUILayout.SelectableLabel(string.IsNullOrEmpty(updatedPath) ? "No updated archive selected" :
                updatedPath, GUILayout.Height(38));
            EditorGUILayout.EndHorizontal();
            EditorGUI.BeginDisabledGroup(string.IsNullOrEmpty(previousPath) || string.IsNullOrEmpty(updatedPath));
            if (GUILayout.Button("Review an UPGRADE (old replaced by new)", GUILayout.Height(36)))
                BeginScan(false);
            if (GUILayout.Button("Check COEXISTENCE (both packages together)", GUILayout.Height(36)))
                BeginScan(true);
            EditorGUI.EndDisabledGroup();
            EditorGUI.EndDisabledGroup();
            if (scanning) EditorGUILayout.HelpBox("Inspecting package archives. Cancel via the Unity progress panel.", MessageType.Warning);
            EditorGUILayout.HelpBox(notice, (preview != null && preview.incomplete) ||
                (coexistencePreview != null && coexistencePreview.incomplete) ?
                MessageType.Error : MessageType.None);
            if (coexistencePreview != null) { DrawCoexistence(); return; }
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

        private void DrawCoexistence()
        {
            GUILayout.Label("INDEPENDENT-PACKAGE COEXISTENCE — " + coexistencePreview.status,
                EditorStyles.boldLabel);
            GUILayout.Label("First archive: " + coexistencePreview.firstArchiveAssets +
                " assets | Second: " + coexistencePreview.secondArchiveAssets +
                " | GUID collisions: " + coexistencePreview.guidCollisions +
                " | Path collisions: " + coexistencePreview.pathCollisions +
                " | Case-only path collisions: " + coexistencePreview.caseOnlyPathCollisions);
            GUILayout.Label("Shared identity with different source/settings: " +
                coexistencePreview.overwriteRisks + " | Exactly shared assets: " +
                coexistencePreview.identicalSharedAssets);
            if (coexistencePreview.incomplete)
                EditorGUILayout.HelpBox("INCOMPLETE — do not infer that simultaneous installation is safe.",
                    MessageType.Error);
            EditorGUI.BeginDisabledGroup(scanning);
            if (GUILayout.Button("Export coexistence review to a NEW JSON file"))
            {
                string destination = EditorUtility.SaveFilePanel("Save independent package coexistence preview", "",
                    "unitypackage-coexistence-review.json", "json");
                if (!string.IsNullOrEmpty(destination))
                {
                    try { HprArchiveCoexistence.ExportNew(coexistencePreview, destination);
                        notice = "New coexistence report saved."; }
                    catch (Exception e) { notice = "Report not written: " + e.Message; }
                }
            }
            EditorGUI.EndDisabledGroup();
            scroll = EditorGUILayout.BeginScrollView(scroll);
            if (previous != null && previous.status == "INCOMPLETE")
                EditorGUILayout.HelpBox("First archive incomplete: " + previous.reason, MessageType.Error);
            if (updated != null && updated.status == "INCOMPLETE")
                EditorGUILayout.HelpBox("Second archive incomplete: " + updated.reason, MessageType.Error);
            foreach (var finding in coexistencePreview.findings ?? new HprArchiveDifference[0])
            {
                GUILayout.Label(finding.kind, EditorStyles.boldLabel);
                EditorGUILayout.LabelField("First: " + finding.before, EditorStyles.wordWrappedLabel);
                EditorGUILayout.LabelField("Second: " + finding.after, EditorStyles.wordWrappedLabel);
                EditorGUILayout.LabelField(finding.guidance, EditorStyles.wordWrappedLabel);
                GUILayout.Space(7);
            }
            EditorGUILayout.HelpBox(coexistencePreview.limitation, MessageType.Warning);
            EditorGUILayout.EndScrollView();
        }

        private void TryCoexistenceExample()
        {
            const string root = "Assets/HPRArchivePreflight/Samples";
            string projectRoot = Directory.GetParent(Application.dataPath).FullName;
            string source = Path.Combine(projectRoot, root, "HprExample-baseline.unitypackage");
            string competing = Path.Combine(projectRoot, root, "HprExample-changed_guid.unitypackage");
            if (!File.Exists(source) || !File.Exists(competing))
            {
                preview = null; coexistencePreview = null;
                notice = "Original examples missing. Re-import the complete package or select two archives.";
                return;
            }
            previousPath = source;
            updatedPath = competing;
            BeginScan(true);
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
                preview = null; coexistencePreview = null;
                notice = "The original example archives are missing. Re-import the complete " +
                    "package or choose two existing local .unitypackage files yourself.";
                return;
            }
            previousPath = source;
            updatedPath = proposed;
            BeginScan(false);
        }

        private void BeginScan(bool checkIndependentPackageCoexistence)
        {
            if (scanning) return;
            scanning = true;
            preview = null; coexistencePreview = null;
            notice = checkIndependentPackageCoexistence ?
                "Checking two independent packages for collisions without importing." :
                "Scanning old and new archives. The progress panel supports cancellation.";
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
                    if (checkIndependentPackageCoexistence)
                    {
                        coexistencePreview = HprArchiveCoexistence.Compare(previous, updated);
                        notice = coexistencePreview.incomplete ?
                            "Cannot evaluate two independent packages: invalid, incomplete or canceled input." :
                            "Coexistence preview complete. Test the two packages together in a disposable project.";
                    }
                    else
                    {
                        preview = HprUnitypackageArchiveReader.Compare(previous, updated);
                        notice = preview.incomplete ? "Cannot approve: incomplete/malformed archive or canceled scan." :
                            "Upgrade preview finished. Test actual customer project references.";
                    }
                }
                catch (Exception e) { preview = null; coexistencePreview = null;
                    notice = "Scan stopped: " + e.Message; }
                finally { EditorUtility.ClearProgressBar(); scanning = false; if (this != null) Repaint(); }
            };
        }
    }
}
#endif
