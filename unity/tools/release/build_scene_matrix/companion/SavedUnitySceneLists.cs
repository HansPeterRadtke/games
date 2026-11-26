using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using HPR.BuildSceneMatrix;

namespace HPR.BuildSceneGate
{
    /// <summary>
    /// Strict, deliberately limited reader of saved first-party Unity project
    /// text files. Never invokes Unity, evaluates YAML tags, or loads assemblies.
    /// Unknown serialized forms fail closed rather than guessing effective lists.
    /// </summary>
    internal sealed class SavedUnitySceneLists
    {
        private const int MaxFileBytes = 4 * 1024 * 1024;
        private const int MaxRows = 20000;
        private const int MaxMetaBytes = 64 * 1024;
        private const int MaxTotalReadBytes = 32 * 1024 * 1024;
        private static readonly UTF8Encoding Utf8 = new UTF8Encoding(false, true);
        private static readonly Regex GuidPattern = new Regex("^[0-9a-f]{32}$", RegexOptions.CultureInvariant);
        private static readonly string ZeroGuid = new string('0', 32);
        private readonly string root;
        private readonly string version;
        private readonly Dictionary<string, byte[]> readFiles = new Dictionary<string, byte[]>(StringComparer.Ordinal);
        private int totalReadBytes;
        private readonly Dictionary<string, bool> observedScenes = new Dictionary<string, bool>(StringComparer.Ordinal);

        private SavedUnitySceneLists(string project)
        {
            root = Path.TrimEndingDirectorySeparator(Path.GetFullPath(project));
            Require(Directory.Exists(root), "Project directory not found.");
            CheckNoLinks(root);
            string[] versionLines = Lines(ReadRequired("ProjectSettings/ProjectVersion.txt"));
            version = Scalar(OneField(versionLines, "m_EditorVersion:", ""));
            Require(version == "6000.6.8f1" || version == "2022.3.22f1",
                "Saved project format is not verified for this Unity version: " + version);
        }

        public static (HprSceneProfile Profile, string UnityVersion) Capture(string project, string selector)
        {
            var scan = new SavedUnitySceneLists(project);
            HprSceneProfile result = selector == "global" ? scan.Global() : scan.Custom(selector);
            scan.VerifyUnchanged();
            return (result, scan.version);
        }

        public static string NewOutputPath(string project, string output)
        {
            string basePath = Path.TrimEndingDirectorySeparator(Path.GetFullPath(project));
            string target = Path.GetFullPath(output);
            string relative = Path.GetRelativePath(basePath, target);
            Require(relative == ".." || relative.StartsWith(".." + Path.DirectorySeparatorChar, StringComparison.Ordinal)
                || Path.IsPathRooted(relative), "Snapshot output must be outside the project directory.");
            Require(string.Equals(Path.GetExtension(target), ".hpr-scenes", StringComparison.OrdinalIgnoreCase),
                "Snapshot output must use .hpr-scenes extension.");
            CheckNoLinks(Path.GetDirectoryName(target) ?? "");
            return target;
        }

        private static void Require(bool value, string message)
        {
            if (!value) throw new InvalidDataException(message);
        }

        // Reject symlinks/reparse points for every existing component, including
        // ancestor directories. This intentionally does not support linked assets.
        private static void CheckNoLinks(string full)
        {
            string path = Path.GetFullPath(full);
            string start = Path.GetPathRoot(path);
            foreach (string part in path.Substring(start.Length).Split(Path.DirectorySeparatorChar,
                StringSplitOptions.RemoveEmptyEntries))
            {
                start = Path.Combine(start, part);
                FileAttributes attrs;
                try { attrs = File.GetAttributes(start); }
                catch (FileNotFoundException) { continue; }
                catch (DirectoryNotFoundException) { continue; }
                Require((attrs & FileAttributes.ReparsePoint) == 0,
                    "Linked/reparse-point project path is not supported: " + start);
            }
        }

        private string Resolve(string relative)
        {
            Require(!string.IsNullOrEmpty(relative) && !relative.Contains('\\') &&
                !relative.Contains(':') && !Path.IsPathRooted(relative) &&
                !relative.Any(char.IsControl) &&
                relative.Split('/').All(part => part.Length > 0 && part != "." && part != ".."),
                "Unsafe or unsupported project-relative path: " + relative);
            string full = Path.GetFullPath(Path.Combine(root, relative.Replace('/', Path.DirectorySeparatorChar)));
            string roundTrip = Path.GetRelativePath(root, full).Replace(Path.DirectorySeparatorChar, '/');
            Require(string.Equals(roundTrip, relative, StringComparison.Ordinal),
                "Project-relative path does not resolve exactly.");
            CheckNoLinks(full);
            return full;
        }

        private static byte[] ReadBounded(string path, int limit = MaxFileBytes)
        {
            RegularFileInput.RequireRegular(path);
            using (var input = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read))
            {
                Require(input.Length <= limit, "Saved project file exceeds read limit: " + path);
                var bytes = new byte[(int)input.Length];
                input.ReadExactly(bytes);
                Require(input.ReadByte() == -1, "Saved file changed during read: " + path);
                return bytes;
            }
        }

        private byte[] ReadRequired(string relative)
        {
            string path = Resolve(relative);
            Require(File.Exists(path), "Saved project file missing: " + relative);
            if (readFiles.TryGetValue(relative, out byte[] original)) return original;
            int limit = relative.EndsWith(".meta", StringComparison.Ordinal) ? MaxMetaBytes : MaxFileBytes;
            var bytes = ReadBounded(path, Math.Min(limit, MaxTotalReadBytes - totalReadBytes));
            totalReadBytes += bytes.Length;
            readFiles.Add(relative, bytes);
            return bytes;
        }

        private static string[] Lines(byte[] bytes) =>
            Utf8.GetString(bytes).TrimStart('\uFEFF').Replace("\r\n", "\n").Split('\n');

        private static string Scalar(string raw)
        {
            string value = raw.Trim();
            // Only simple plain scalars from verified native serialization.
            // A quoted, tagged, anchored, multiline or ambiguous value must not
            // be interpreted by this limited reader.
            Require(!value.Any(char.IsControl) && !value.Contains(" #") && !value.Contains(": ") &&
                (value.Length == 0 || !"\"'!&*|>{[?#@\u0060".Contains(value[0])),
                "Unsupported saved YAML scalar: " + value);
            return value;
        }

        private static string OneField(string[] lines, string field, string indent = "  ")
        {
            string prefix = indent + field;
            string key = field.TrimEnd(':');
            foreach (string line in lines)
            {
                if (!line.StartsWith(indent, StringComparison.Ordinal) || line.Length <= indent.Length ||
                    char.IsWhiteSpace(line[indent.Length])) continue;
                string body = line.Substring(indent.Length);
                int colon = body.IndexOf(':');
                if (colon >= 0 && body.Substring(0, colon).TrimEnd() == key)
                    Require(FieldMatches(line, prefix), "Noncanonical saved field: " + field);
            }
            var values = lines.Where(line => FieldMatches(line, prefix)).ToArray();
            Require(values.Length == 1, "Expected exactly one serialized field: " + field);
            return values[0].Substring(prefix.Length).Trim();
        }

        private static void Header(string[] lines, string objectType, string objectTag)
        {
            Require(lines.Length >= 4 && lines[0] == "%YAML 1.1" &&
                lines[1] == "%TAG !u! tag:unity3d.com,2011:" &&
                lines[2].StartsWith(objectTag, StringComparison.Ordinal) &&
                lines[3] == objectType + ":" &&
                lines.Count(line => line.StartsWith("---", StringComparison.Ordinal)) == 1,
                "Unsupported saved Unity YAML document layout.");
        }

        private List<(bool Enabled, string Path, string Guid)> ParseRows(string[] lines, bool profile)
        {
            string prefix = "  m_Scenes:";
            // Check equivalent but noncanonical spellings before locating the list.
            OneField(lines, "m_Scenes:");
            int[] indexes = Enumerable.Range(0, lines.Length).Where(i =>
                lines[i].StartsWith(prefix, StringComparison.Ordinal) &&
                (lines[i].Length == prefix.Length || lines[i][prefix.Length] == ' ')).ToArray();
            Require(indexes.Length == 1, "Expected exactly one saved scene list.");
            int index = indexes[0];
            string value = lines[index].Substring(prefix.Length).Trim();
            var rows = new List<(bool, string, string)>();
            string enabledKey = profile ? "  - m_enabled:" : "  - enabled:";
            string pathKey = profile ? "    m_path:" : "    path:";
            string guidKey = profile ? "    m_guid:" : "    guid:";
            int iRow = index + 1;
            if (value == "[]")
            {
                Require(iRow >= lines.Length || IsNextTopLevel(lines[iRow]),
                    "Unexpected entries after empty scene list.");
                RejectStrayRows(lines, index, iRow, enabledKey, pathKey, guidKey);
                return rows;
            }
            Require(value.Length == 0, "Unsupported saved scene-list representation.");
            while (iRow < lines.Length && !IsNextTopLevel(lines[iRow]))
            {
                Require(rows.Count < MaxRows && iRow + 2 < lines.Length &&
                    lines[iRow].StartsWith(enabledKey + " ", StringComparison.Ordinal) &&
                    FieldMatches(lines[iRow + 1], pathKey) && FieldMatches(lines[iRow + 2], guidKey),
                    "Unsupported saved scene-list entry at line " + (iRow + 1).ToString(CultureInfo.InvariantCulture));
                string enabled = lines[iRow].Substring(enabledKey.Length).Trim();
                string path = Scalar(lines[iRow + 1].Substring(pathKey.Length));
                string guid = Scalar(lines[iRow + 2].Substring(guidKey.Length));
                Require((enabled == "0" || enabled == "1") && GuidPattern.IsMatch(guid),
                    "Unsupported enabled flag or scene identifier.");
                if (path.Length > 0)
                {
                    Require(path.StartsWith("Assets/", StringComparison.Ordinal) &&
                        path.EndsWith(".unity", StringComparison.OrdinalIgnoreCase),
                        "Only project Assets scene paths are supported: " + path);
                    Resolve(path); // Validate even if not the effective scene list.
                }
                rows.Add((enabled == "1", path, guid));
                iRow += 3;
            }
            Require(rows.Count > 0, "Nonempty scene-list header without recognized entries.");
            RejectStrayRows(lines, index, iRow, enabledKey, pathKey, guidKey);
            return rows;
        }

        private static void RejectStrayRows(string[] lines, int start, int end,
            params string[] keys)
        {
            for (int i = 0; i < lines.Length; i++)
                if (i <= start || i >= end)
                    Require(!keys.Any(key => FieldMatches(lines[i], key)),
                        "Scene-list fields appear outside the recognized list.");
        }

        private static bool FieldMatches(string line, string key) => line == key ||
            line.StartsWith(key + " ", StringComparison.Ordinal);

        private static bool IsNextTopLevel(string line) =>
            line.Length == 0 || (line.StartsWith("  ", StringComparison.Ordinal) && line.Length > 2 &&
            line[2] != ' ' && line[2] != '-' && line.Contains(':'));

        private HprSceneProfile Global()
        {
            string[] lines = Lines(ReadRequired("ProjectSettings/EditorBuildSettings.asset"));
            Header(lines, "EditorBuildSettings", "--- !u!1045 &");
            Require(OneField(lines, "serializedVersion:") == "2",
                "Unsupported EditorBuildSettings serialization version.");
            var profile = new HprSceneProfile { Id = HprSceneMatrix.GlobalId,
                Title = "Global scenes", AssetPath = "", Source = "Shared scene list" };
            Append(profile, ParseRows(lines, false));
            return profile;
        }

        private HprSceneProfile Custom(string selector)
        {
            Require(version == "6000.6.8f1", "Custom saved Build Profiles are supported only for the verified Unity 6.6 version.");
            Require(selector.StartsWith("Assets/", StringComparison.Ordinal) &&
                selector.EndsWith(".asset", StringComparison.OrdinalIgnoreCase),
                "Select global or an explicit project Assets Build Profile .asset path.");
            string[] lines = Lines(ReadRequired(selector));
            Header(lines, "MonoBehaviour", "--- !u!114 &");
            Require(OneField(lines, "m_EditorClassIdentifier:") == "UnityEditor.dll::UnityEditor.Build.Profile.BuildProfile" &&
                OneField(lines, "m_AssetVersion:") == "2",
                "Selected file is not a verified version-two Unity Build Profile.");
            string mode = OneField(lines, "m_OverrideGlobalSceneList:");
            Require(mode == "0" || mode == "1", "Unsupported global scene inheritance flag.");
            var stored = ParseRows(lines, true);
            string name = Scalar(OneField(lines, "m_Name:"));
            var profile = new HprSceneProfile { Id = MetaGuid(selector + ".meta", true),
                Title = name + "  [" + selector + "]", AssetPath = selector,
                Source = mode == "1" ? "Overrides global scenes" : "Inherits global scenes" };
            if (mode == "1") Append(profile, stored);
            else profile.Rows.AddRange(Global().Rows);
            return profile;
        }

        private string MetaGuid(string relative, bool required)
        {
            string full = Resolve(relative);
            bool present = File.Exists(full);
            observedScenes[relative] = present;
            if (!present)
            {
                Require(!required, "Required asset metadata missing: " + relative);
                return "";
            }
            string[] lines = Lines(ReadRequired(relative));
            Require(OneField(lines, "fileFormatVersion:", "") == "2",
                "Unsupported saved metadata format: " + relative);
            string value = OneField(lines, "guid:", "");
            Require(GuidPattern.IsMatch(value) && value != ZeroGuid,
                "Invalid saved asset metadata identifier: " + relative);
            return value;
        }

        private void Append(HprSceneProfile profile, List<(bool Enabled, string Path, string Guid)> rows)
        {
            int buildIndex = 0;
            foreach (var row in rows)
            {
                bool missing = true;
                if (row.Path.Length > 0)
                {
                    bool present = File.Exists(Resolve(row.Path));
                    observedScenes[row.Path] = present;
                    if (present) RegularFileInput.RequireRegular(Resolve(row.Path));
                    string meta = MetaGuid(row.Path + ".meta", false);
                    missing = !present || row.Guid == ZeroGuid || row.Guid != meta;
                }
                profile.Rows.Add(new HprSceneRow { Path = row.Path, Guid = row.Guid,
                    Name = Path.GetFileNameWithoutExtension(row.Path), Enabled = row.Enabled,
                    Missing = missing, ListIndex = profile.Rows.Count, BuildIndex = row.Enabled ? buildIndex++ : -1 });
            }
        }

        private void VerifyUnchanged()
        {
            foreach (var entry in readFiles)
                Require(ReadBounded(Resolve(entry.Key), entry.Value.Length).SequenceEqual(entry.Value),
                    "Saved settings changed during capture: " + entry.Key);
            foreach (var entry in observedScenes)
            {
                string path = Resolve(entry.Key);
                Require(File.Exists(path) == entry.Value,
                    "Scene or metadata presence changed during capture: " + entry.Key);
                if (entry.Value) RegularFileInput.RequireRegular(path);
            }
        }
    }
}
