#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Compression;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.RegularExpressions;
using UnityEngine;

namespace HPR.ArchivePreflight
{
    [Serializable]
    public sealed class HprArchivedAsset
    {
        public string assetPath;
        public string guid;
        public bool isFolder;
        public long sourceBytes;
        public string sourceHash;
        public string importerHash;
    }

    [Serializable]
    public sealed class HprArchiveInspection
    {
        public int schemaVersion = 1;
        public string archiveFilename;
        public string status;
        public string reason;
        public int pathsChecked;
        public HprArchivedAsset[] assets;
    }

    [Serializable]
    public sealed class HprArchiveDifference
    {
        public string kind;
        public string before;
        public string after;
        public string guidance;
    }

    [Serializable]
    public sealed class HprArchiveUpgradePreview
    {
        public int schemaVersion = 1;
        public string status;
        public bool incomplete;
        public string limitation;
        public int legacyAssets;
        public int updatedAssets;
        public int addedPaths;
        public int removedPaths;
        public int replacedGuids;
        public int movedPaths;
        public int sourceChanges;
        public int importerChanges;
        public HprArchiveDifference[] findings;
    }

    /// <summary>
    /// Strict read-only Unity .unitypackage TAR.GZ interpreter. Never extracts,
    /// writes, imports or follows archive paths. Intentionally fails closed on
    /// unusual/huge TAR extensions instead of making a false safety claim.
    /// </summary>
    public static class HprUnitypackageArchiveReader
    {
        private const long MaxCompressedBytes = 536870912; // 512 MB
        private const long MaxDecompressedBytes = 2147483648; // 2 GiB scanned
        private const long MaxSinglePayload = 1073741824; // 1 GiB per asset
        private const int MaxHeaders = 40000;
        private const int MaxAssets = 7500;
        private static readonly Regex GuidPattern = new Regex("^[0-9a-f]{32}$", RegexOptions.CultureInvariant);
        private static readonly Regex MetaGuid = new Regex(@"(?m)^guid: ([a-f0-9]{32})\s*$", RegexOptions.CultureInvariant);

        private sealed class EntryGroup
        {
            public string path;
            public bool pathnameSeen;
            public bool metaSeen;
            public bool assetSeen;
            public string metaGuid;
            public bool folder;
            public string assetHash;
            public string metaHash;
            public long assetBytes;
        }

        // Stream every decompressed byte, including trailing TAR blocks, so
        // a truncated or corrupt GZIP footer never produces a false pass.
        private sealed class IntegrityReadStream : Stream
        {
            private readonly Stream inner;
            private readonly Func<bool> canceled;
            private uint crc = 0xffffffffU;
            private long bytesRead;
            private static readonly uint[] Table = MakeCrcTable();

            private static uint[] MakeCrcTable()
            {
                var result = new uint[256];
                for (uint i = 0; i < 256; i++)
                {
                    uint value = i;
                    for (int k = 0; k < 8; k++)
                        value = (value & 1U) != 0U ? (value >> 1) ^ 0xedb88320U : value >> 1;
                    result[i] = value;
                }
                return result;
            }

            public IntegrityReadStream(Stream inner, Func<bool> canceled)
            { this.inner = inner; this.canceled = canceled; }
            public uint FinalCrc { get { return ~crc; } }
            public uint SizeModulo32 { get { return unchecked((uint)bytesRead); } }
            public override bool CanRead { get { return true; } }
            public override bool CanSeek { get { return false; } }
            public override bool CanWrite { get { return false; } }
            public override long Length { get { throw new NotSupportedException(); } }
            public override long Position { get { throw new NotSupportedException(); }
                set { throw new NotSupportedException(); } }
            public override int Read(byte[] buffer, int offset, int count)
            {
                if (canceled != null && canceled())
                    throw new InvalidDataException("Scan canceled while reading compressed content.");
                int size = inner.Read(buffer, offset, count);
                if (size < 0 || bytesRead > MaxDecompressedBytes - size)
                    throw new InvalidDataException("Decompressed GZIP stream exceeds safety limit.");
                bytesRead += size;
                for (int i = offset; i < offset + size; i++)
                    crc = Table[(int)((crc ^ buffer[i]) & 0xffU)] ^ (crc >> 8);
                return size;
            }
            public override void Flush() { throw new NotSupportedException(); }
            public override long Seek(long offset, SeekOrigin origin) { throw new NotSupportedException(); }
            public override void SetLength(long value) { throw new NotSupportedException(); }
            public override void Write(byte[] buffer, int offset, int count) { throw new NotSupportedException(); }
        }

        public static HprArchiveInspection Inspect(string filePath, Func<bool> cancel = null)
        {
            var report = new HprArchiveInspection
            {
                archiveFilename = string.IsNullOrEmpty(filePath) ? "" : Path.GetFileName(filePath),
                status = "INCOMPLETE", reason = "Not yet scanned", assets = new HprArchivedAsset[0]
            };
            try
            {
                if (string.IsNullOrEmpty(filePath) || !Path.IsPathRooted(filePath) ||
                    !filePath.EndsWith(".unitypackage", StringComparison.OrdinalIgnoreCase))
                    throw new InvalidDataException("Choose an existing absolute .unitypackage file.");
                var info = new FileInfo(filePath);
                if (!info.Exists || info.Length < 100 || info.Length > MaxCompressedBytes)
                    throw new InvalidDataException("Missing, empty, or excessive compressed archive size.");
                var groups = new Dictionary<string, EntryGroup>(StringComparer.Ordinal);
                long scanned = 0;
                int headers = 0;
                int zeroBlocks = 0;
                using (var file = new FileStream(filePath, FileMode.Open, FileAccess.Read, FileShare.Read))
                using (var zip = new GZipStream(file, CompressionMode.Decompress))
                using (var input = new IntegrityReadStream(zip, cancel))
                {
                    var header = new byte[512];
                    while (true)
                    {
                        if (cancel != null && cancel())
                            throw new InvalidDataException("Scan canceled; no release pass.");
                        int found = ReadExactly(input, header, 0, 512, true);
                        if (found == 0) throw new InvalidDataException("Truncated TAR: missing end-of-archive blocks.");
                        scanned = CheckedTotal(scanned, 512);
                        if (header.All(x => x == 0))
                        {
                            zeroBlocks++;
                            if (zeroBlocks == 2) break;
                            continue;
                        }
                        if (zeroBlocks != 0) throw new InvalidDataException("Unexpected data after TAR end marker.");
                        if (++headers > MaxHeaders) throw new InvalidDataException("TAR has too many members.");
                        CheckHeaderChecksum(header);
                        string rawName = ReadAscii(header, 0, 100);
                        string name = rawName;
                        string prefix = ReadAscii(header, 345, 155);
                        if (!string.IsNullOrEmpty(prefix)) throw new InvalidDataException("Unsupported TAR filename prefix extension.");
                        if (name.StartsWith("./", StringComparison.Ordinal)) name = name.Substring(2);
                        char kind = (char)header[156];
                        long length = ParseOctal(header, 124, 12);
                        if (length < 0 || length > MaxSinglePayload) throw new InvalidDataException("TAR payload is oversized.");
                        scanned = CheckedTotal(scanned, length + ((512 - (length % 512)) % 512));
                        // Unity's real ExportPackage writes the TAR root as
                        // "./", not only ".". Strip "./" *after* recognizing it.
                        if ((rawName == "." || rawName == "./") && kind == '5' && length == 0)
                            continue;
                        string[] parts = name.TrimEnd('/').Split('/');
                        if (parts.Length < 1 || !GuidPattern.IsMatch(parts[0]))
                            throw new InvalidDataException("Invalid Unity package member GUID or path.");
                        if (kind == '5')
                        {
                            if (parts.Length != 1 || length != 0)
                                throw new InvalidDataException("Unsupported directory member.");
                            continue;
                        }
                        if (kind != '0' && kind != '\0')
                            throw new InvalidDataException("Unsafe/unsupported TAR entry type (not a regular file).");
                        if (parts.Length != 2 || (parts[1] != "pathname" && parts[1] != "asset.meta" &&
                                                  parts[1] != "asset" && parts[1] != "preview.png"))
                            throw new InvalidDataException("Unrecognized Unity package member, refusing to infer safety.");
                        EntryGroup group;
                        if (!groups.TryGetValue(parts[0], out group))
                        {
                            if (groups.Count >= MaxAssets) throw new InvalidDataException("Asset count cap reached.");
                            group = new EntryGroup(); groups.Add(parts[0], group);
                        }
                        if (parts[1] == "pathname")
                        {
                            if (group.pathnameSeen || length < 1 || length > 4096)
                                throw new InvalidDataException("Duplicate/oversized/empty Unity pathname.");
                            byte[] raw = ReadPayload(input, length, true, out _);
                            string path = new UTF8Encoding(false, true).GetString(raw).TrimEnd('\n', '\r');
                            if (!SafeAssetPath(path)) throw new InvalidDataException("Unsafe or unsupported buyer asset path.");
                            group.path = path; group.pathnameSeen = true;
                        }
                        else if (parts[1] == "asset.meta")
                        {
                            if (group.metaSeen || length < 40 || length > 262144)
                                throw new InvalidDataException("Duplicate or invalid metadata payload.");
                            string hash;
                            byte[] raw = ReadPayload(input, length, true, out hash);
                            string meta = new UTF8Encoding(false, true).GetString(raw);
                            var matches = MetaGuid.Matches(meta);
                            if (matches.Count != 1 || matches[0].Groups[1].Value != parts[0])
                                throw new InvalidDataException("Metadata GUID does not match archive member identity.");
                            group.folder = Regex.IsMatch(meta, @"(?m)^folderAsset:\s*yes\s*$");
                            group.metaGuid = parts[0]; group.metaHash = hash; group.metaSeen = true;
                        }
                        else if (parts[1] == "asset")
                        {
                            if (group.assetSeen) throw new InvalidDataException("Duplicate source asset payload.");
                            string hash;
                            ReadPayload(input, length, false, out hash);
                            group.assetHash = hash; group.assetBytes = length; group.assetSeen = true;
                        }
                        else
                        {
                            if (length > 2097152) throw new InvalidDataException("Excessive preview image size.");
                            string ignoredHash;
                            ReadPayload(input, length, false, out ignoredHash);
                        }
                        int padding = (int)((512 - (length % 512)) % 512);
                        if (padding > 0)
                        {
                            var skipped = ReadPayload(input, padding, false, out _);
                            if (skipped != null) throw new InvalidDataException("Unexpected padding buffer.");
                        }
                    }
                    // Some TAR writers pad archives beyond two zero blocks.
                    // Consume the whole decoded stream and require all remaining
                    // bytes to be zero. Verify the *actual* GZIP CRC32 and ISIZE
                    // trailer, rather than trusting a partial decompressor read.
                    byte[] remainder = new byte[65536];
                    int extra;
                    while ((extra = input.Read(remainder, 0, remainder.Length)) > 0)
                        for (int i = 0; i < extra; i++)
                            if (remainder[i] != 0) throw new InvalidDataException("Unexpected nonzero data after TAR end marker.");
                    var trailer = new byte[8];
                    if (file.Seek(-8, SeekOrigin.End) < 0 ||
                        ReadExactly(file, trailer, 0, 8, false) != 8)
                        throw new InvalidDataException("Missing GZIP integrity trailer.");
                    if (BitConverter.ToUInt32(trailer, 0) != input.FinalCrc ||
                        BitConverter.ToUInt32(trailer, 4) != input.SizeModulo32)
                        throw new InvalidDataException("Truncated or corrupted GZIP CRC32/size trailer.");
                }
                var paths = new HashSet<string>(StringComparer.Ordinal);
                var assets = new List<HprArchivedAsset>();
                foreach (var group in groups.OrderBy(x => x.Value.path ?? "", StringComparer.Ordinal))
                {
                    var g = group.Value;
                    if (!g.pathnameSeen || !g.metaSeen || (!g.folder && !g.assetSeen) ||
                        (g.folder && g.assetSeen) || !paths.Add(g.path))
                        throw new InvalidDataException("Missing/duplicate Unity asset, metadata or file path.");
                    assets.Add(new HprArchivedAsset { assetPath = g.path, guid = group.Key,
                        isFolder = g.folder, sourceHash = g.assetHash ?? "", sourceBytes = g.assetBytes,
                        importerHash = g.metaHash });
                }
                if (assets.Count == 0) throw new InvalidDataException("Empty archive; nothing to verify.");
                report.assets = assets.ToArray(); report.pathsChecked = assets.Count;
                report.status = "READABLE_STRICT_ARCHIVE";
                report.reason = "All supported Unity archive members have unique valid paths and matching GUID metadata.";
            }
            catch (Exception e) when (e is IOException || e is InvalidDataException ||
                                       e is ArgumentException || e is UnauthorizedAccessException ||
                                       e is OverflowException || e is DecoderFallbackException)
            {
                report.status = "INCOMPLETE";
                report.reason = e.GetType().Name + ": " + e.Message;
                report.assets = new HprArchivedAsset[0]; report.pathsChecked = 0;
            }
            return report;
        }

        private static bool SafeAssetPath(string path)
        {
            if (string.IsNullOrWhiteSpace(path) || path.Length > 512 ||
                !path.StartsWith("Assets/", StringComparison.Ordinal) ||
                path.Contains("\\") || path.Contains("\0") || path.Contains("//") ||
                path.EndsWith("/", StringComparison.Ordinal) ||
                path.Any(char.IsControl)) return false;
            var segments = path.Split('/');
            return segments.Length > 1 && segments.All(s => s.Length > 0 && s != "." && s != "..");
        }

        private static long CheckedTotal(long previous, long length)
        {
            if (length < 0 || previous > MaxDecompressedBytes - length)
                throw new InvalidDataException("Uncompressed archive safety limit reached.");
            return previous + length;
        }

        private static int ReadExactly(Stream input, byte[] buffer, int index, int requested, bool allowEof)
        {
            int done = 0;
            while (done < requested)
            {
                int amount = input.Read(buffer, index + done, requested - done);
                if (amount == 0)
                {
                    if (done == 0 && allowEof) return 0;
                    throw new InvalidDataException("Truncated compressed TAR member or header.");
                }
                done += amount;
            }
            return done;
        }

        private static byte[] ReadPayload(Stream input, long length, bool capture, out string digest)
        {
            if (capture && length > 262144) throw new InvalidDataException("Refusing oversized buffered archive member.");
            byte[] saved = capture ? new byte[(int)length] : null;
            byte[] chunk = new byte[65536];
            long remaining = length;
            int written = 0;
            using (var hash = SHA256.Create())
            {
                while (remaining > 0)
                {
                    int count = (int)Math.Min(remaining, chunk.Length);
                    ReadExactly(input, chunk, 0, count, false);
                    hash.TransformBlock(chunk, 0, count, chunk, 0);
                    if (saved != null) { Buffer.BlockCopy(chunk, 0, saved, written, count); written += count; }
                    remaining -= count;
                }
                hash.TransformFinalBlock(new byte[0], 0, 0);
                digest = BitConverter.ToString(hash.Hash).Replace("-", "").ToLowerInvariant();
            }
            return saved;
        }

        private static string ReadAscii(byte[] raw, int offset, int length)
        {
            int end = offset;
            while (end < offset + length && raw[end] != 0) end++;
            for (int i = offset; i < end; i++)
                if (raw[i] < 0x20 || raw[i] > 0x7e)
                    throw new InvalidDataException("Non-ASCII TAR member names are unsupported.");
            return Encoding.ASCII.GetString(raw, offset, end - offset);
        }

        private static long ParseOctal(byte[] data, int offset, int length)
        {
            long value = 0; bool digit = false;
            for (int i = offset; i < offset + length; i++)
            {
                byte b = data[i];
                if (b == 0 || b == 32) continue;
                if (b < '0' || b > '7') throw new InvalidDataException("Invalid TAR octal number.");
                digit = true;
                checked { value = value * 8 + (b - '0'); }
            }
            if (!digit) throw new InvalidDataException("Missing TAR octal number.");
            return value;
        }

        private static void CheckHeaderChecksum(byte[] data)
        {
            long expected = ParseOctal(data, 148, 8);
            long total = 0;
            for (int i = 0; i < data.Length; i++) total += i >= 148 && i < 156 ? 32 : data[i];
            if (expected != total) throw new InvalidDataException("TAR header checksum mismatch.");
        }

        public static HprArchiveUpgradePreview Compare(HprArchiveInspection previous, HprArchiveInspection updated,
            int maxFindings = 1200)
        {
            if (maxFindings < 1) throw new ArgumentOutOfRangeException("maxFindings");
            var result = new HprArchiveUpgradePreview
            {
                incomplete = true, status = "INCOMPLETE", findings = new HprArchiveDifference[0],
                limitation = "Stable GUIDs do not guarantee API/runtime compatibility, serialized fileIDs, " +
                    "shader dependencies, external registry packages, purchaser entitlements or imported asset behavior. " +
                    "Always test in a populated disposable buyer project."
            };
            if (previous == null || updated == null ||
                previous.status != "READABLE_STRICT_ARCHIVE" || updated.status != "READABLE_STRICT_ARCHIVE" ||
                previous.assets == null || updated.assets == null ||
                previous.assets.Length == 0 || updated.assets.Length == 0 ||
                previous.assets.Length != previous.pathsChecked || updated.assets.Length != updated.pathsChecked)
                return result;
            result.legacyAssets = previous.pathsChecked; result.updatedAssets = updated.pathsChecked;
            var oldByPath = previous.assets.ToDictionary(x => x.assetPath, x => x, StringComparer.Ordinal);
            var oldByGuid = previous.assets.ToDictionary(x => x.guid, x => x, StringComparer.Ordinal);
            var newByPath = updated.assets.ToDictionary(x => x.assetPath, x => x, StringComparer.Ordinal);
            var newByGuid = updated.assets.ToDictionary(x => x.guid, x => x, StringComparer.Ordinal);
            var findings = new List<HprArchiveDifference>();
            Action<string,string,string,string> add = (type, before, after, advice) =>
            {
                if (findings.Count < maxFindings)
                    findings.Add(new HprArchiveDifference { kind=type, before=before, after=after, guidance=advice });
                else result.incomplete = true;
            };
            result.incomplete = false;
            foreach (var old in previous.assets.OrderBy(x => x.assetPath,StringComparer.Ordinal))
            {
                HprArchivedAsset atPath;
                if (newByPath.TryGetValue(old.assetPath, out atPath))
                {
                    if (old.guid != atPath.guid)
                    {
                        result.replacedGuids++;
                        add("GUID_REPLACED_AT_PATH", old.assetPath+" | "+old.guid,
                            atPath.assetPath+" | "+atPath.guid,
                            "Likely breaks customer serialized references; prove a supported migration before release.");
                    }
                    else
                    {
                        if (old.isFolder != atPath.isFolder)
                        { result.replacedGuids++; add("ASSET_FOLDER_TYPE_CHANGED",old.assetPath,atPath.assetPath,
                            "An asset/folder type change may break Unity references and importer behavior."); }
                        if (old.sourceHash != atPath.sourceHash)
                        { result.sourceChanges++; add("SOURCE_BYTES_CHANGED",old.assetPath,atPath.assetPath,
                            "Identity is stable; independently test API and runtime compatibility in real buyer projects."); }
                        if (old.importerHash != atPath.importerHash)
                        { result.importerChanges++; add("IMPORT_SETTINGS_CHANGED",old.assetPath,atPath.assetPath,
                            "Importer settings changed; inspect serialized subasset IDs and import results."); }
                    }
                }
                else
                {
                    HprArchivedAsset moved;
                    if (newByGuid.TryGetValue(old.guid, out moved))
                    { result.movedPaths++; add("PATH_MOVED_SAME_GUID",old.assetPath,moved.assetPath,
                        "Unity GUID references may survive; test path-based loading and scripted asset lookups."); }
                    else
                    { result.removedPaths++; add("REMOVED_ASSET",old.assetPath+" | "+old.guid,"",
                        "Can break serialized references in existing customer projects."); }
                }
            }
            foreach (var newer in updated.assets.OrderBy(x => x.assetPath,StringComparer.Ordinal))
                if (!oldByGuid.ContainsKey(newer.guid) && !oldByPath.ContainsKey(newer.assetPath))
                { result.addedPaths++; add("ADDED_ASSET","",newer.assetPath+" | "+newer.guid,
                    "New asset: check declared scope, licensing and clean install."); }
            result.findings = findings.ToArray();
            result.status = result.incomplete ? "INCOMPLETE" :
                (result.replacedGuids > 0 || result.removedPaths > 0) ? "REVIEW_POTENTIAL_REFERENCE_BREAKAGE" :
                result.movedPaths > 0 ? "REVIEW_PATH_MIGRATION" :
                (result.sourceChanges > 0 || result.importerChanges > 0) ? "REVIEW_CONTENT_OR_IMPORT_CHANGES" :
                result.addedPaths > 0 ? "ADDITIONS_ONLY" : "IDENTICAL_ASSET_IDENTITIES_AND_BYTES";
            return result;
        }

        public static void ExportNew(HprArchiveUpgradePreview report, string fullPath)
        {
            if (report == null || string.IsNullOrWhiteSpace(fullPath) || !Path.IsPathRooted(fullPath))
                throw new ArgumentException("Valid preview and an absolute path are required.");
            using (var file = new FileStream(fullPath, FileMode.CreateNew, FileAccess.Write, FileShare.None))
            using (var writer = new StreamWriter(file, new UTF8Encoding(false)))
                writer.Write(JsonUtility.ToJson(report,true));
        }
    }
}
#endif
