#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using UnityEditor;
using UnityEngine;

namespace HPR.FbxSourceTakeVisibility
{
    [Serializable]
    public sealed class SourceTakeModelResult
    {
        public string assetPath;
        public string status;
        public int sourceTakeCount;
        public int customClipCount;
        public int missingSourceTakeCount;
        public bool customClipList;
        public bool incomplete;
        public string[] sourceTakes;
        public string[] missingSourceTakes;
        public string[] customTakeNames;
        public string detail;
    }

    [Serializable]
    public sealed class SourceTakeScanReport
    {
        public string unityVersion;
        public string status;
        public int modelsChecked;
        public int modelsWithMissingSourceTakes;
        public int sourceTakesMissing;
        public bool incomplete;
        public string limitation;
        public SourceTakeModelResult[] models;
    }

    /// <summary>
    /// Read-only comparison of original FBX source take names against a user's
    /// customized Unity ModelImporter clip definitions. Never calls setter,
    /// SaveAndReimport or any AssetDatabase mutation API.
    /// </summary>
    public static class HprFbxSourceTakeAudit
    {
        public const string ExampleFbxPath = "Assets/HPRFbxSourceTakes/Samples/HPRTwoTakeCube.fbx";
        public const string ExampleOmittedTakeFbxPath = "Assets/HPRFbxSourceTakes/Samples/HPRTwoTakeCustomMissing.fbx";
        public const int MaxModels = 300;
        public const int MaxTakesPerModel = 2048;
        private const int MaxPrintedTakeNames = 80;
        private const string Scope = "This is a read-only source-take coverage preview, not an import repair. " +
            "Source takes not listed in customized clip settings may require adding them manually in " +
            "the model Animation tab. It does not inspect all animation events, clip timing, " +
            "references, saved poses or any future reimport. Your actual import result can vary.";

        private static SourceTakeModelResult Uncertain(string path, string status, string detail)
        {
            return new SourceTakeModelResult
            {
                assetPath = path ?? "", status = status, incomplete = true,
                detail = detail, sourceTakes = new string[0], customTakeNames = new string[0],
                missingSourceTakes = new string[0]
            };
        }

        private static bool ValidTakeName(string name)
        {
            return !string.IsNullOrWhiteSpace(name) && name.Length <= 250 &&
                !name.Any(char.IsControl);
        }

        /// <summary>
        /// Testable comparison logic. Multiple configured clips may legitimately
        /// use the SAME source take when an FBX timeline is split by frame.
        /// The displayed user-facing clip name is NOT the source take key.
        /// </summary>
        public static SourceTakeModelResult Compare(string assetPath,
            IEnumerable<string> sourceTakeNames, IEnumerable<string> customClipTakeNames,
            bool isCustomized, bool animationImportEnabled = true)
        {
            var source = sourceTakeNames == null ? null : sourceTakeNames.ToArray();
            var customized = customClipTakeNames == null ? null : customClipTakeNames.ToArray();
            if (source == null || customized == null ||
                source.Length > MaxTakesPerModel || customized.Length > MaxTakesPerModel ||
                source.Any(x => !ValidTakeName(x)) || customized.Any(x => !ValidTakeName(x)))
                return Uncertain(assetPath, "INCOMPLETE", "Importer take names were missing, invalid, or too numerous to check.");
            var result = new SourceTakeModelResult
            {
                assetPath = assetPath ?? "", sourceTakeCount = source.Length,
                customClipCount = customized.Length, customClipList = isCustomized,
                sourceTakes = source.Length <= MaxPrintedTakeNames ? source : source.Take(MaxPrintedTakeNames).ToArray(),
                customTakeNames = customized.Length <= MaxPrintedTakeNames ? customized : customized.Take(MaxPrintedTakeNames).ToArray(),
                missingSourceTakes = new string[0]
            };
            if (!animationImportEnabled)
            {
                result.status = "ANIMATION_IMPORT_DISABLED";
                result.detail = "ModelImporter animation importing is disabled; no take visibility verdict applies.";
                return result;
            }
            if (source.Length == 0)
            {
                result.status = "NO_SOURCE_TAKES";
                result.detail = "Unity reports no source takes. Do not interpret this as a successful animation check.";
                return result;
            }
            var uniqueSource = new HashSet<string>(StringComparer.Ordinal);
            if (source.Any(t => !uniqueSource.Add(t)))
                return Uncertain(assetPath, "INCOMPLETE", "Source take names are repeated, so this comparison is ambiguous.");
            if (!isCustomized)
            {
                if (customized.Length != 0)
                    return Uncertain(assetPath, "INCOMPLETE", "An automatic import was supplied with unexpected custom take entries.");
                result.status = "DEFAULT_SOURCE_TAKES_ACTIVE";
                result.detail = "No customized clip list; Unity can use original source takes automatically.";
                return result;
            }
            if (customized.Length == 0)
                return Uncertain(assetPath, "INCOMPLETE", "A customized clip list was declared but contains no clips.");
            var included = new HashSet<string>(customized, StringComparer.Ordinal);
            var missing = source.Where(x => !included.Contains(x)).ToArray();
            result.missingSourceTakeCount = missing.Length;
            // A full count remains available even when output is capped.
            result.missingSourceTakes = missing.Take(MaxPrintedTakeNames).ToArray();
            if (missing.Length > MaxPrintedTakeNames)
            {
                result.status = "INCOMPLETE"; result.incomplete = true;
                result.detail = "More source takes are missing than can be displayed safely. Review the model manually.";
            }
            else if (missing.Length > 0)
            {
                result.status = "SOURCE_TAKES_NOT_IN_CUSTOM_LIST";
                result.detail = "One or more FBX source takes are not referenced by the customized " +
                    "clip list. Check the model Animation tab and manually add any desired take.";
            }
            else
            {
                result.status = "ALL_SOURCE_TAKE_NAMES_REFERENCED";
                result.detail = "All source take names occur in the custom clip list. This does not validate clips or timing.";
            }
            return result;
        }

        public static SourceTakeModelResult ScanOne(string path)
        {
            if (string.IsNullOrEmpty(path) || !path.StartsWith("Assets/", StringComparison.Ordinal) ||
                !path.EndsWith(".fbx", StringComparison.OrdinalIgnoreCase) ||
                path.Split('/').Any(p => p.Length == 0 || p == "." || p == "..") ||
                path.Contains("\\") || path.Any(char.IsControl))
                return Uncertain(path, "INCOMPLETE", "Select an FBX model asset under Assets.");
            try
            {
                var importer = AssetImporter.GetAtPath(path) as ModelImporter;
                if (importer == null)
                    return Uncertain(path, "INCOMPLETE", "Unity has no ModelImporter for this FBX asset.");
                ModelImporterClipAnimation[] source = importer.defaultClipAnimations;
                ModelImporterClipAnimation[] customized = importer.clipAnimations;
                if (source == null || customized == null || source.Any(c => c == null) ||
                    customized.Any(c => c == null))
                    return Uncertain(path, "INCOMPLETE", "Unity returned an unsupported clip array.");
                // ModelImporter.clipAnimations is empty until the user customizes
                // the imported clips; comparing both arrays without this check
                // would falsely warn on every default FBX model.
                return Compare(path, source.Select(c => c.takeName),
                    customized.Select(c => c.takeName), customized.Length > 0,
                    importer.importAnimation);
            }
            catch (Exception error)
            { return Uncertain(path, "INCOMPLETE", "Importer read failed: " + error.GetType().Name); }
        }

        public static SourceTakeScanReport ScanSingle(string assetPath)
        {
            var model = ScanOne(assetPath);
            var result = new SourceTakeScanReport
            {
                unityVersion = Application.unityVersion, modelsChecked = 1,
                modelsWithMissingSourceTakes = model.missingSourceTakeCount > 0 ? 1 : 0,
                sourceTakesMissing = model.missingSourceTakeCount,
                incomplete = model.incomplete, models = new[] {model}, limitation = Scope
            };
            result.status = Classify(result);
            return result;
        }

        public static SourceTakeScanReport ScanAssets(Func<int,int,bool> cancelled = null,
            int limit = MaxModels)
        {
            if (limit < 1 || limit > MaxModels)
                throw new ArgumentOutOfRangeException("limit");
            var result = new SourceTakeScanReport
            { unityVersion = Application.unityVersion, limitation = Scope };
            var all = AssetDatabase.GetAllAssetPaths()
                .Where(p => p.StartsWith("Assets/", StringComparison.Ordinal) &&
                    p.EndsWith(".fbx", StringComparison.OrdinalIgnoreCase) &&
                    !string.Equals(p, ExampleFbxPath, StringComparison.OrdinalIgnoreCase) &&
                    !string.Equals(p, ExampleOmittedTakeFbxPath, StringComparison.OrdinalIgnoreCase))
                .Distinct(StringComparer.OrdinalIgnoreCase)
                .OrderBy(p => p, StringComparer.Ordinal).ToArray();
            var models = new List<SourceTakeModelResult>();
            if (all.Length > limit) result.incomplete = true;
            for (int i = 0; i < Math.Min(all.Length,limit); i++)
            {
                if (cancelled != null && cancelled(i,Math.Min(all.Length,limit)))
                { result.incomplete = true; break; }
                var model = ScanOne(all[i]);
                models.Add(model);
                result.modelsChecked++;
                if (model.incomplete) result.incomplete = true;
                if (model.missingSourceTakeCount > 0)
                { result.modelsWithMissingSourceTakes++; result.sourceTakesMissing += model.missingSourceTakeCount; }
            }
            result.models = models.ToArray();
            result.status = Classify(result);
            return result;
        }

        public static string Classify(SourceTakeScanReport report)
        {
            if (report == null || report.incomplete || report.models == null ||
                report.modelsChecked != report.models.Length || report.models.Any(m => m == null || m.incomplete))
                return "INCOMPLETE";
            if (report.modelsChecked == 0) return "NO_CUSTOMER_FBX_MODELS_SCANNED";
            if (report.sourceTakesMissing > 0) return "POSSIBLY_UNEXPOSED_SOURCE_TAKES";
            if (report.models.All(m => m.status == "NO_SOURCE_TAKES" ||
                m.status == "ANIMATION_IMPORT_DISABLED")) return "NO_ENABLED_SOURCE_ANIMATIONS_CHECKED";
            if (report.models.All(m => m.status == "DEFAULT_SOURCE_TAKES_ACTIVE" ||
                m.status == "NO_SOURCE_TAKES" || m.status == "ANIMATION_IMPORT_DISABLED"))
                return "NO_CUSTOMIZED_CLIP_LISTS_TO_COMPARE";
            return "NO_MISSING_SOURCE_TAKES_IN_INSPECTED_CUSTOM_LISTS";
        }

        public static void ExportNew(SourceTakeScanReport report, string absolutePath)
        {
            if (report == null || string.IsNullOrWhiteSpace(absolutePath) || !Path.IsPathRooted(absolutePath))
                throw new ArgumentException("Expected a report and new absolute path.");
            using (var file = new FileStream(absolutePath, FileMode.CreateNew, FileAccess.Write, FileShare.None))
            using (var writer = new StreamWriter(file, new UTF8Encoding(false)))
                writer.Write(JsonUtility.ToJson(report,true));
        }
    }
}
#endif
