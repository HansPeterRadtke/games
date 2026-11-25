#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
#if UNITY_6000_1_OR_NEWER
using UnityEditor.Build.Profile;
#endif

namespace HPR.BuildSceneMatrix
{
    public static partial class HprSceneMatrix
    {
        private static void ReadRows(HprSceneProfile p, EditorBuildSettingsScene[] scenes)
        {
            if (scenes == null) throw new InvalidOperationException("Unity returned no scene list.");
            int enabledIndex = 0;
            for (int i = 0; i < scenes.Length; i++)
            {
                var s = scenes[i];
                if (s == null)
                {
                    p.Rows.Add(new HprSceneRow { Path = "(null scene entry)", Name = "", Guid = "", Missing = true,
                        ListIndex = i, BuildIndex = -1 });
                    continue;
                }
                string path = s.path ?? "";
                // Resolve against the asset database rather than trusting a stale path.
                string guid = s.guid.ToString();
                string resolved = string.IsNullOrEmpty(guid) ? "" : AssetDatabase.GUIDToAssetPath(guid);
                bool missing = string.IsNullOrEmpty(path) || string.IsNullOrEmpty(resolved) ||
                    !string.Equals(path, resolved, StringComparison.Ordinal) ||
                    AssetDatabase.LoadAssetAtPath<SceneAsset>(path) == null;
                p.Rows.Add(new HprSceneRow { Path = path, Guid = guid,
                    Name = System.IO.Path.GetFileNameWithoutExtension(path), Enabled = s.enabled,
                    Missing = missing, ListIndex = i, BuildIndex = s.enabled ? enabledIndex++ : -1 });
            }
        }

        public static List<HprSceneProfile> Scan()
        {
            var result = new List<HprSceneProfile>();
            var global = new HprSceneProfile { Id = GlobalId, Title = "Global scenes",
                Source = "Shared scene list" };
            result.Add(global);
#if UNITY_6000_1_OR_NEWER
            try { ReadRows(global, EditorBuildSettings.globalScenes); }
            catch (Exception e) { global.Error = e.GetType().Name + ": " + e.Message; }
            BuildProfile active = null;
            try { active = BuildProfile.GetActiveBuildProfile(); global.Active = active == null; }
            catch (Exception e) { global.Error = "Active profile unreadable: " + e.Message; }
            var paths = new SortedSet<string>(StringComparer.Ordinal);
            try
            {
                foreach (var guid in AssetDatabase.FindAssets("t:BuildProfile", new[] { "Assets" }))
                    paths.Add(AssetDatabase.GUIDToAssetPath(guid));
                if (active != null)
                {
                    string path = AssetDatabase.GetAssetPath(active);
                    if (!string.IsNullOrEmpty(path)) paths.Add(path);
                    else result.Add(new HprSceneProfile { Id = "active-unbacked", Title = active.name,
                        Active = true, Error = "Active profile has no persistent asset path." });
                }
            }
            catch (Exception e) { global.Error = "Profile discovery incomplete: " + e.Message; }
            foreach (string path in paths)
            {
                var p = new HprSceneProfile { Id = AssetDatabase.AssetPathToGUID(path), AssetPath = path, Title = path };
                result.Add(p);
                try
                {
                    var profile = AssetDatabase.LoadAssetAtPath<BuildProfile>(path);
                    if (profile == null) throw new InvalidOperationException("Build Profile asset cannot be loaded.");
                    p.Title = profile.name + "  [" + path + "]";
                    p.Active = profile == active;
                    p.Source = profile.overrideGlobalScenes ? "Overrides global scenes" : "Inherits global scenes";
                    ReadRows(p, profile.GetScenesForBuild());
                }
                catch (Exception e) { p.Error = e.GetType().Name + ": " + e.Message; }
            }
#else
            global.Error = "Build Scene Matrix needs Unity 6.1 or newer. This editor is not supported.";
#endif
            return result;
        }

    }

    public sealed class HprBuildSceneMatrixWindow : EditorWindow
    {
        private List<HprSceneProfile> profiles;
        private List<HprSceneDifference> differences = new List<HprSceneDifference>();
        private int left, right;
        private bool differencesOnly = true, showOverview;
        private int visibleCount;
        private string filter = "", scanned = "", status = "";
        private Vector2 scroll;
        private DateTimeOffset scannedUtc;
        private HprSceneBaseline baseline;
        private HprSceneProfile Reference => baseline == null ? profiles[left] : baseline.Profile;
        [MenuItem("Tools/HPR/Build Scene Matrix")]
        public static void Open() => GetWindow<HprBuildSceneMatrixWindow>("Build Scene Matrix");
        private void OnEnable() { minSize = new Vector2(480, 340); Refresh(); }
        private void OnFocus() { if (profiles == null) Refresh(); }

        private void Refresh()
        {
            string a = profiles != null && profiles.Count > left ? profiles[left].Id : HprSceneMatrix.GlobalId;
            string b = profiles != null && profiles.Count > right ? profiles[right].Id : null;
            profiles = HprSceneMatrix.Scan();
            left = Math.Max(0, profiles.FindIndex(p => p.Id == a));
            int defaultRight = profiles.FindIndex(p => p.Active && p.Id != HprSceneMatrix.GlobalId);
            if (defaultRight < 0) defaultRight = Math.Min(1, profiles.Count - 1);
            int preserved = profiles.FindIndex(p => p.Id == b);
            right = preserved >= 0 ? preserved : defaultRight;
            scannedUtc = DateTimeOffset.UtcNow;
            scanned = scannedUtc.ToLocalTime().ToString("yyyy-MM-dd HH:mm:ss");
            Recompare();
        }
        private void Recompare()
        {
            differences.Clear();
            status = "";
            if (Reference.Readable && profiles[right].Readable)
                differences = HprSceneMatrix.Compare(Reference, profiles[right]);
        }
        private void SaveBaseline()
        {
            string path = EditorUtility.SaveFilePanel("Save current scene reference (new file only)",
                "", "build-scenes", HprSceneBaseline.Extension);
            if (string.IsNullOrEmpty(path)) return;
            try
            {
                HprSceneBaseline.SaveNew(path, profiles[left], scannedUtc);
                status = "Saved the scanned reference. No existing file was replaced.";
            }
            catch (Exception e) { status = "Snapshot save failed: " + e.Message; }
        }

        private void LoadBaseline()
        {
            string path = EditorUtility.OpenFilePanel("Open saved scene reference", "", HprSceneBaseline.Extension);
            if (string.IsNullOrEmpty(path)) return;
            try
            {
                var loaded = HprSceneBaseline.Load(path);
                baseline = loaded;
                int same = profiles.FindIndex(p => p.Id == loaded.Profile.Id && p.Readable);
                if (same >= 0) right = same;
                Recompare();
                status = "Saved reference loaded. No project settings or active profile changed.";
            }
            catch (Exception e) { status = "Snapshot load failed: " + e.Message; }
        }

        private void DrawBaselineControls()
        {
            EditorGUILayout.BeginHorizontal();
            using (new EditorGUI.DisabledScope(baseline != null || !profiles[left].Readable))
                if (GUILayout.Button("Save live reference…")) SaveBaseline();
            if (GUILayout.Button("Load saved reference…")) LoadBaseline();
            EditorGUILayout.EndHorizontal();
            if (baseline == null) return;
            EditorGUILayout.LabelField("Saved profile: " + baseline.Profile.Title, EditorStyles.wordWrappedLabel);
            EditorGUILayout.HelpBox("Captured: " + baseline.CapturedUtc.ToString("u") +
                " (UTC). Use a snapshot from the intended project; profile identity alone cannot establish that.",
                MessageType.Info);
            if (baseline.Profile.Id != profiles[right].Id)
                EditorGUILayout.HelpBox("The saved and current profile identifiers differ. Check that this is intentional.",
                    MessageType.Warning);
            if (GUILayout.Button("Return to live reference"))
            {
                baseline = null;
                Recompare();
            }
        }

        private void DrawProfile(string label, HprSceneProfile p)
        {
            EditorGUILayout.LabelField(label + ": " + (p.Active ? "ACTIVE · " : "") + p.Source, EditorStyles.boldLabel);
            if (!p.Readable) { EditorGUILayout.HelpBox(p.Error, MessageType.Error); return; }
            EditorGUILayout.LabelField(p.EnabledCount + " enabled / " + p.Rows.Count + " listed");
            EditorGUILayout.SelectableLabel("Start: " + p.First, EditorStyles.textField, GUILayout.Height(EditorGUIUtility.singleLineHeight));
            if (p.EnabledCount == 0) EditorGUILayout.HelpBox("No enabled scenes in this declared list.", MessageType.Warning);
        }
        private void OnGUI()
        {
            if (profiles == null || profiles.Count == 0) Refresh();
            EditorGUILayout.Space(6);
            EditorGUILayout.LabelField("BUILD SCENE MATRIX", EditorStyles.boldLabel);
            EditorGUILayout.HelpBox("Read-only: compare declared effective scene lists without switching build profiles. Does not certify a build or custom build scripts.", MessageType.Info);
            EditorGUILayout.BeginHorizontal();
            if (GUILayout.Button("Scan project", GUILayout.Width(112))) Refresh();
            GUILayout.Label("Snapshot: " + scanned, EditorStyles.miniLabel);
            GUILayout.FlexibleSpace();
            EditorGUILayout.EndHorizontal();
            var names = profiles.Select(p => (p.Active ? "[Active] " : "") + p.Title).ToArray();
            int nextLeft = left;
            if (baseline == null)
                nextLeft = EditorGUILayout.Popup("Live reference", left, names);
            else
                EditorGUILayout.LabelField("Reference", "Saved snapshot");
            int nextRight = EditorGUILayout.Popup("Compare", right, names);
            if (nextLeft != left || nextRight != right) { left = nextLeft; right = nextRight; Recompare(); }
            scroll = EditorGUILayout.BeginScrollView(scroll);
            DrawBaselineControls();
            showOverview = EditorGUILayout.Foldout(showOverview, "All profiles (" + profiles.Count + ")", true);
            if (showOverview)
            {
                for (int n = 0; n < profiles.Count; n++)
                {
                    var p = profiles[n];
                    EditorGUILayout.BeginVertical(EditorStyles.helpBox);
                    EditorGUILayout.BeginHorizontal();
                    EditorGUILayout.LabelField((p.Active ? "[Active] " : "") + p.Title, EditorStyles.wordWrappedLabel);
                    if (GUILayout.Button("Compare", GUILayout.Width(80))) { right = n; Recompare(); }
                    EditorGUILayout.EndHorizontal();
                    EditorGUILayout.LabelField(p.Source + " | " + HprSceneMatrix.Summary(p), EditorStyles.wordWrappedLabel);
                    if (!p.Readable) EditorGUILayout.HelpBox(p.Error, MessageType.Error);
                    else EditorGUILayout.SelectableLabel("Start: " + p.First, EditorStyles.textField,
                        GUILayout.Height(EditorGUIUtility.singleLineHeight));
                    EditorGUILayout.EndVertical();
                }
            }
            DrawProfile(baseline == null ? "Reference" : "Saved reference", Reference);
            DrawProfile("Compared", profiles[right]);
            if (baseline != null && Reference.Readable && profiles[right].Readable &&
                Reference.Source != profiles[right].Source)
                EditorGUILayout.HelpBox("The source of the scene list has changed (shared, inherited or overridden).",
                    MessageType.Warning);
            EditorGUILayout.Space(5);
            bool readable = Reference.Readable && profiles[right].Readable;
            if (readable)
            {
                EditorGUILayout.LabelField(differences.Count(d => d.Different) + " differences • " +
                    differences.Count(d => d.Warning) + " rows with warnings", EditorStyles.boldLabel);
                differencesOnly = EditorGUILayout.ToggleLeft("Only differences or warnings", differencesOnly);
                filter = EditorGUILayout.TextField("Filter scene path", filter);
                visibleCount = 0;
                foreach (var row in differences)
                {
                    if (differencesOnly && !row.Different && !row.Warning) continue;
                    if (!string.IsNullOrEmpty(filter) &&
                        row.Path.IndexOf(filter, StringComparison.OrdinalIgnoreCase) < 0 &&
                        row.ReferencePath.IndexOf(filter, StringComparison.OrdinalIgnoreCase) < 0) continue;
                    visibleCount++;
                    EditorGUILayout.BeginVertical(EditorStyles.helpBox);
                    EditorGUILayout.BeginHorizontal();
                    EditorGUILayout.SelectableLabel(row.Path, EditorStyles.textField, GUILayout.Height(EditorGUIUtility.singleLineHeight));
                    string livePath = !string.IsNullOrEmpty(row.ComparedPath) ? row.ComparedPath :
                        baseline == null ? row.ReferencePath : "";
                    using (new EditorGUI.DisabledScope(string.IsNullOrEmpty(livePath) ||
                        !livePath.EndsWith(".unity", StringComparison.OrdinalIgnoreCase)))
                        if (GUILayout.Button("Find", GUILayout.Width(52)))
                        {
                            var scene = AssetDatabase.LoadAssetAtPath<SceneAsset>(livePath);
                            if (scene != null) EditorGUIUtility.PingObject(scene);
                        }
                    EditorGUILayout.EndHorizontal();
                    if (row.ReferencePath != row.ComparedPath && !string.IsNullOrEmpty(row.ReferencePath) &&
                        !string.IsNullOrEmpty(row.ComparedPath))
                        EditorGUILayout.SelectableLabel("Previous path: " + row.ReferencePath, EditorStyles.textField,
                            GUILayout.Height(EditorGUIUtility.singleLineHeight));
                    EditorGUILayout.LabelField("Ref: " + row.A + "    Compared: " + row.B, EditorStyles.wordWrappedLabel);
                    if (row.Warning) EditorGUILayout.HelpBox(row.Issue, MessageType.Warning);
                    EditorGUILayout.EndVertical();
                }
                if (visibleCount == 0) EditorGUILayout.HelpBox(differences.Count == 0 ?
                    "No scene entries to compare." : "No rows match the current filter.", MessageType.None);
                if (GUILayout.Button("Export full comparison CSV…"))
                {
                    var path = EditorUtility.SaveFilePanel("Export comparison (new file only)", "", "build-scene-comparison", "csv");
                    if (!string.IsNullOrEmpty(path))
                    {
                        try { HprSceneMatrix.ExportNewCsv(path, Reference, profiles[right]); status = "Exported new CSV."; }
                        catch (Exception e) { status = "Export failed: " + e.Message; }
                    }
                }
            }
            if (!string.IsNullOrEmpty(status)) EditorGUILayout.HelpBox(status, MessageType.Info);
            EditorGUILayout.EndScrollView();
        }
    }
}
#endif
