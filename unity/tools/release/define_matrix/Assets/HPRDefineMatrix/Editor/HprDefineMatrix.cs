// Copyright (c) Multiverse. Private prerelease; not published or licensed for resale.
// Original Editor-only inspector of saved Unity 6 Build Profile scripting defines.
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

namespace HPR.DefineMatrix
{
    public sealed class DefineProfile
    {
        public string Id = "";
        public string Path = "";
        public string Name = "";
        public string Error;
        public bool IsActive;
        public DateTimeOffset? HistoricalCapturedUtc;
        public readonly List<string> Symbols = new List<string>();
        public readonly List<string> Warnings = new List<string>();
        public bool Readable { get { return string.IsNullOrEmpty(Error); } }
    }

    public sealed class DefineDifference
    {
        public string Symbol;
        public bool Left;
        public bool Right;
        public string Status { get { return Left && Right ? "Both" : Left ? "Left only" : "Right only"; } }
    }

    public static class HprDefineMatrix
    {
        // Only symbols explicitly added in each BuildProfile: never conflate these
        // with Player Settings, csc.rsp or build-command additional defines.
        public const int MaxProfiles = 256;
        public const int MaxSymbols = 4096;
        private static bool ValidSymbol(string value)
        {
            if (string.IsNullOrEmpty(value) || value.Length > 128) return false;
            if (!(value[0] == '_' || char.IsLetter(value[0]) && value[0] < 128)) return false;
            foreach (char ch in value)
                if (!(ch == '_' || ch >= 'A' && ch <= 'Z' || ch >= 'a' && ch <= 'z' ||
                      ch >= '0' && ch <= '9')) return false;
            return true;
        }

        public static void ParseDeclared(DefineProfile target, string[] source)
        {
            if (target == null) throw new ArgumentNullException(nameof(target));
            if (source == null) return; // No profile-specific defines is a valid state.
            if (source.Length > MaxSymbols) throw new InvalidOperationException("Profile symbol list exceeds the supported limit.");
            var seen = new HashSet<string>(StringComparer.Ordinal);
            for (int n = 0; n < source.Length; n++)
            {
                string raw = source[n];
                if (raw == null || !ValidSymbol(raw))
                {
                    target.Warnings.Add("Entry " + (n + 1) + " is an empty or invalid scripting define.");
                    continue;
                }
                if (!seen.Add(raw))
                {
                    target.Warnings.Add("Repeated scripting define: " + raw);
                    continue;
                }
                target.Symbols.Add(raw);
            }
            target.Symbols.Sort(StringComparer.Ordinal);
        }

        public static List<DefineProfile> Scan()
        {
            var result = new List<DefineProfile>();
#if UNITY_6000_1_OR_NEWER
            try
            {
                var paths = new SortedSet<string>(StringComparer.Ordinal);
                var ids = AssetDatabase.FindAssets("t:BuildProfile", new[] { "Assets" });
                if (ids.Length > MaxProfiles)
                    throw new InvalidOperationException("Too many Build Profiles; narrow the project before scanning.");
                foreach (var guid in ids)
                {
                    string path = AssetDatabase.GUIDToAssetPath(guid);
                    if (!string.IsNullOrEmpty(path)) paths.Add(path);
                }
                BuildProfile active = BuildProfile.GetActiveBuildProfile();
                if (active != null)
                {
                    string activePath = AssetDatabase.GetAssetPath(active);
                    if (!string.IsNullOrEmpty(activePath)) paths.Add(activePath);
                    else result.Add(new DefineProfile { Name = "Active unsaved profile", IsActive = true,
                        Error = "The current profile has no persistent asset path and cannot be certified." });
                }
                if (paths.Count > MaxProfiles)
                    throw new InvalidOperationException("Build Profile count exceeds the supported limit.");
                foreach (string path in paths)
                {
                    var row = new DefineProfile { Path = path, Id = AssetDatabase.AssetPathToGUID(path), Name = Path.GetFileNameWithoutExtension(path) };
                    result.Add(row);
                    try
                    {
                        var asset = AssetDatabase.LoadAssetAtPath<BuildProfile>(path);
                        if (asset == null) throw new InvalidOperationException("Build Profile could not be loaded.");
                        row.IsActive = asset == active;
                        ParseDeclared(row, asset.scriptingDefines);
                    }
                    catch (Exception ex) { row.Error = ex.GetType().Name + ": " + ex.Message; }
                }
            }
            catch (Exception ex)
            {
                result.Add(new DefineProfile { Name = "Profile discovery error", Error = ex.GetType().Name + ": " + ex.Message });
            }
#else
            result.Add(new DefineProfile { Name = "Unsupported Unity Editor",
                Error = "HPR Define Matrix requires Unity 6.1 or newer." });
#endif
            return result;
        }

        public static List<DefineDifference> Compare(DefineProfile a, DefineProfile b)
        {
            if (a == null || b == null || !a.Readable || !b.Readable)
                throw new InvalidOperationException("Select two readable saved profiles before comparing.");
            var left = new HashSet<string>(a.Symbols, StringComparer.Ordinal);
            var right = new HashSet<string>(b.Symbols, StringComparer.Ordinal);
            var names = new SortedSet<string>(left, StringComparer.Ordinal);
            names.UnionWith(right);
            return names.Select(n => new DefineDifference { Symbol = n, Left = left.Contains(n), Right = right.Contains(n) }).ToList();
        }

        private static string Csv(string raw)
        {
            // Create-only CSV, never formulas when opened in spreadsheet software.
            if (raw == null) raw = "";
            string trimmed = raw.TrimStart();
            if ((trimmed.Length > 0 && "=+-@＝＋－＠".IndexOf(trimmed[0]) >= 0) ||
                (raw.Length > 0 && "\t\r\n".IndexOf(raw[0]) >= 0)) raw = "'" + raw;
            return "\"" + raw.Replace("\"", "\"\"").Replace("\r", " ").Replace("\n", " ") + "\"";
        }

        public static void ExportNewCsv(string destination, DefineProfile a, DefineProfile b)
        {
            if (string.IsNullOrWhiteSpace(destination)) throw new ArgumentException("Choose a new CSV output path.", nameof(destination));
            if (!destination.EndsWith(".csv", StringComparison.OrdinalIgnoreCase))
                throw new ArgumentException("Only CSV output is supported.", nameof(destination));
            var rows = Compare(a, b);
            // No file created before all comparisons and bounded validation succeed.
            if (rows.Count > MaxSymbols * 2) throw new InvalidOperationException("Export result is too large.");
            var csv = new StringBuilder("Profile left,Profile right,Symbol,Left,Right,Status\r\n");
            if (a.HistoricalCapturedUtc.HasValue)
            {
                csv.Append(Csv(a.Path)).Append(',').Append(Csv(b.Path))
                   .Append(',').Append(Csv("Reference captured UTC"))
                   .Append(",,,").Append(Csv(a.HistoricalCapturedUtc.Value.ToUniversalTime().ToString("O")))
                   .Append("\r\n");
                csv.Append(Csv(a.Path)).Append(',').Append(Csv(b.Path))
                   .Append(',').Append(Csv("Reference asset identity changed"))
                   .Append(",,,").Append(Csv(string.Equals(a.Id, b.Id, StringComparison.Ordinal) ?
                       "No" : "Yes — verify the intended project and profile"))
                   .Append("\r\n");
            }
            foreach (var row in rows)
                csv.Append(Csv(a.Path)).Append(',').Append(Csv(b.Path)).Append(',').Append(Csv(row.Symbol))
                   .Append(',').Append(row.Left ? "yes" : "no").Append(',').Append(row.Right ? "yes" : "no")
                   .Append(',').Append(Csv(row.Status)).Append("\r\n");
            // Never let an apparently clean CSV omit the malformed declarations
            // visible in the Editor window. They require separate user review.
            foreach (string warning in a.Warnings)
                csv.Append(Csv(a.Path)).Append(',').Append(Csv(b.Path)).Append(',').Append(Csv(warning))
                   .Append(",,,").Append(Csv("Reference warning")).Append("\r\n");
            foreach (string warning in b.Warnings)
                csv.Append(Csv(a.Path)).Append(',').Append(Csv(b.Path)).Append(',').Append(Csv(warning))
                   .Append(",,,").Append(Csv("Compared warning")).Append("\r\n");
            // FileMode.CreateNew is intentionally atomic and refuses overwrite.
            using (var stream = new FileStream(destination, FileMode.CreateNew, FileAccess.Write, FileShare.None))
            using (var writer = new StreamWriter(stream, new UTF8Encoding(false))) writer.Write(csv.ToString());
        }
    }

    public sealed class HprDefineMatrixWindow : EditorWindow
    {
        private List<DefineProfile> profiles = new List<DefineProfile>();
        private int left, right;
        private Vector2 scroll;
        private string filter = "", status = "";
        private bool differencesOnly;
        private HprDefineBaseline baseline;
        private DefineProfile Reference { get { return baseline == null ? profiles[left] : baseline.Profile; } }

        [MenuItem("Tools/HPR/Define Matrix")]
        public static HprDefineMatrixWindow OpenWindow()
        {
            var window = GetWindow<HprDefineMatrixWindow>("Define Matrix");
            window.minSize = new Vector2(570f, 380f);
            window.Show();
            return window;
        }
        private void OnEnable() { RefreshProfiles(); }
        private void RefreshProfiles()
        {
            if (profiles == null) profiles = new List<DefineProfile>();
            string oldLeft = left >= 0 && left < profiles.Count ? profiles[left].Id : null;
            string oldRight = right >= 0 && right < profiles.Count ? profiles[right].Id : null;
            profiles = HprDefineMatrix.Scan();
            left = oldLeft == null ? 0 : Math.Max(0, profiles.FindIndex(p => p.Id == oldLeft));
            right = oldRight == null ? Math.Min(1, profiles.Count - 1) :
                Math.Max(0, profiles.FindIndex(p => p.Id == oldRight));
            status = "Scanned saved profile-specific scripting defines without changing project settings.";
        }
        private void SaveReference()
        {
            string path = EditorUtility.SaveFilePanel("Save a NEW declared-define reference",
                "", "hpr-release-defines", HprDefineBaseline.Extension);
            if (string.IsNullOrEmpty(path)) return;
            try
            {
                HprDefineBaseline.SaveNew(path, profiles[left], DateTimeOffset.UtcNow);
                status = "Saved a new reference without changing Unity project assets.";
            }
            catch (Exception ex) { status = "Reference save refused: " + ex.Message; }
        }
        private void LoadReference()
        {
            string path = EditorUtility.OpenFilePanel("Load a saved define reference",
                "", HprDefineBaseline.Extension);
            if (string.IsNullOrEmpty(path)) return;
            try
            {
                var loaded = HprDefineBaseline.Load(path);
                baseline = loaded;
                int same = profiles.FindIndex(p => p.Id == loaded.Profile.Id && p.Readable);
                if (same >= 0) right = same;
                status = "Saved reference loaded read-only. Verify it belongs to this project.";
            }
            catch (Exception ex) { status = "Reference load refused: " + ex.Message; }
        }
        private void DrawReferenceControls()
        {
            EditorGUILayout.BeginHorizontal();
            using (new EditorGUI.DisabledScope(baseline != null || !profiles[left].Readable))
                if (GUILayout.Button("Save live define reference…")) SaveReference();
            if (GUILayout.Button("Load saved define reference…")) LoadReference();
            EditorGUILayout.EndHorizontal();
            if (baseline == null) return;
            EditorGUILayout.HelpBox("Saved profile: " + baseline.Profile.Name +
                " · captured " + baseline.CapturedUtc.ToString("u") +
                ". A saved profile GUID alone does not establish project identity.", MessageType.Info);
            if (GUILayout.Button("Return to live profile comparison"))
            {
                baseline = null;
                status = "Comparing two current saved profiles again.";
            }
        }
        private void OnGUI()
        {
            EditorGUILayout.LabelField("HPR DEFINE MATRIX", EditorStyles.boldLabel);
            EditorGUILayout.HelpBox("Compare only explicit scripting defines in saved Unity Build Profile assets. Player Settings, csc.rsp, command-line defines and actual compiled symbols are NOT inspected. No builds or profile switches occur.", MessageType.Info);
            if (GUILayout.Button("Rescan saved Build Profiles", GUILayout.Height(29))) RefreshProfiles();
            if (profiles.Count == 0)
            {
                EditorGUILayout.HelpBox("No saved Build Profile assets found under Assets. Create two profiles in Unity to compare their custom defines.", MessageType.Info);
                return;
            }
            string[] labels = profiles.Select(p => p.Name + (p.IsActive ? " (active)" : "") +
                (p.Readable ? "" : " (unreadable)")).ToArray();
            left = Mathf.Clamp(left, 0, profiles.Count - 1);
            right = Mathf.Clamp(right, 0, profiles.Count - 1);
            if (baseline == null)
                left = EditorGUILayout.Popup("Reference profile", left, labels);
            else
                EditorGUILayout.LabelField("Reference", "Saved snapshot");
            right = EditorGUILayout.Popup("Compared profile", right, labels);
            DrawReferenceControls();
            var a = Reference; var b = profiles[right];
            if (!a.Readable || !b.Readable)
            {
                EditorGUILayout.HelpBox("Profile read failed: " + (a.Error ?? b.Error), MessageType.Error);
                return;
            }
            if (baseline != null && !string.Equals(a.Id, b.Id, StringComparison.Ordinal))
                EditorGUILayout.HelpBox("The historical profile asset identifier differs from the selected live profile. " +
                    "Check whether this comparison is intentional before interpreting the results.", MessageType.Warning);
            foreach (var warning in a.Warnings.Concat(b.Warnings).Distinct())
                EditorGUILayout.HelpBox(warning, MessageType.Warning);
            var differences = HprDefineMatrix.Compare(a, b);
            int onlyA = differences.Count(d => d.Left && !d.Right);
            int onlyB = differences.Count(d => d.Right && !d.Left);
            EditorGUILayout.LabelField("Shared: " + (differences.Count - onlyA - onlyB) + "    Reference only: " + onlyA +
                "    Compared only: " + onlyB, EditorStyles.boldLabel);
            EditorGUILayout.HelpBox(onlyA + onlyB == 0 ?
                "These references declare the same additional defines. This does not certify equal builds." :
                "Different profile-specific symbols can intentionally compile different features. Review the differences before releasing a build.",
                onlyA + onlyB == 0 ? MessageType.Info : MessageType.Warning);
            differencesOnly = EditorGUILayout.ToggleLeft("Show differences only", differencesOnly);
            filter = EditorGUILayout.TextField("Filter symbol", filter);
            EditorGUILayout.Space(3f);
            scroll = EditorGUILayout.BeginScrollView(scroll);
            EditorGUILayout.BeginHorizontal();
            GUILayout.Label("Symbol", EditorStyles.boldLabel, GUILayout.MinWidth(200));
            GUILayout.Label("Reference", EditorStyles.boldLabel, GUILayout.Width(100));
            GUILayout.Label("Compared", EditorStyles.boldLabel, GUILayout.Width(100));
            EditorGUILayout.EndHorizontal();
            int shown = 0;
            foreach (var entry in differences)
            {
                if (differencesOnly && entry.Left == entry.Right) continue;
                if (!string.IsNullOrEmpty(filter) && entry.Symbol.IndexOf(filter, StringComparison.OrdinalIgnoreCase) < 0) continue;
                EditorGUILayout.BeginHorizontal();
                GUILayout.Label(entry.Symbol, GUILayout.MinWidth(200));
                GUILayout.Label(entry.Left ? "Included" : "Absent", GUILayout.Width(100));
                GUILayout.Label(entry.Right ? "Included" : "Absent", GUILayout.Width(100));
                EditorGUILayout.EndHorizontal();
                shown++;
            }
            EditorGUILayout.EndScrollView();
            if (shown == 0) EditorGUILayout.LabelField("No matching symbols in the current view.");
            EditorGUILayout.Space(4f);
            if (GUILayout.Button("Export a NEW CSV comparison…", GUILayout.Height(27)))
            {
                string file = EditorUtility.SaveFilePanel("Export a new profile define comparison", "", "hpr-define-matrix", "csv");
                if (!string.IsNullOrEmpty(file))
                {
                    try { HprDefineMatrix.ExportNewCsv(file, a, b); status = "Created a new report without changing any Unity assets. Inspect project paths before sharing."; }
                    catch (Exception e) { status = "Export refused: " + e.Message; }
                }
            }
            EditorGUILayout.HelpBox(status, MessageType.None);
        }
    }
}
#endif
