#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEngine;
#if UNITY_6000_1_OR_NEWER
using UnityEditor.Build.Profile;
#endif

namespace HPR.BuildSceneMatrix
{
    // Original first-party read-only configuration diagnostic.
    public sealed class HprSceneRow
    {
        public string Path, Guid, Name;
        public bool Enabled, Missing;
        public int ListIndex, BuildIndex;
    }

    public sealed class HprSceneProfile
    {
        public string Id, Title, AssetPath, Source, Error;
        public bool Active;
        public readonly List<HprSceneRow> Rows = new List<HprSceneRow>();
        public int EnabledCount => Rows.Count(r => r.Enabled);
        public string First => Rows.FirstOrDefault(r => r.Enabled)?.Path ?? "(none)";
        public bool Readable => string.IsNullOrEmpty(Error);
    }

    public sealed class HprSceneDifference
    {
        public string Key, Path, A, B, Issue;
        public bool Different, Warning;
    }

    public static class HprSceneMatrix
    {
        public const string GlobalId = "global";

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

        private static string Key(HprSceneRow r) => string.IsNullOrEmpty(r.Guid) ||
            r.Guid == "00000000000000000000000000000000" ? "path:" + r.Path : "guid:" + r.Guid;
        private static string State(List<HprSceneRow> rows)
        {
            if (rows.Count == 0) return "Absent";
            return string.Join(", ", rows.Select(r => r.Enabled ? "#" + r.BuildIndex : "Disabled"));
        }

        private static HashSet<string> ConflictingNames(HprSceneProfile profile) =>
            new HashSet<string>(profile.Rows.Where(r => r.Enabled && !string.IsNullOrEmpty(r.Name))
                .GroupBy(r => r.Name, StringComparer.OrdinalIgnoreCase)
                .Where(g => g.Select(Key).Distinct().Skip(1).Any()).Select(g => g.Key),
                StringComparer.OrdinalIgnoreCase);

        public static string Summary(HprSceneProfile profile)
        {
            if (!profile.Readable) return "Unreadable";
            int missing = profile.Rows.Count(r => r.Missing);
            int duplicate = profile.Rows.GroupBy(Key).Count(g => g.Count() > 1);
            return profile.EnabledCount + " enabled • " + missing + " stale • " + duplicate +
                " repeated • " + ConflictingNames(profile).Count + " ambiguous names";
        }

        public static List<HprSceneDifference> Compare(HprSceneProfile a, HprSceneProfile b)
        {
            if (a == null || b == null || !a.Readable || !b.Readable)
                throw new InvalidOperationException("Select two readable scene lists before comparison.");
            var keys = a.Rows.Select(Key).Concat(b.Rows.Select(Key)).Distinct().ToArray();
            var left = a.Rows.GroupBy(Key).ToDictionary(g => g.Key, g => g.ToList());
            var right = b.Rows.GroupBy(Key).ToDictionary(g => g.Key, g => g.ToList());
            var result = new List<HprSceneDifference>();
            var conflictsA = ConflictingNames(a);
            var conflictsB = ConflictingNames(b);
            foreach (string key in keys)
            {
                if (!left.TryGetValue(key, out var aa)) aa = new List<HprSceneRow>();
                if (!right.TryGetValue(key, out var bb)) bb = new List<HprSceneRow>();
                string sa = State(aa), sb = State(bb);
                var all = aa.Concat(bb).ToArray();
                var issues = new List<string>();
                if (all.Any(r => r.Missing)) issues.Add("Missing or stale scene reference");
                if (aa.Count > 1 || bb.Count > 1) issues.Add("Repeated scene entry");
                if (aa.Any(r => r.Enabled && conflictsA.Contains(r.Name)) ||
                    bb.Any(r => r.Enabled && conflictsB.Contains(r.Name))) issues.Add("Ambiguous enabled scene name");
                if (all.Select(r => r.Path).Distinct().Skip(1).Any()) issues.Add("Path differs for same identifier");
                result.Add(new HprSceneDifference { Key = key, Path = all[0].Path, A = sa, B = sb,
                    Different = sa != sb || issues.Contains("Path differs for same identifier"),
                    Warning = issues.Count > 0, Issue = string.Join("; ", issues) });
            }
            return result;
        }

        // Prefix untrusted cells which spreadsheet applications might execute as formulas.
        private static string CsvCell(string value)
        {
            value = value ?? "";
            string trimmed = value.TrimStart();
            if (trimmed.Length > 0 && "=+-@".IndexOf(trimmed[0]) >= 0) value = "'" + value;
            return "\"" + value.Replace("\"", "\"\"") + "\"";
        }
        public static void ExportNewCsv(string path, HprSceneProfile a, HprSceneProfile b)
        {
            var rows = Compare(a, b);
            // CreateNew prevents overwriting a pre-existing file. No automatic export.
            using (var stream = new FileStream(path, FileMode.CreateNew, FileAccess.Write))
            using (var writer = new StreamWriter(stream, new UTF8Encoding(true)))
            {
                writer.WriteLine("Scene,Reference state,Compared state,Different,Warning");
                writer.WriteLine(string.Join(",", new[] { "Profile identities", a.Title, b.Title, "", "" }.Select(CsvCell)));
                writer.WriteLine(string.Join(",", new[] { "Scene sources", a.Source, b.Source, "", "" }.Select(CsvCell)));
                foreach (var row in rows)
                    writer.WriteLine(string.Join(",", new[] { row.Path, row.A, row.B,
                        row.Different ? "Yes" : "No", row.Issue }.Select(CsvCell)));
            }
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
            scanned = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
            Recompare();
        }
        private void Recompare()
        {
            differences.Clear();
            status = "";
            if (profiles[left].Readable && profiles[right].Readable)
                differences = HprSceneMatrix.Compare(profiles[left], profiles[right]);
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
            int nextLeft = EditorGUILayout.Popup("Reference", left, names);
            int nextRight = EditorGUILayout.Popup("Compare", right, names);
            if (nextLeft != left || nextRight != right) { left = nextLeft; right = nextRight; Recompare(); }
            scroll = EditorGUILayout.BeginScrollView(scroll);
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
            DrawProfile("Reference", profiles[left]);
            DrawProfile("Compared", profiles[right]);
            EditorGUILayout.Space(5);
            bool readable = profiles[left].Readable && profiles[right].Readable;
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
                    if (!string.IsNullOrEmpty(filter) && row.Path.IndexOf(filter, StringComparison.OrdinalIgnoreCase) < 0) continue;
                    visibleCount++;
                    EditorGUILayout.BeginVertical(EditorStyles.helpBox);
                    EditorGUILayout.BeginHorizontal();
                    EditorGUILayout.SelectableLabel(row.Path, EditorStyles.textField, GUILayout.Height(EditorGUIUtility.singleLineHeight));
                    using (new EditorGUI.DisabledScope(string.IsNullOrEmpty(row.Path) || !row.Path.EndsWith(".unity", StringComparison.OrdinalIgnoreCase)))
                        if (GUILayout.Button("Find", GUILayout.Width(52)))
                        {
                            var scene = AssetDatabase.LoadAssetAtPath<SceneAsset>(row.Path);
                            if (scene != null) EditorGUIUtility.PingObject(scene);
                        }
                    EditorGUILayout.EndHorizontal();
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
                        try { HprSceneMatrix.ExportNewCsv(path, profiles[left], profiles[right]); status = "Exported new CSV."; }
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
