#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEngine;

namespace HPR.PackageBoundary
{
    [Serializable]
    public sealed class BoundaryFinding
    {
        public string category;
        public string asset;
        public string dependency;
        public string action;
    }

    [Serializable]
    public sealed class BoundaryReport
    {
        public int schemaVersion;
        public string unityVersion;
        public string root;
        public string status;
        public BoundaryIdentity[] identities;
        public int assetsChecked;
        public int dependenciesChecked;
        public int externalAssets;
        public int unityPackageReferences;
        public int thirdPartyPackageReferences;
        public int unknownReferences;
        public bool incomplete;
        public string limitation;
        public BoundaryFinding[] findings;
    }

    /// <summary>
    /// Read-only dependency *preflight*, not a missing-reference scanner or a
    /// claim that a Unity package is automatically installable. Dynamic loads,
    /// optional APIs, and undeclared code dependencies need separate testing.
    /// </summary>
    public static class HprPackageBoundaryScanner
    {
        public const int DefaultMaxAssets = 10000;
        public const int DefaultMaxFindings = 1500;

        public static string NormalizeRoot(string path)
        {
            if (string.IsNullOrWhiteSpace(path))
                throw new ArgumentException("Select a package folder under Assets or Packages.");
            path = path.Replace('\\', '/').TrimEnd('/');
            if (path == "Assets" || path == "Packages" ||
                !(path.StartsWith("Assets/", StringComparison.Ordinal) ||
                  path.StartsWith("Packages/", StringComparison.Ordinal)) ||
                path.Split('/').Any(segment => segment == ".." || segment == "." || segment.Length == 0) ||
                !AssetDatabase.IsValidFolder(path))
                throw new ArgumentException("Choose an existing, specific folder under Assets or Packages.");
            return path;
        }

        public static string Classify(BoundaryReport report)
        {
            if (report == null || report.incomplete || report.assetsChecked == 0)
                return "INCOMPLETE";
            if (report.externalAssets > 0 || report.thirdPartyPackageReferences > 0 ||
                report.unknownReferences > 0)
                return "REVIEW_EXTERNAL_DEPENDENCIES";
            if (report.unityPackageReferences > 0)
                return "REVIEW_UNITY_PACKAGE_DECLARATIONS";
            return "NO_RESOLVED_EXTERNAL_DEPENDENCIES_FOUND";
        }

        private static bool Inside(string path, string root)
        {
            return path.Equals(root, StringComparison.Ordinal) ||
                path.StartsWith(root + "/", StringComparison.Ordinal);
        }

        private static bool BuiltIn(string path)
        {
            // Unity exposes built-in shader/primitive pseudo-assets with these
            // paths. They are not external files the publisher can export.
            return path.StartsWith("Resources/unity_builtin_extra", StringComparison.OrdinalIgnoreCase) ||
                   path.StartsWith("Library/unity default resources", StringComparison.OrdinalIgnoreCase) ||
                   path.StartsWith("Resources/unity default resources", StringComparison.OrdinalIgnoreCase);
        }

        public static BoundaryReport Scan(string packageRoot, int maxAssets = DefaultMaxAssets,
            int maxFindings = DefaultMaxFindings, Func<int, int, bool> cancelRequested = null)
        {
            string root = NormalizeRoot(packageRoot);
            if (maxAssets < 1 || maxFindings < 1)
                throw new ArgumentOutOfRangeException("Scan limits must be positive.");
            var result = new BoundaryReport
            {
                schemaVersion = 1,
                unityVersion = Application.unityVersion,
                root = root,
                limitation = "Only references resolved by AssetDatabase are checked. " +
                    "Dynamic loading, missing serialized GUIDs, runtime script dependencies, " +
                    "build profile and dependency-manifest declarations require separate review."
            };
            var findings = new List<BoundaryFinding>();
            var identities = new List<BoundaryIdentity>();
            try
            {
                string[] assets = AssetDatabase.FindAssets("", new[] { root })
                    .Select(AssetDatabase.GUIDToAssetPath)
                    .Where(path => !string.IsNullOrEmpty(path) && Inside(path, root) &&
                                   !AssetDatabase.IsValidFolder(path))
                    .Distinct(StringComparer.Ordinal)
                    .OrderBy(path => path, StringComparer.Ordinal).ToArray();
                if (assets.Length > maxAssets) result.incomplete = true;
                int scanned = Math.Min(assets.Length, maxAssets);
                for (int index = 0; index < scanned; ++index)
                {
                    if (cancelRequested != null && cancelRequested(index, scanned))
                    {
                        result.incomplete = true;
                        break;
                    }
                    string asset = assets[index];
                    string guid = AssetDatabase.AssetPathToGUID(asset);
                    if (string.IsNullOrEmpty(guid) || guid.Length != 32)
                        result.incomplete = true;
                    identities.Add(new BoundaryIdentity { assetPath = asset, guid = guid });
                    result.assetsChecked++;
                    foreach (string path in AssetDatabase.GetDependencies(asset, false)
                                 .Distinct(StringComparer.Ordinal).OrderBy(p => p, StringComparer.Ordinal))
                    {
                        if (string.IsNullOrEmpty(path) || path == asset || Inside(path, root) || BuiltIn(path))
                            continue;
                        result.dependenciesChecked++;
                        string category;
                        string action;
                        if (path.StartsWith("Assets/", StringComparison.Ordinal))
                        {
                            result.externalAssets++;
                            category = "EXTERNAL_ASSET";
                            action = "Move an owned dependency into the package, or clearly disclose/install it; never copy third-party files without rights.";
                        }
                        else if (path.StartsWith("Packages/com.unity.", StringComparison.Ordinal))
                        {
                            result.unityPackageReferences++;
                            category = "UNITY_PACKAGE";
                            action = "Declare and test the exact official Package Manager dependency in the supported workflow.";
                        }
                        else if (path.StartsWith("Packages/", StringComparison.Ordinal))
                        {
                            result.thirdPartyPackageReferences++;
                            category = "THIRD_PARTY_PACKAGE";
                            action = "Verify redistribution rights and seller package dependency declarations; do not silently bundle third-party content.";
                        }
                        else
                        {
                            result.unknownReferences++;
                            category = "UNKNOWN_PATH";
                            action = "Review this Editor-resolved path manually; it may be a Unity internal resource.";
                        }
                        if (findings.Count < maxFindings)
                            findings.Add(new BoundaryFinding
                            { category = category, asset = asset, dependency = path, action = action });
                        else result.incomplete = true;
                    }
                }
            }
            catch (Exception ex)
            {
                result.incomplete = true;
                if (findings.Count < maxFindings)
                    findings.Add(new BoundaryFinding
                    { category = "SCAN_ERROR", asset = root, dependency = "", action = ex.GetType().Name + ": " + ex.Message });
            }
            result.findings = findings.ToArray();
            result.identities = identities.ToArray();
            result.status = Classify(result);
            return result;
        }

        public static void ExportNewJson(BoundaryReport report, string fullPath)
        {
            if (report == null || string.IsNullOrWhiteSpace(fullPath) || !Path.IsPathRooted(fullPath))
                throw new ArgumentException("A completed report and absolute output path are required.");
            // Never silently overwrite evidence, even from CI.
            using (var stream = new FileStream(fullPath, FileMode.CreateNew, FileAccess.Write, FileShare.None))
            using (var writer = new StreamWriter(stream, new UTF8Encoding(false)))
                writer.Write(JsonUtility.ToJson(report, true));
        }
    }

    public sealed class HprPackageBoundaryWindow : EditorWindow
    {
        private DefaultAsset folder;
        private BoundaryReport last;
        private BoundaryUpgradeReport lastUpgrade;
        private Vector2 scroll;
        private bool scanPending;
        private string notice = "Select the top-level folder you intend to export.";

        [MenuItem("Tools/HPR/Package Boundary Inspector")]
        public static void Open()
        {
            var window = GetWindow<HprPackageBoundaryWindow>("HPR Package Boundary");
            window.minSize = new Vector2(670, 410);
            window.Show();
        }

        private void BeginScan()
        {
            // Defer work one Editor tick so the user sees an immediate
            // acknowledgement; the Editor-native progress panel is cancelable.
            string root;
            try { root = HprPackageBoundaryScanner.NormalizeRoot(AssetDatabase.GetAssetPath(folder)); }
            catch (Exception error) { notice = "Cannot scan: " + error.Message; return; }
            scanPending = true;
            last = null;
            lastUpgrade = null;
            notice = "Scanning package assets. Cancel in the Unity progress panel to mark this scan incomplete.";
            Repaint();
            EditorApplication.delayCall += () =>
            {
                try
                {
                    if (this == null) return;
                    last = HprPackageBoundaryScanner.Scan(root,
                        HprPackageBoundaryScanner.DefaultMaxAssets,
                        HprPackageBoundaryScanner.DefaultMaxFindings,
                        (done, total) => EditorUtility.DisplayCancelableProgressBar(
                            "HPR Package Boundary Inspector", "Scanning asset " + (done + 1) + " of " + total,
                            total < 1 ? 0f : (float)done / total));
                    notice = last.incomplete ? "Scan INCOMPLETE: canceled, failed, or reached a limit." :
                        "Scan finished; review the unresolved limitations before packaging.";
                }
                catch (Exception error) { last = null; notice = "Scan failed: " + error.Message; }
                finally { EditorUtility.ClearProgressBar(); scanPending = false; if (this != null) Repaint(); }
            };
        }

        private void LoadPreviousReport()
        {
            if (last == null) return;
            string path = EditorUtility.OpenFilePanel("Compare previous HPR package boundary JSON", "", "json");
            if (string.IsNullOrEmpty(path)) return;
            lastUpgrade = null;
            try
            {
                if (!File.Exists(path) || new FileInfo(path).Length > 4 * 1024 * 1024)
                    throw new IOException("Choose an existing, reasonably sized previous scan JSON file.");
                var previous = JsonUtility.FromJson<BoundaryReport>(File.ReadAllText(path));
                lastUpgrade = HprBoundaryUpgradeReview.Compare(previous, last);
                notice = lastUpgrade.incomplete ? "Comparison INCOMPLETE: previous evidence is invalid or differs in scope." :
                    "Previous/current GUID and path identities compared. Review the findings below.";
            }
            catch (Exception error) { notice = "Cannot compare: " + error.Message; }
        }

        private void OnGUI()
        {
            EditorGUILayout.Space(8);
            GUILayout.Label("PACKAGE BOUNDARY INSPECTOR", EditorStyles.boldLabel);
            EditorGUILayout.HelpBox("Read-only preflight before exporting a Unity package. " +
                "Shows dependencies on assets outside the selected folder. " +
                "It cannot certify a package, detect dynamic loads, or replace clean-project import tests.",
                MessageType.Info);
            EditorGUI.BeginDisabledGroup(scanPending);
            var choice = (DefaultAsset)EditorGUILayout.ObjectField("Top-level package folder", folder, typeof(DefaultAsset), false);
            if (choice != folder) { folder = choice; last = null; lastUpgrade = null; }
            if (GUILayout.Button("Scan dependency boundary (read only)", GUILayout.Height(32))) BeginScan();
            EditorGUI.EndDisabledGroup();
            if (scanPending)
                EditorGUILayout.HelpBox("Scanning... progress and Cancel are available in the Unity Editor progress panel.", MessageType.Info);
            EditorGUI.BeginDisabledGroup(last == null || scanPending);
            if (GUILayout.Button("Export JSON report as a NEW file"))
            {
                string dest = EditorUtility.SaveFilePanel("Export HPR package boundary report", "",
                    "package-boundary.json", "json");
                if (!string.IsNullOrEmpty(dest))
                {
                    try { HprPackageBoundaryScanner.ExportNewJson(last, dest); notice = "New report saved."; }
                    catch (Exception exception) { notice = "Report not written: " + exception.Message; }
                }
            }
            if (GUILayout.Button("Compare previous JSON scan for safe-upgrade review")) LoadPreviousReport();
            EditorGUI.EndDisabledGroup();
            if (lastUpgrade != null)
            {
                GUILayout.Label("Upgrade identity: " + lastUpgrade.status, EditorStyles.boldLabel);
                GUILayout.Label("Replaced GUIDs: " + lastUpgrade.replacedGuids + " | removed: " +
                    lastUpgrade.removedAssets + " | moved: " + lastUpgrade.movedPaths +
                    " | added: " + lastUpgrade.addedAssets);
                if (lastUpgrade.incomplete)
                    EditorGUILayout.HelpBox("Incomplete comparison: do not interpret this as an upgrade pass.", MessageType.Error);
                if (GUILayout.Button("Export upgrade comparison as NEW JSON file"))
                {
                    string dest = EditorUtility.SaveFilePanel("Export HPR upgrade identity comparison", "",
                        "package-upgrade-identity.json", "json");
                    if (!string.IsNullOrEmpty(dest))
                    {
                        try { HprBoundaryUpgradeReview.ExportNewJson(lastUpgrade, dest); notice = "New upgrade report saved."; }
                        catch (Exception error) { notice = "Upgrade report not written: " + error.Message; }
                    }
                }
            }
            EditorGUILayout.HelpBox(notice, MessageType.None);
            if (last == null) return;
            GUILayout.Label("Status: " + last.status, EditorStyles.boldLabel);
            GUILayout.Label("Assets examined: " + last.assetsChecked + " | outside Assets/ references: " +
                last.externalAssets + " | Unity packages: " + last.unityPackageReferences +
                " | third-party packages: " + last.thirdPartyPackageReferences);
            if (last.incomplete) EditorGUILayout.HelpBox("Scan incomplete: limits or an error were reached. Never interpret this report as clean.", MessageType.Error);
            scroll = EditorGUILayout.BeginScrollView(scroll);
            if (lastUpgrade != null && lastUpgrade.findings != null)
            {
                foreach (var issue in lastUpgrade.findings)
                {
                    EditorGUILayout.LabelField(issue.kind, EditorStyles.boldLabel);
                    EditorGUILayout.LabelField("Before: " + issue.before + " | After: " + issue.after,
                        EditorStyles.wordWrappedLabel);
                    EditorGUILayout.LabelField(issue.guidance, EditorStyles.wordWrappedLabel);
                    GUILayout.Space(6);
                }
                EditorGUILayout.HelpBox(lastUpgrade.limitation, MessageType.Warning);
            }
            foreach (var finding in last.findings)
            {
                EditorGUILayout.LabelField(finding.category + " | " + finding.asset, EditorStyles.boldLabel);
                EditorGUILayout.LabelField("Depends on: " + finding.dependency, EditorStyles.wordWrappedLabel);
                EditorGUILayout.LabelField(finding.action, EditorStyles.wordWrappedLabel);
                GUILayout.Space(7);
            }
            EditorGUILayout.HelpBox(last.limitation, MessageType.Warning);
            EditorGUILayout.EndScrollView();
        }
    }
}
#endif
