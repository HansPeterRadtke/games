using System;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using HPR.BuildSceneMatrix;

namespace HPR.BuildSceneGate
{
    internal static class Program
    {
        private const string Version = "0.2.0";
        private const string Usage =
            "HPR Scene Gate — read-only declared scene configuration comparison\n" +
            "Usage: dotnet HprSceneGate.dll check REFERENCE.hpr-scenes PROJECT global|Assets/Profile.asset [--format text|json]\n" +
            "       dotnet HprSceneGate.dll compare REFERENCE.hpr-scenes CURRENT.hpr-scenes\n" +
            "       dotnet HprSceneGate.dll capture PROJECT global|Assets/Profile.asset OUTPUT.hpr-scenes\n" +
            "Check reads saved project files now; default text, optional JSON. It creates no snapshot.\n" +
            "Compare writes only JSON; capture writes one new snapshot outside the project. Never starts Unity.\n" +
            "Check/compare exit 0: same declared configuration, no warnings. Capture exit 0: snapshot created.\n" +
            "Exit 1: configuration differs or diagnostic warnings exist.\n" +
            "Exit 2: invalid input, arguments or read error.\n" +
            "Choose the reference and explicit project/profile you intend to check.\n" +
            "This does not certify unsaved Editor state, the active profile or the contents/success of a build.";

        private static int Main(string[] args)
        {
            Console.OutputEncoding = new UTF8Encoding(false);
            if (args.Length == 1 && (args[0] == "--help" || args[0] == "-h"))
            {
                Console.WriteLine(Usage);
                return 0;
            }
            if (args.Length == 1 && args[0] == "--version")
            {
                Console.WriteLine(Version);
                return 0;
            }
            if (args.Length > 0 && args[0] == "check")
            {
                if ((args.Length == 4 || args.Length == 6) &&
                    (args.Length == 4 || (args[4] == "--format" &&
                        (args[5] == "text" || args[5] == "json"))))
                    return Check(args[1], args[2], args[3], args.Length == 4 || args[5] == "text");
                Console.Error.WriteLine(Usage);
                return 2;
            }
            if (args.Length == 4 && args[0] == "capture")
                return Capture(args[1], args[2], args[3]);
            if (args.Length != 3 || args[0] != "compare")
            {
                Console.Error.WriteLine(Usage);
                return 2;
            }

            try
            {
                HprSceneBaseline original = LoadReference(args[1]);
                HprSceneBaseline current = LoadReference(args[2]);
                return Compare(original, current.Profile, current.CapturedUtc);
            }
            catch (Exception e) when (IsInputError(e)) { return Error(e, false); }
        }

        private static bool IsInputError(Exception e) => e is IOException || e is InvalidDataException ||
            e is ArgumentException || e is UnauthorizedAccessException ||
            e is NotSupportedException || e is InvalidOperationException;

        private static HprSceneBaseline LoadReference(string path)
        {
            RegularFileInput.RequireRegular(path);
            return HprSceneBaseline.Load(path);
        }

        private static int Check(string reference, string project, string selector, bool text)
        {
            try
            {
                HprSceneBaseline original = LoadReference(reference);
                var started = DateTimeOffset.UtcNow;
                var current = SavedUnitySceneLists.Capture(project, selector);
                var completed = DateTimeOffset.UtcNow;
                return Compare(original, current.Profile, completed, text, true,
                    Path.GetFullPath(project), selector, current.UnityVersion, started);
            }
            catch (Exception e) when (IsInputError(e)) { return Error(e, text); }
        }

        private static int Compare(HprSceneBaseline original, HprSceneProfile b,
            DateTimeOffset capturedUtc, bool text = false, bool freshSavedRead = false,
            string project = null, string selector = null, string unityVersion = null,
            DateTimeOffset? readStartedUtc = null)
        {
            HprSceneProfile a = original.Profile;
            var rows = HprSceneMatrix.Compare(a, b);
            var declared = HprSceneMatrix.CompareDeclaredLists(a, b);
            int firstDifference = declared.FirstDifferingEntryIndex;
            bool emptyReference = a.EnabledCount == 0, emptyCurrent = b.EnabledCount == 0;
            bool chronologyUnexpected = capturedUtc < original.CapturedUtc;
            int drift = rows.Count(r => r.Different), warnings = rows.Count(r => r.Warning);
            bool pass = !declared.ProfileIdentifierChanged && !declared.SceneListSourceChanged &&
                !declared.ProfileAssetPathChanged && !declared.DeclaredEntrySequenceChanged &&
                !emptyReference && !emptyCurrent && !chronologyUnexpected &&
                drift == 0 && warnings == 0;

            if (text)
            {
                Console.WriteLine(pass
                    ? "Scene Gate: MATCH — saved scene configuration matches the reference without warnings."
                    : "Scene Gate: REVIEW REQUIRED — saved scene configuration differs or contains warnings.");
                Console.WriteLine("Project: " + SafeText(project));
                Console.WriteLine("Selected list: " + SafeText(selector));
                Console.WriteLine("List source: " + SafeText(b.Source));
                Console.WriteLine("Launch scene: " + SafeText(b.First));
                Console.WriteLine("Reference launch scene: " + SafeText(a.First));
                Console.WriteLine("Scenes: " + b.EnabledCount + " enabled; " + b.Rows.Count + " declared.");
                Console.WriteLine("Reference captured: " + original.CapturedUtc.ToString("O", CultureInfo.InvariantCulture));
                Console.WriteLine("Saved files read now: " + capturedUtc.ToString("O", CultureInfo.InvariantCulture) +
                    " (Unity " + SafeText(unityVersion) + ").");
                if (declared.ProfileIdentifierChanged)
                    Console.WriteLine("Review: selected profile identity differs from the reference.");
                if (declared.ProfileAssetPathChanged)
                    Console.WriteLine("Review: profile path changed from " + SafeText(a.AssetPath) + " to " + SafeText(b.AssetPath) + ".");
                if (declared.SceneListSourceChanged)
                    Console.WriteLine("Review: list source changed from " + SafeText(a.Source) + " to " + SafeText(b.Source) + ".");
                if (declared.DeclaredEntrySequenceChanged)
                    Console.WriteLine("First differing declared entry " + (firstDifference + 1) + ": " +
                        TextRow(a, firstDifference) + " -> " + TextRow(b, firstDifference) + ".");
                if (emptyReference || emptyCurrent)
                    Console.WriteLine("Review: " + (emptyReference ? "reference" : "current") +
                        (emptyReference && emptyCurrent ? " and current" : "") + " list has no enabled scenes.");
                if (chronologyUnexpected)
                    Console.WriteLine("Review: reference capture time is later than this saved-file read.");
                var findings = rows.Where(r => r.Different || r.Warning).ToArray();
                foreach (var row in findings.Take(10))
                    Console.WriteLine("Scene: " + SafeText(row.ReferencePath) + " [" + SafeText(row.A) + "] -> " +
                        SafeText(row.ComparedPath) + " [" + SafeText(row.B) + "]" +
                        (string.IsNullOrEmpty(row.Issue) ? "" : "; " + SafeText(row.Issue)));
                if (findings.Length > 10)
                    Console.WriteLine((findings.Length - 10) + " more scene findings; use --format json for all findings.");
                Console.WriteLine("Scope: saved files only. Does not verify unsaved Editor state, the active profile, " +
                    "project identity, approval of the reference, or actual build contents.");
            }
            else
            {
                var report = new
                {
                    schema = 1, tool_version = Version,
                    status = pass ? "MATCH_WITHOUT_WARNINGS" : "REVIEW_REQUIRED",
                    scope = "Declared scene configuration only; not actual build certification.",
                    project_identity_verified = false,
                    current_snapshot_freshness_verified = false,
                    current_saved_configuration_read_this_run = freshSavedRead,
                    current_configuration_source = freshSavedRead ? "saved_project_read_this_run" : "snapshot_file",
                    project_path = project, profile_selector = selector, unity_version = unityVersion,
                    current_read_started_utc = readStartedUtc,
                    current_read_completed_utc = freshSavedRead ? (DateTimeOffset?)capturedUtc : null,
                    reference = Describe(a, original.CapturedUtc),
                    current = Describe(b, capturedUtc),
                    profile_identifier_changed = declared.ProfileIdentifierChanged,
                    list_source_changed = declared.SceneListSourceChanged,
                    profile_asset_path_changed = declared.ProfileAssetPathChanged,
                    declared_entry_sequence_changed = declared.DeclaredEntrySequenceChanged,
                    first_differing_entry = !declared.DeclaredEntrySequenceChanged ? null : new
                    {
                        list_index = firstDifference,
                        reference = firstDifference < a.Rows.Count ? DescribeRow(a.Rows[firstDifference]) : null,
                        current = firstDifference < b.Rows.Count ? DescribeRow(b.Rows[firstDifference]) : null
                    },
                    reference_has_no_enabled_scenes = emptyReference,
                    current_has_no_enabled_scenes = emptyCurrent,
                    current_capture_precedes_reference = chronologyUnexpected,
                    changed_scene_identities = drift,
                    scene_identities_with_warnings = warnings,
                    findings = rows.Where(r => r.Different || r.Warning).Select(r => new
                    {
                        key = r.Key, reference_path = r.ReferencePath, current_path = r.ComparedPath,
                        reference_state = r.A, current_state = r.B, changed = r.Different,
                        warning = r.Warning, message = r.Issue
                    }).ToArray()
                };
                Console.WriteLine(JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true }));
            }
            return pass ? 0 : 1;
        }

        // Escape input-derived control/format characters in text, just as the
        // JSON writer does. Paths and profile labels cannot forge terminal lines.
        private static string SafeText(string value)
        {
            if (string.IsNullOrEmpty(value)) return "(none)";
            var result = new StringBuilder();
            foreach (var rune in value.EnumerateRunes())
            {
                var category = Rune.GetUnicodeCategory(rune);
                if (category == UnicodeCategory.Control || category == UnicodeCategory.Format ||
                    category == UnicodeCategory.LineSeparator || category == UnicodeCategory.ParagraphSeparator)
                    result.Append(rune.IsBmp ? "\\u" : "\\U").Append(rune.Value.ToString(
                        rune.IsBmp ? "x4" : "x8", CultureInfo.InvariantCulture));
                else result.Append(rune.ToString());
            }
            return result.ToString();
        }

        private static string TextRow(HprSceneProfile profile, int index)
        {
            if (index >= profile.Rows.Count) return "(absent)";
            var row = profile.Rows[index];
            return SafeText(row.Path) + (row.Enabled ? " [enabled]" : " [disabled]");
        }

        private static int Error(Exception error, bool text)
        {
            if (text) Console.WriteLine("Scene Gate: INPUT ERROR — " + SafeText(error.Message));
            else Console.WriteLine(JsonSerializer.Serialize(new
            {
                schema = 1, tool_version = Version, status = "INVALID_INPUT_OR_READ_ERROR",
                error = error.GetType().Name, message = error.Message
            }));
            return 2;
        }

        private static int Capture(string project, string selector, string output)
        {
            try
            {
                string destination = SavedUnitySceneLists.NewOutputPath(project, output);
                var result = SavedUnitySceneLists.Capture(project, selector);
                var captured = DateTimeOffset.UtcNow;
                HprSceneBaseline.SaveNew(destination, result.Profile, captured);
                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    schema = 1, tool_version = Version,
                    status = "SAVED_PROJECT_SNAPSHOT_CREATED", unity_version = result.UnityVersion,
                    scope = "Explicit saved scene-list configuration and path metadata only. Not a Unity scan or build.",
                    profile = result.Profile.Id, source = result.Profile.Source,
                    declared_entries = result.Profile.Rows.Count, enabled_entries = result.Profile.EnabledCount,
                    missing_or_stale_entries = result.Profile.Rows.Count(r => r.Missing),
                    output = destination, captured_utc = captured
                }));
                return 0;
            }
            catch (Exception e) when (IsInputError(e)) { return Error(e, false); }
        }

        private static object Describe(HprSceneProfile p, DateTimeOffset capturedUtc) => new
        {
            id = p.Id, title = p.Title, asset_path = p.AssetPath, source = p.Source,
            captured_utc = capturedUtc, declared_entries = p.Rows.Count,
            enabled_entries = p.EnabledCount, first_enabled_scene = p.First
        };

        private static object DescribeRow(HprSceneRow row) => new
        {
            path = row.Path, guid = row.Guid, enabled = row.Enabled, missing = row.Missing,
            build_index = row.BuildIndex
        };
    }
}
