using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;

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
        public DateTimeOffset? HistoricalCapturedUtc;
        public readonly List<HprSceneRow> Rows = new List<HprSceneRow>();
        public int EnabledCount => Rows.Count(r => r.Enabled);
        public string First => Rows.FirstOrDefault(r => r.Enabled)?.Path ?? "(none)";
        public bool Readable => string.IsNullOrEmpty(Error);
    }

    public sealed class HprSceneDifference
    {
        public string Key, Path, ReferencePath, ComparedPath, A, B, Issue;
        public bool Different, Warning;
    }

    /// <summary>Structural comparison distinct from per-scene enabled build indices.</summary>
    public sealed class HprDeclaredListDelta
    {
        public bool ProfileIdentifierChanged, ProfileAssetPathChanged, SceneListSourceChanged;
        public int FirstDifferingEntryIndex = -1;
        public bool DeclaredEntrySequenceChanged => FirstDifferingEntryIndex >= 0;
    }

    public static partial class HprSceneMatrix
    {
        public const string GlobalId = "global";

        public static HprDeclaredListDelta CompareDeclaredLists(HprSceneProfile a, HprSceneProfile b)
        {
            if (a == null || b == null || !a.Readable || !b.Readable)
                throw new InvalidOperationException("Select two readable scene lists before comparison.");
            var result = new HprDeclaredListDelta
            {
                ProfileIdentifierChanged = !string.Equals(a.Id, b.Id, StringComparison.Ordinal),
                ProfileAssetPathChanged = !string.Equals(a.AssetPath ?? "", b.AssetPath ?? "", StringComparison.Ordinal),
                SceneListSourceChanged = !string.Equals(a.Source ?? "", b.Source ?? "", StringComparison.Ordinal)
            };
            int common = Math.Min(a.Rows.Count, b.Rows.Count);
            for (int i = 0; i < common; i++)
            {
                HprSceneRow x = a.Rows[i], y = b.Rows[i];
                if (!string.Equals(x.Guid ?? "", y.Guid ?? "", StringComparison.Ordinal) ||
                    !string.Equals(x.Path ?? "", y.Path ?? "", StringComparison.Ordinal) || x.Enabled != y.Enabled)
                {
                    result.FirstDifferingEntryIndex = i;
                    return result;
                }
            }
            if (a.Rows.Count != b.Rows.Count) result.FirstDifferingEntryIndex = common;
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
                bool referenceMissing = aa.Any(r => r.Missing);
                bool comparedMissing = bb.Any(r => r.Missing);
                if (referenceMissing || comparedMissing)
                    issues.Add("Missing or stale scene reference (" +
                        (referenceMissing && comparedMissing ? "both" : referenceMissing ? "reference" : "compared") + ")");
                if (aa.Count > 1 || bb.Count > 1) issues.Add("Repeated scene entry");
                if (aa.Any(r => r.Enabled && conflictsA.Contains(r.Name)) ||
                    bb.Any(r => r.Enabled && conflictsB.Contains(r.Name))) issues.Add("Ambiguous enabled scene name");
                bool pathChanged = aa.Count > 0 && bb.Count > 0 &&
                    !new HashSet<string>(aa.Select(r => r.Path), StringComparer.Ordinal)
                        .SetEquals(bb.Select(r => r.Path));
                if (pathChanged) issues.Add("Path differs for same identifier");
                else if (all.Select(r => r.Path).Distinct(StringComparer.Ordinal).Skip(1).Any())
                    issues.Add("Conflicting paths already present for same identifier");
                string referencePath = aa.FirstOrDefault()?.Path ?? "";
                string comparedPath = bb.FirstOrDefault()?.Path ?? "";
                bool missingStatusChanged = !aa.Select(r => r.Missing).SequenceEqual(bb.Select(r => r.Missing));
                result.Add(new HprSceneDifference { Key = key,
                    Path = bb.Count > 0 ? comparedPath : referencePath,
                    ReferencePath = referencePath, ComparedPath = comparedPath, A = sa, B = sb,
                    Different = sa != sb || missingStatusChanged || pathChanged,
                    Warning = issues.Count > 0, Issue = string.Join("; ", issues) });
            }
            return result;
        }

        // Prefix untrusted cells which spreadsheet applications might execute as formulas.
        private static string CsvCell(string value)
        {
            value = value ?? "";
            string trimmed = value.TrimStart();
            if ((trimmed.Length > 0 && "=+-@＝＋－＠".IndexOf(trimmed[0]) >= 0) ||
                (value.Length > 0 && "\t\r\n".IndexOf(value[0]) >= 0)) value = "'" + value;
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
                writer.WriteLine(string.Join(",", new[] { "Scene sources", a.Source, b.Source,
                    a.HistoricalCapturedUtc.HasValue ? (a.Source == b.Source ? "No" : "Yes") : "", "" }.Select(CsvCell)));
                if (a.HistoricalCapturedUtc.HasValue)
                {
                    writer.WriteLine(string.Join(",", new[] { "Reference snapshot UTC",
                        a.HistoricalCapturedUtc.Value.ToString("O", System.Globalization.CultureInfo.InvariantCulture),
                        "Live compared list", "", "" }.Select(CsvCell)));
                    writer.WriteLine(string.Join(",", new[] { "Profile asset identities", a.Id, b.Id,
                        a.Id == b.Id ? "No" : "Yes", "Confirm both lists belong to the intended project" }.Select(CsvCell)));
                    var declared = CompareDeclaredLists(a, b);
                    writer.WriteLine(string.Join(",", new[] { "Profile asset paths", a.AssetPath, b.AssetPath,
                        declared.ProfileAssetPathChanged ? "Yes" : "No", "" }.Select(CsvCell)));
                    writer.WriteLine(string.Join(",", new[] { "Declared entry sequence", a.Rows.Count + " entries",
                        b.Rows.Count + " entries", declared.DeclaredEntrySequenceChanged ? "Yes" : "No",
                        declared.DeclaredEntrySequenceChanged ?
                            "First differing list position: " + (declared.FirstDifferingEntryIndex + 1) :
                            "Enabled build indices are compared separately" }.Select(CsvCell)));

                }
                foreach (var row in rows)
                    writer.WriteLine(string.Join(",", new[] { row.Path, row.A, row.B,
                        row.Different ? "Yes" : "No", row.Issue +
                        (row.ReferencePath != row.ComparedPath && row.ReferencePath.Length > 0 &&
                         row.ComparedPath.Length > 0 ? " | Reference path: " + row.ReferencePath : "")
                    }.Select(CsvCell)));
            }
        }
    }
}
