#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using UnityEngine;

namespace HPR.ArchivePreflight
{
    [Serializable]
    public sealed class HprArchiveCoexistencePreview
    {
        public int schemaVersion = 1;
        public string status;
        public bool incomplete;
        public string limitation;
        public int firstArchiveAssets;
        public int secondArchiveAssets;
        public int guidCollisions;
        public int pathCollisions;
        public int caseOnlyPathCollisions;
        public int overwriteRisks;
        public int identicalSharedAssets;
        public HprArchiveDifference[] findings;
    }

    /// <summary>
    /// Comparison of *independent* release archives expected to be installed
    /// together. Do not use upgrade semantics to validate coexistence: a GUID
    /// that moves between packages is a potential collision, not a safe move.
    /// No assets are imported, rewritten, remapped or extracted.
    /// </summary>
    public static class HprArchiveCoexistence
    {
        private static readonly Regex GuidRegex = new Regex("^[0-9a-f]{32}$", RegexOptions.CultureInvariant);
        private const int MaxAssets = 7500;

        // Inspect() enforces these rules, but enforce them again here because
        // other Editor tools can call public Compare with serialized objects.
        private static bool Valid(HprArchiveInspection report)
        {
            if (report == null || report.status != "READABLE_STRICT_ARCHIVE" ||
                report.assets == null || report.pathsChecked != report.assets.Length ||
                report.pathsChecked < 1 || report.pathsChecked > MaxAssets) return false;
            var byGuid = new HashSet<string>(StringComparer.Ordinal);
            var byPath = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach (var item in report.assets)
                if (item == null || string.IsNullOrEmpty(item.assetPath) ||
                    !item.assetPath.StartsWith("Assets/",StringComparison.Ordinal) ||
                    item.assetPath.Split('/').Any(segment => segment == "." || segment == ".." ||
                        segment.Length == 0) ||
                    item.assetPath.Contains("\\") || item.assetPath.Contains("//") ||
                    item.assetPath.Any(char.IsControl) ||
                    string.IsNullOrEmpty(item.guid) || !GuidRegex.IsMatch(item.guid) ||
                    string.IsNullOrEmpty(item.importerHash) || item.importerHash.Length != 64 ||
                    (item.isFolder && !string.IsNullOrEmpty(item.sourceHash)) ||
                    (!item.isFolder && (item.sourceHash == null || item.sourceHash.Length != 64)) ||
                    !byGuid.Add(item.guid) || !byPath.Add(item.assetPath)) return false;
            return true;
        }

        public static HprArchiveCoexistencePreview Compare(
            HprArchiveInspection first, HprArchiveInspection second, int maxFindings = 1200)
        {
            if (maxFindings < 1) throw new ArgumentOutOfRangeException("maxFindings");
            var result = new HprArchiveCoexistencePreview
            {
                status = "INCOMPLETE", incomplete = true, findings = new HprArchiveDifference[0],
                limitation = "Only GUID, path, source and importer overlaps between two valid classic " +
                    ".unitypackage archives are checked. This does not inspect assets already in your " +
                    "project, APIs, serialized subasset fileIDs, runtime dependencies, license or actual " +
                    "post-import behavior. Test import into a disposable buyer project."
            };
            if (!Valid(first) || !Valid(second)) return result;
            result.firstArchiveAssets = first.pathsChecked;
            result.secondArchiveAssets = second.pathsChecked;
            var secondByGuid = second.assets.ToDictionary(x => x.guid, x => x, StringComparer.Ordinal);
            var secondByPath = second.assets.ToDictionary(x => x.assetPath, x => x, StringComparer.Ordinal);
            var secondByCaseFoldedPath = second.assets.ToDictionary(x => x.assetPath,
                x => x, StringComparer.OrdinalIgnoreCase);
            var findings = new List<HprArchiveDifference>();
            Action<string, HprArchivedAsset, HprArchivedAsset, string> add = (kind, a, b, advice) =>
            {
                if (findings.Count < maxFindings)
                    findings.Add(new HprArchiveDifference { kind = kind,
                        before = a.assetPath + " | " + a.guid,
                        after = b.assetPath + " | " + b.guid,
                        guidance = advice });
                else result.incomplete = true;
            };
            result.incomplete = false;
            foreach (var a in first.assets.OrderBy(x => x.assetPath, StringComparer.Ordinal))
            {
                HprArchivedAsset guidMatch;
                if (secondByGuid.TryGetValue(a.guid, out guidMatch))
                {
                    if (a.assetPath != guidMatch.assetPath)
                    {
                        result.guidCollisions++;
                        add("GUID_REUSED_AT_DIFFERENT_PATH", a, guidMatch,
                            "These independent packages reuse the same GUID for different paths. " +
                            "Unity may conflate assets; inspect in an isolated combined-buyer project.");
                    }
                    else if (a.isFolder != guidMatch.isFolder ||
                             a.sourceHash != guidMatch.sourceHash ||
                             a.importerHash != guidMatch.importerHash)
                    {
                        result.overwriteRisks++;
                        add("SHARED_GUID_PATH_DIFFERENT_BYTES", a, guidMatch,
                            "Both independent packages contain the same identity/path with different " +
                            "bytes or importer settings. One import may overwrite the other.");
                    }
                    else result.identicalSharedAssets++;
                }
                HprArchivedAsset pathMatch;
                if (secondByPath.TryGetValue(a.assetPath, out pathMatch) && a.guid != pathMatch.guid)
                {
                    result.pathCollisions++;
                    add("PATH_REUSED_WITH_DIFFERENT_GUID", a, pathMatch,
                        "Two independent packages claim the same path with different GUIDs. " +
                        "One may overwrite or invalidate the other's references.");
                }
                else if (!secondByPath.ContainsKey(a.assetPath))
                {
                    HprArchivedAsset folded;
                    if (secondByCaseFoldedPath.TryGetValue(a.assetPath, out folded) &&
                        a.guid != folded.guid)
                    {
                        result.caseOnlyPathCollisions++;
                        add("CASE_ONLY_ASSET_PATH_COLLISION", a, folded,
                            "Unity asset lookup paths are case-insensitive. Distinct GUIDs under names " +
                            "that differ only in letter case can collide on import or lookup.");
                    }
                }
            }
            result.findings = findings.ToArray();
            result.status = result.incomplete ? "INCOMPLETE" :
                (result.guidCollisions > 0 || result.pathCollisions > 0 ||
                 result.caseOnlyPathCollisions > 0 || result.overwriteRisks > 0) ?
                "REVIEW_INDEPENDENT_PACKAGE_COLLISIONS" : "NO_OVERLAP_CONFLICTS_IN_CHECKED_ARCHIVES";
            return result;
        }

        public static void ExportNew(HprArchiveCoexistencePreview report, string fullPath)
        {
            if (report == null || string.IsNullOrWhiteSpace(fullPath) || !Path.IsPathRooted(fullPath))
                throw new ArgumentException("Valid preview and an absolute path are required.");
            using (var file = new FileStream(fullPath, FileMode.CreateNew, FileAccess.Write, FileShare.None))
            using (var writer = new StreamWriter(file, new UTF8Encoding(false)))
                writer.Write(JsonUtility.ToJson(report, true));
        }
    }
}
#endif
