#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using UnityEngine;

namespace HPR.PackageBoundary
{
    [Serializable]
    public sealed class BoundaryIdentity
    {
        public string assetPath;
        public string guid;
    }

    [Serializable]
    public sealed class BoundaryUpgradeFinding
    {
        public string kind;
        public string before;
        public string after;
        public string guidance;
    }

    [Serializable]
    public sealed class BoundaryUpgradeReport
    {
        public int schemaVersion;
        public string packageRoot;
        public string status;
        public bool incomplete;
        public int oldAssets;
        public int newAssets;
        public int replacedGuids;
        public int removedAssets;
        public int movedPaths;
        public int addedAssets;
        public string limitation;
        public BoundaryUpgradeFinding[] findings;
    }

    /// <summary>
    /// Pure, deterministic, read-only comparison of snapshot GUID/path identity.
    /// Not a proof of serialized reference or code/runtime compatibility.
    /// </summary>
    public static class HprBoundaryUpgradeReview
    {
        public const int MaxFindings = 1500;
        private static readonly Regex GuidPattern =
            new Regex("^[0-9a-f]{32}$", RegexOptions.CultureInvariant);

        private static bool Valid(BoundaryReport report)
        {
            if (report == null || report.schemaVersion != 1 || report.incomplete ||
                report.status == "INCOMPLETE" || string.IsNullOrWhiteSpace(report.root) ||
                report.identities == null || report.assetsChecked < 1 ||
                report.identities.Length != report.assetsChecked || report.findings == null)
                return false;
            var uniquePaths = new HashSet<string>(StringComparer.Ordinal);
            var uniqueGuids = new HashSet<string>(StringComparer.Ordinal);
            foreach (var identity in report.identities)
            {
                if (identity == null || string.IsNullOrEmpty(identity.assetPath) ||
                    string.IsNullOrEmpty(identity.guid) ||
                    !identity.assetPath.StartsWith(report.root + "/", StringComparison.Ordinal) ||
                    identity.assetPath.Contains("/../") || identity.assetPath.Contains("/./") ||
                    !GuidPattern.IsMatch(identity.guid) ||
                    !uniquePaths.Add(identity.assetPath) || !uniqueGuids.Add(identity.guid))
                    return false;
            }
            return true;
        }

        public static BoundaryUpgradeReport Compare(BoundaryReport previous,
            BoundaryReport current, int maxFindings = MaxFindings)
        {
            if (maxFindings < 1)
                throw new ArgumentOutOfRangeException("maxFindings");
            var result = new BoundaryUpgradeReport
            {
                schemaVersion = 1,
                packageRoot = current == null ? "" : current.root,
                oldAssets = previous == null ? 0 : previous.assetsChecked,
                newAssets = current == null ? 0 : current.assetsChecked,
                limitation = "Only stable GUID/path identities are compared. Same GUID does not prove " +
                    "binary/API compatibility, and folder GUIDs, dynamic loading, serialized links " +
                    "and dependent projects require independent import/upgrade tests."
            };
            var issues = new List<BoundaryUpgradeFinding>();
            if (!Valid(previous) || !Valid(current) ||
                !string.Equals(previous.root, current.root, StringComparison.Ordinal))
            {
                result.incomplete = true;
                result.status = "INCOMPLETE";
                result.findings = new BoundaryUpgradeFinding[0];
                return result;
            }
            var oldByPath = previous.identities.ToDictionary(x => x.assetPath,
                x => x, StringComparer.Ordinal);
            var oldByGuid = previous.identities.ToDictionary(x => x.guid,
                x => x, StringComparer.Ordinal);
            var nowByPath = current.identities.ToDictionary(x => x.assetPath,
                x => x, StringComparer.Ordinal);
            var nowByGuid = current.identities.ToDictionary(x => x.guid,
                x => x, StringComparer.Ordinal);

            Action<string, string, string, string> add = (kind, before, after, guidance) =>
            {
                if (issues.Count < maxFindings)
                    issues.Add(new BoundaryUpgradeFinding
                    { kind = kind, before = before, after = after, guidance = guidance });
                else
                    result.incomplete = true;
            };
            foreach (var old in previous.identities.OrderBy(x => x.assetPath, StringComparer.Ordinal))
            {
                BoundaryIdentity currentAtPath;
                if (nowByPath.TryGetValue(old.assetPath, out currentAtPath))
                {
                    if (currentAtPath.guid != old.guid)
                    {
                        result.replacedGuids++;
                        add("GUID_REPLACED_AT_PATH", old.assetPath + " | " + old.guid,
                            currentAtPath.assetPath + " | " + currentAtPath.guid,
                            "Potentially breaks external serialized references; restore original GUID or prove migrations in buyer projects.");
                    }
                }
                else
                {
                    BoundaryIdentity moved;
                    if (nowByGuid.TryGetValue(old.guid, out moved))
                    {
                        result.movedPaths++;
                        add("PATH_MOVED_WITH_SAME_GUID", old.assetPath,
                            moved.assetPath, "Serialized references may survive; inspect path-based loading and public code paths.");
                    }
                    else
                    {
                        result.removedAssets++;
                        add("ASSET_REMOVED", old.assetPath + " | " + old.guid, "",
                            "Determine whether buyers depend on this GUID and test upgrading an existing populated project.");
                    }
                }
            }
            foreach (var now in current.identities.OrderBy(x => x.assetPath, StringComparer.Ordinal))
                if (!oldByPath.ContainsKey(now.assetPath) && !oldByGuid.ContainsKey(now.guid))
                {
                    result.addedAssets++;
                    add("ASSET_ADDED", "", now.assetPath + " | " + now.guid,
                        "New asset; verify licensing, scope and clean-import behavior.");
                }
            result.findings = issues.ToArray();
            result.status = result.incomplete ? "INCOMPLETE" :
                (result.replacedGuids > 0 || result.removedAssets > 0) ? "REVIEW_SERIALIZED_IDENTITY_BREAKAGE" :
                result.movedPaths > 0 ? "REVIEW_MOVED_PATHS" :
                result.addedAssets > 0 ? "ADDITIONS_ONLY" : "UNCHANGED_IDENTITIES";
            return result;
        }

        public static void ExportNewJson(BoundaryUpgradeReport report, string fullPath)
        {
            if (report == null || string.IsNullOrWhiteSpace(fullPath) || !Path.IsPathRooted(fullPath))
                throw new ArgumentException("Report and absolute output path required.");
            using (var stream = new FileStream(fullPath, FileMode.CreateNew, FileAccess.Write, FileShare.None))
            using (var writer = new StreamWriter(stream, new UTF8Encoding(false)))
                writer.Write(JsonUtility.ToJson(report, true));
        }
    }
}
#endif
