// Copyright (c) Multiverse. Private prerelease; not for redistribution.
// Saved, read-only comparison reference for explicitly declared Unity Build Profile defines.
#if UNITY_EDITOR
using System;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using UnityEngine;

namespace HPR.DefineMatrix
{
    [Serializable]
    internal sealed class DefineBaselineDocument
    {
        public string format;
        public string capturedUtc;
        public string profileName;
        public string profileId;
        public string profileAssetPath;
        public string[] symbols;
        public string[] warnings;
    }

    public sealed class HprDefineBaseline
    {
        public const string Extension = "hpr-defines";
        public const string Format = "hpr-define-baseline-v1";
        public const int MaxFileBytes = 262144;
        public readonly DefineProfile Profile;
        public readonly DateTimeOffset CapturedUtc;

        private HprDefineBaseline(DefineProfile profile, DateTimeOffset capturedUtc)
        {
            Profile = profile;
            CapturedUtc = capturedUtc;
        }

        private static void CheckNewPath(string path)
        {
            if (string.IsNullOrWhiteSpace(path) ||
                !path.EndsWith("." + Extension, StringComparison.OrdinalIgnoreCase))
                throw new ArgumentException("Choose a new .hpr-defines file.");
            string resolved = Path.GetFullPath(path);
            string project = Path.GetFullPath(Path.GetDirectoryName(Application.dataPath));
            string prefix = project.EndsWith(Path.DirectorySeparatorChar.ToString()) ? project :
                project + Path.DirectorySeparatorChar;
            if (string.Equals(resolved, project, StringComparison.OrdinalIgnoreCase) ||
                resolved.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
                throw new IOException("Reference files must be stored outside the entire Unity project.");
        }

        public static void SaveNew(string path, DefineProfile profile, DateTimeOffset capturedUtc)
        {
            CheckNewPath(path);
            if (profile == null || !profile.Readable ||
                string.IsNullOrEmpty(profile.Id) || string.IsNullOrEmpty(profile.Path))
                throw new InvalidOperationException("Capture a readable saved Build Profile with asset identity.");
            if (profile.Symbols.Count > HprDefineMatrix.MaxSymbols ||
                profile.Warnings.Count > HprDefineMatrix.MaxSymbols)
                throw new InvalidOperationException("Reference is larger than the supported limit.");
            var document = new DefineBaselineDocument
            {
                format = Format,
                capturedUtc = capturedUtc.ToUniversalTime().ToString("O", CultureInfo.InvariantCulture),
                profileName = profile.Name,
                profileId = profile.Id,
                profileAssetPath = profile.Path,
                symbols = profile.Symbols.ToArray(),
                warnings = profile.Warnings.ToArray()
            };
            string text = JsonUtility.ToJson(document, true) + "\n";
            byte[] bytes = new UTF8Encoding(false).GetBytes(text);
            if (bytes.Length > MaxFileBytes)
                throw new InvalidOperationException("Snapshot exceeds the supported file limit.");
            using (var stream = new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.None))
                stream.Write(bytes, 0, bytes.Length);
        }

        public static HprDefineBaseline Load(string path)
        {
            if (string.IsNullOrWhiteSpace(path) ||
                !path.EndsWith("." + Extension, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException("Select an .hpr-defines reference.");
            var file = new FileInfo(path);
            if (!file.Exists || file.Length < 1 || file.Length > MaxFileBytes)
                throw new InvalidDataException("Snapshot is missing, empty or too large.");
            string text = File.ReadAllText(path, new UTF8Encoding(false, true));
            DefineBaselineDocument data;
            try { data = JsonUtility.FromJson<DefineBaselineDocument>(text); }
            catch (Exception error) { throw new InvalidDataException("Invalid reference JSON.", error); }
            if (data == null || data.format != Format ||
                string.IsNullOrWhiteSpace(data.profileId) ||
                string.IsNullOrWhiteSpace(data.profileAssetPath) ||
                data.symbols == null || data.warnings == null ||
                data.symbols.Length > HprDefineMatrix.MaxSymbols ||
                data.warnings.Length > HprDefineMatrix.MaxSymbols)
                throw new InvalidDataException("Unsupported or incomplete reference document.");
            if (!DateTimeOffset.TryParseExact(data.capturedUtc, "O", CultureInfo.InvariantCulture,
                DateTimeStyles.RoundtripKind, out var capture))
                throw new InvalidDataException("Invalid reference capture time.");
            var profile = new DefineProfile { Id = data.profileId,
                Path = data.profileAssetPath, Name = data.profileName ?? "Saved reference",
                IsActive = false, HistoricalCapturedUtc = capture };
            var symbols = data.symbols;
            if (symbols.Any(v => v == null) ||
                symbols.Distinct(StringComparer.Ordinal).Count() != symbols.Length)
                throw new InvalidDataException("Duplicate or null saved scripting defines.");
            HprDefineMatrix.ParseDeclared(profile, symbols);
            if (profile.Warnings.Count > 0 || profile.Symbols.Count != symbols.Length)
                throw new InvalidDataException("Snapshot contains invalid scripting defines.");
            foreach (var warning in data.warnings)
            {
                if (string.IsNullOrEmpty(warning) || warning.Length > 512 ||
                    warning.IndexOfAny(new[] { '\r', '\n', '\0' }) >= 0)
                    throw new InvalidDataException("Invalid saved warning text.");
                profile.Warnings.Add(warning);
            }
            return new HprDefineBaseline(profile, capture);
        }
    }
}
#endif
