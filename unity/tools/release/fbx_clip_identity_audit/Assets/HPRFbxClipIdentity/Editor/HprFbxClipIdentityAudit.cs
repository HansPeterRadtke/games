#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEngine;

namespace HPR.FbxClipIdentity
{
    [Serializable]
    public sealed class FbxClipIdentityFinding
    {
        public string severity;
        public string rule;
        public string source;
        public string detail;
    }

    [Serializable]
    public sealed class FbxClipIdentityModel
    {
        public string path;
        public string status;
        public int modelClipCount;
        public int idEntries;
        public int clipIdEntries;
        public int configuredClipEntries;
        public int duplicateClipIds;
        public bool incomplete;
        public FbxClipIdentityFinding[] findings;
    }

    [Serializable]
    public sealed class FbxClipIdentityReport
    {
        public string unityVersion;
        public string status;
        public int modelsChecked;
        public int duplicateModels;
        public int definiteDuplicateIds;
        public bool incomplete;
        public string limitation;
        public FbxClipIdentityModel[] models;
    }

    /// <summary>Read-only, narrow importer metadata detector; NEVER rewrites .meta or FBX.</summary>
    public static class HprFbxClipIdentityAudit
    {
        public const int MaxModels = 300;
        public const int MaxMetadataBytes = 4194304;
        public const int MaxEntries = 10000;
        private static readonly Regex First = new Regex(@"^  - first:\s*$", RegexOptions.Compiled);
        private static readonly Regex SerializedId = new Regex(@"^      (\d+):\s*(-?\d+)\s*$", RegexOptions.Compiled);
        private static readonly Regex Second = new Regex(@"^    second:\s*(.*)$", RegexOptions.Compiled);

        private static FbxClipIdentityModel Incomplete(string assetPath, string rule, string why)
        {
            return new FbxClipIdentityModel
            {
                path = assetPath, status = "INCOMPLETE", incomplete = true,
                findings = new[] { new FbxClipIdentityFinding
                { severity = "ERROR", rule = rule, source = assetPath, detail = why } }
            };
        }

        // Unity also writes clipAnimations[].internalID: directly inside the
        // animations importer section. Checking internalIDToNameTable alone
        // misses the exact custom-clip collision reported by Unity users.
        // Unrecognized entries fail closed; this parser never edits metadata.
        private static bool InspectConfiguredClipIds(string assetPath, string yaml,
            FbxClipIdentityModel model, List<FbxClipIdentityFinding> findings)
        {
            bool section = false, active = false, inRow = false;
            bool hasId = false, malformed = false, foundSection = false;
            string id = "", name = "", take = "";
            var known = new Dictionary<string,string>(StringComparer.Ordinal);
            Action flush = () =>
            {
                if (!inRow) return;
                if (!hasId) malformed = true;
                else
                {
                    model.configuredClipEntries++;
                    string first;
                    if (known.TryGetValue(id, out first))
                    {
                        if (id == "0")
                        {
                            malformed = true; // zero may be a placeholder
                            if (findings.Count < 200)
                                findings.Add(new FbxClipIdentityFinding
                                { severity = "REVIEW", rule = "REPEATED_ZERO_CLIP_ID",
                                  source = assetPath, detail = "Multiple configured clips have local ID zero. " +
                                    "This may be a placeholder; verify Unity import results manually." });
                        }
                        else
                        {
                            model.duplicateClipIds++;
                            if (findings.Count < 200)
                                findings.Add(new FbxClipIdentityFinding
                                { severity = "DEFINITE", rule = "DUPLICATE_CONFIGURED_CLIP_INTERNAL_ID",
                                  source = assetPath, detail = "Configured AnimationClip internalID " + id +
                                    " repeats for '" + first + "' and '" + name +
                                    "' (take '" + take + "'). References may become ambiguous." });
                            else malformed = true;
                        }
                    }
                    else known.Add(id, name);
                }
                inRow = false; hasId = false; id = ""; name = ""; take = "";
            };
            foreach (string line in yaml.Replace("\r\n", "\n").Split('\n'))
            {
                if (!section)
                {
                    if (line == "    clipAnimations: []") { foundSection = true; break; }
                    if (line == "    clipAnimations:")
                    { section = true; foundSection = true; }
                    continue;
                }
                if (line.StartsWith("    ", StringComparison.Ordinal) &&
                    !line.StartsWith("      ", StringComparison.Ordinal) &&
                    !line.StartsWith("    - ", StringComparison.Ordinal) &&
                    line.Trim().Length > 0)
                { flush(); break; }
                if (line.StartsWith("    - ", StringComparison.Ordinal))
                {
                    flush(); inRow = true;
                    if (model.configuredClipEntries >= MaxEntries) { malformed = true; break; }
                    continue;
                }
                if (inRow && line.StartsWith("      ", StringComparison.Ordinal))
                {
                    string property = line.Trim();
                    if (property.StartsWith("internalID:", StringComparison.Ordinal))
                    {
                        string value = property.Substring("internalID:".Length).Trim();
                        long parsed;
                        if (!long.TryParse(value, out parsed) || hasId) malformed = true;
                        else { id = parsed.ToString(System.Globalization.CultureInfo.InvariantCulture); hasId = true; }
                    }
                    else if (property.StartsWith("name:", StringComparison.Ordinal))
                        name = property.Substring("name:".Length).Trim();
                    else if (property.StartsWith("takeName:", StringComparison.Ordinal))
                        take = property.Substring("takeName:".Length).Trim();
                }
            }
            flush();
            if (!foundSection || malformed)
            {
                if (findings.Count < 200)
                    findings.Add(new FbxClipIdentityFinding
                    { severity = "ERROR", rule = "CUSTOM_CLIP_TABLE_UNVERIFIED",
                      source = assetPath, detail = "Custom clip internalID metadata missing, ambiguous, " +
                        "or unsupported; verify this model in Unity before shipping." });
                return false;
            }
            return true;
        }

        public static FbxClipIdentityModel AnalyzeMetaText(string assetPath, string metadata)
        {
            if (string.IsNullOrEmpty(assetPath) || !assetPath.StartsWith("Assets/", StringComparison.Ordinal) ||
                assetPath.Contains("..") || !assetPath.EndsWith(".fbx", StringComparison.OrdinalIgnoreCase))
                return Incomplete(assetPath ?? "", "INVALID_SOURCE", "Expected an FBX asset under Assets.");
            if (string.IsNullOrEmpty(metadata) || Encoding.UTF8.GetByteCount(metadata) > MaxMetadataBytes ||
                !metadata.Contains("ModelImporter:") || !metadata.Contains("internalIDToNameTable:"))
                return Incomplete(assetPath, "UNREADABLE_META", "Missing/oversized or unexpected Unity ModelImporter metadata.");
            var found = new List<FbxClipIdentityFinding>();
            var model = new FbxClipIdentityModel { path = assetPath };
            bool inTable = false, tableFound = false, rowOpen = false, rowHasId = false;
            string rowKey = "", rowName = "";
            var clipIds = new Dictionary<string, string>(StringComparer.Ordinal);
            bool failed = false;
            Action flush = () =>
            {
                if (!rowOpen) return;
                if (!rowHasId) { failed = true; return; }
                model.idEntries++;
                if (rowKey.StartsWith("74:", StringComparison.Ordinal))
                {
                    model.clipIdEntries++;
                    string firstName;
                    if (clipIds.TryGetValue(rowKey, out firstName))
                    {
                        model.duplicateClipIds++;
                        if (found.Count < 200)
                            found.Add(new FbxClipIdentityFinding
                            {
                                severity = "DEFINITE", rule = "DUPLICATE_ANIMATION_CLIP_LOCAL_ID",
                                source = assetPath,
                                detail = "Clip local ID " + rowKey.Substring(3) +
                                    " appears for both '" + firstName + "' and '" + rowName +
                                    "'. Review importer naming/clip setup; do not edit IDs automatically."
                            });
                        else failed = true;
                    }
                    else clipIds.Add(rowKey, rowName);
                }
                rowOpen = false; rowHasId = false; rowKey = ""; rowName = "";
            };
            foreach (string line in metadata.Replace("\r\n", "\n").Split('\n'))
            {
                if (!inTable)
                {
                    if (line == "  internalIDToNameTable: []")
                    { tableFound = true; break; }
                    if (line == "  internalIDToNameTable:")
                    { inTable = true; tableFound = true; }
                    continue;
                }
                // Another top-level ModelImporter property ends the ID table.
                if (line.StartsWith("  ", StringComparison.Ordinal) &&
                    !line.StartsWith("    ", StringComparison.Ordinal) &&
                    !line.StartsWith("  - ", StringComparison.Ordinal) &&
                    line.Trim().Length != 0)
                { flush(); break; }
                if (First.IsMatch(line))
                {
                    flush(); rowOpen = true;
                    if (model.idEntries >= MaxEntries) { failed = true; break; }
                    continue;
                }
                var id = SerializedId.Match(line);
                if (id.Success && rowOpen)
                {
                    if (rowHasId) failed = true;
                    rowKey = id.Groups[1].Value + ":" + id.Groups[2].Value;
                    rowHasId = true;
                    continue;
                }
                var second = Second.Match(line);
                if (second.Success && rowOpen) { rowName = second.Groups[1].Value; continue; }
                if (line.Trim().Length > 0 && !rowOpen) failed = true;
            }
            flush();
            if (!InspectConfiguredClipIds(assetPath, metadata, model, found)) failed = true;
            if (!tableFound || failed || model.idEntries > MaxEntries)
            {
                model.incomplete = true;
                found.Add(new FbxClipIdentityFinding
                { severity = "ERROR", rule = "METADATA_TABLE_UNSUPPORTED_OR_TRUNCATED", source = assetPath,
                  detail = "The internal ID table is incomplete or uses an unrecognized layout. Review this asset manually." });
            }
            model.findings = found.ToArray();
            model.status = model.incomplete ? "INCOMPLETE" : model.duplicateClipIds > 0 ?
                "DUPLICATE_CLIP_IDS" : "NO_DUPLICATE_CLIP_IDS_IN_TABLE";
            return model;
        }

        public static FbxClipIdentityModel ScanOne(string assetPath)
        {
            if (string.IsNullOrEmpty(assetPath) || !assetPath.StartsWith("Assets/", StringComparison.Ordinal) ||
                !assetPath.EndsWith(".fbx", StringComparison.OrdinalIgnoreCase) ||
                assetPath.Contains(".."))
                return Incomplete(assetPath ?? "", "INVALID_SOURCE", "Choose a real FBX model under Assets.");
            if (!(AssetImporter.GetAtPath(assetPath) is ModelImporter))
                return Incomplete(assetPath, "NO_MODEL_IMPORTER", "Unity did not recognize the selected FBX as a model.");
            try
            {
                string project = Directory.GetParent(Application.dataPath).FullName;
                string target = Path.GetFullPath(Path.Combine(project, assetPath + ".meta"));
                if (!target.StartsWith(project + Path.DirectorySeparatorChar, StringComparison.Ordinal) ||
                    !File.Exists(target) || new FileInfo(target).Length > MaxMetadataBytes)
                    return Incomplete(assetPath, "MISSING_META", "Missing or excessive Unity importer metadata.");
                var result = AnalyzeMetaText(assetPath, File.ReadAllText(target));
                result.modelClipCount = AssetDatabase.LoadAllAssetsAtPath(assetPath)
                    .OfType<AnimationClip>().Count(clip => !clip.name.StartsWith("__preview__", StringComparison.Ordinal));
                return result;
            }
            catch (Exception ex)
            { return Incomplete(assetPath, "READ_FAILURE", ex.GetType().Name + ": " + ex.Message); }
        }

        // One-file shortcut for first-time users and a bundled, original
        // animated FBX example. Does not import or modify the chosen model.
        public const string ExampleFbxPath = "Assets/HPRFbxClipIdentity/Samples/OriginalMotion.fbx";
        // These are original first-party training examples shipped by the
        // related HPR Source Take Visibility tool. They are NOT buyer models.
        // Keep exact path comparisons; never hide arbitrary customer assets.
        private const string RelatedSourceTakeHealthyExample =
            "Assets/HPRFbxSourceTakes/Samples/HPRTwoTakeCube.fbx";
        private const string RelatedSourceTakeMissingExample =
            "Assets/HPRFbxSourceTakes/Samples/HPRTwoTakeCustomMissing.fbx";

        public static FbxClipIdentityReport ScanSingle(string assetPath)
        {
            var model = ScanOne(assetPath);
            var report = new FbxClipIdentityReport
            {
                unityVersion = Application.unityVersion,
                modelsChecked = 1,
                models = new[] { model },
                incomplete = model.incomplete,
                definiteDuplicateIds = model.duplicateClipIds,
                duplicateModels = model.duplicateClipIds > 0 ? 1 : 0,
                limitation = "Read-only selected-model preflight. This checks only the current " +
                    "stored ModelImporter ID tables. It cannot validate future reimports " +
                    "or repair a source FBX and never modifies buyer assets."
            };
            report.status = Classify(report);
            return report;
        }

        public static FbxClipIdentityReport ScanAssets(Func<int, int, bool> cancelled = null,
            int maxModels = MaxModels)
        {
            if (maxModels < 1 || maxModels > MaxModels)
                throw new ArgumentOutOfRangeException("maxModels");
            var report = new FbxClipIdentityReport
            {
                unityVersion = Application.unityVersion,
                limitation = "Checks ModelImporter class-74 and configured clipAnimations IDs in your " +
                    "project's FBX assets, excluding this and the related HPR Source Take tool's " +
                "exact first-party sample FBX files. " +
                    "Run the demo check separately. This does not prove missing/undetected source clips, " +
                    "future reimport stability or exact Unity hash generation. " +
                    "No automatic asset or importer changes."
            };
            var rows = new List<FbxClipIdentityModel>();
            string[] assets = AssetDatabase.GetAllAssetPaths().Where(p =>
                p.StartsWith("Assets/", StringComparison.Ordinal) &&
                p.EndsWith(".fbx", StringComparison.OrdinalIgnoreCase) &&
                // The bundled first-run demo must not make an empty customer
                // project appear to have passed a real project-wide audit.
                // Users can still inspect the demo explicitly via ScanSingle.
                !string.Equals(p, ExampleFbxPath, StringComparison.OrdinalIgnoreCase) &&
                !string.Equals(p, RelatedSourceTakeHealthyExample, StringComparison.OrdinalIgnoreCase) &&
                !string.Equals(p, RelatedSourceTakeMissingExample, StringComparison.OrdinalIgnoreCase))
                .Distinct(StringComparer.Ordinal).OrderBy(p => p, StringComparer.Ordinal).ToArray();
            if (assets.Length > maxModels) report.incomplete = true;
            int limit = Math.Min(assets.Length, maxModels);
            for (int i = 0; i < limit; i++)
            {
                if (cancelled != null && cancelled(i, limit)) { report.incomplete = true; break; }
                var row = ScanOne(assets[i]);
                rows.Add(row);
                report.modelsChecked++;
                if (row.duplicateClipIds > 0) report.duplicateModels++;
                report.definiteDuplicateIds += row.duplicateClipIds;
                if (row.incomplete) report.incomplete = true;
            }
            report.models = rows.ToArray();
            report.status = Classify(report);
            return report;
        }

        public static string Classify(FbxClipIdentityReport report)
        {
            if (report == null || report.incomplete || report.models == null ||
                report.modelsChecked != report.models.Length)
                return "INCOMPLETE";
            if (report.modelsChecked == 0)
                return "NO_FBX_MODELS_SCANNED";
            if (report.definiteDuplicateIds > 0)
                return "DUPLICATE_IDS_DETECTED";
            if (report.models.All(model => model != null && model.modelClipCount == 0))
                return "NO_ANIMATION_CLIPS_IN_CHECKED_MODELS";
            return "NO_DUPLICATE_IDS_IN_CHECKED_MODELS";
        }

        public static void ExportNew(FbxClipIdentityReport report, string absolutePath)
        {
            if (report == null || string.IsNullOrWhiteSpace(absolutePath) || !Path.IsPathRooted(absolutePath))
                throw new ArgumentException("A report and an absolute output path are required.");
            using (var stream = new FileStream(absolutePath, FileMode.CreateNew, FileAccess.Write, FileShare.None))
            using (var writer = new StreamWriter(stream, new UTF8Encoding(false)))
                writer.Write(JsonUtility.ToJson(report, true));
        }
    }
}
#endif
