using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using HPR.BuildSceneMatrix;

namespace HPR.BuildSceneGate
{
    internal static class Program
    {
        private const string Version = "0.1.0";
        private const string Usage =
            "HPR Scene Gate — read-only declared scene configuration comparison\n" +
            "Usage: dotnet HprSceneGate.dll compare REFERENCE.hpr-scenes CURRENT.hpr-scenes\n" +
            "       dotnet HprSceneGate.dll capture PROJECT global|Assets/Profile.asset OUTPUT.hpr-scenes\n" +
            "Compare writes only JSON; capture writes one new snapshot outside the project. Never starts Unity.\n" +
            "Compare exit 0: same declared configuration, no warnings. Capture exit 0: snapshot created.\n" +
            "Exit 1: configuration differs or diagnostic warnings exist.\n" +
            "Exit 2: invalid input, arguments or read error.\n" +
            "Choose snapshots from the intended project and freshly scan the current configuration.\n" +
            "This does not certify the actual contents or success of a build.";

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
            if (args.Length == 4 && args[0] == "capture")
                return Capture(args[1], args[2], args[3]);
            if (args.Length != 3 || args[0] != "compare")
            {
                Console.Error.WriteLine(Usage);
                return 2;
            }

            try
            {
                HprSceneBaseline original = HprSceneBaseline.Load(args[1]);
                HprSceneBaseline current = HprSceneBaseline.Load(args[2]);
                HprSceneProfile a = original.Profile, b = current.Profile;
                var rows = HprSceneMatrix.Compare(a, b);
                var declared = HprSceneMatrix.CompareDeclaredLists(a, b);
                int firstDifference = declared.FirstDifferingEntryIndex;
                bool emptyReference = a.EnabledCount == 0;
                bool emptyCurrent = b.EnabledCount == 0;
                bool chronologyUnexpected = current.CapturedUtc < original.CapturedUtc;
                int drift = rows.Count(r => r.Different);
                int warnings = rows.Count(r => r.Warning);
                bool pass = !declared.ProfileIdentifierChanged && !declared.SceneListSourceChanged &&
                    !declared.ProfileAssetPathChanged && !declared.DeclaredEntrySequenceChanged &&
                    !emptyReference && !emptyCurrent && !chronologyUnexpected &&
                    drift == 0 && warnings == 0;
                var report = new
                {
                    schema = 1,
                    tool_version = Version,
                    status = pass ? "MATCH_WITHOUT_WARNINGS" : "REVIEW_REQUIRED",
                    scope = "Declared scene configuration only; not actual build certification.",
                    project_identity_verified = false,
                    current_snapshot_freshness_verified = false,
                    reference = Describe(original),
                    current = Describe(current),
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
                        key = r.Key,
                        reference_path = r.ReferencePath,
                        current_path = r.ComparedPath,
                        reference_state = r.A,
                        current_state = r.B,
                        changed = r.Different,
                        warning = r.Warning,
                        message = r.Issue
                    }).ToArray()
                };
                Console.WriteLine(JsonSerializer.Serialize(report, new JsonSerializerOptions
                {
                    WriteIndented = true
                }));
                return pass ? 0 : 1;
            }
            catch (Exception e) when (e is IOException || e is InvalidDataException ||
                e is ArgumentException || e is UnauthorizedAccessException ||
                e is NotSupportedException || e is InvalidOperationException)
            {
                // JSON-escaped input-derived error messages cannot inject control
                // sequences into a terminal or break the structured error receipt.
                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    schema = 1,
                    tool_version = Version,
                    status = "INVALID_INPUT_OR_READ_ERROR",
                    error = e.GetType().Name,
                    message = e.Message
                }));
                return 2;
            }
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
                    status = "SAVED_PROJECT_SNAPSHOT_CREATED",
                    unity_version = result.UnityVersion,
                    scope = "Explicit saved scene-list configuration and path metadata only. Not a Unity scan or build.",
                    profile = result.Profile.Id,
                    source = result.Profile.Source,
                    declared_entries = result.Profile.Rows.Count,
                    enabled_entries = result.Profile.EnabledCount,
                    missing_or_stale_entries = result.Profile.Rows.Count(r => r.Missing),
                    output = destination,
                    captured_utc = captured
                }));
                return 0;
            }
            catch (Exception e) when (e is IOException || e is InvalidDataException ||
                e is ArgumentException || e is UnauthorizedAccessException ||
                e is NotSupportedException || e is InvalidOperationException)
            {
                Console.WriteLine(JsonSerializer.Serialize(new
                {
                    schema = 1, tool_version = Version, status = "INVALID_INPUT_OR_READ_ERROR",
                    error = e.GetType().Name, message = e.Message
                }));
                return 2;
            }
        }

        private static object Describe(HprSceneBaseline snapshot)
        {
            HprSceneProfile p = snapshot.Profile;
            return new
            {
                id = p.Id,
                title = p.Title,
                asset_path = p.AssetPath,
                source = p.Source,
                captured_utc = snapshot.CapturedUtc,
                declared_entries = p.Rows.Count,
                enabled_entries = p.EnabledCount,
                first_enabled_scene = p.First
            };
        }

        private static object DescribeRow(HprSceneRow row) => new
        {
            path = row.Path, guid = row.Guid, enabled = row.Enabled, missing = row.Missing,
            build_index = row.BuildIndex
        };

    }
}
