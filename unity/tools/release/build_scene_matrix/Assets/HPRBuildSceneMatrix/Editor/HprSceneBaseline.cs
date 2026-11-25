using System;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;

namespace HPR.BuildSceneMatrix
{
    /// <summary>One explicitly saved declared scene list, not a Unity build certificate.</summary>
    public sealed class HprSceneBaseline
    {
        public const string Extension = "hpr-scenes";
        private const int MaxRows = 20000;
        private const int MaxBytes = 4 * 1024 * 1024;
        private const int MaxField = 32768;
        private static readonly byte[] Magic = Encoding.ASCII.GetBytes("HPRSCENE1");
        private static readonly UTF8Encoding Utf8 = new UTF8Encoding(false, true);
        public HprSceneProfile Profile { get; private set; }
        public DateTimeOffset CapturedUtc { get; private set; }

        private HprSceneBaseline(HprSceneProfile profile, DateTimeOffset capturedUtc)
        {
            Profile = profile;
            CapturedUtc = capturedUtc;
        }

        private static void Require(bool ok, string message)
        {
            if (!ok) throw new InvalidDataException(message);
        }

        private static void CheckGuid(string guid)
        {
            Require(string.IsNullOrEmpty(guid) || (guid.Length == 32 &&
                guid.All(c => (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f'))),
                "Invalid scene identifier.");
        }

        private static void Validate(HprSceneProfile profile)
        {
            Require(profile != null && profile.Readable && !string.IsNullOrWhiteSpace(profile.Id),
                "Only readable, identified scene lists can be saved.");
            Require(profile.Rows.Count <= MaxRows, "Too many scene entries.");
            int buildIndex = 0;
            for (int i = 0; i < profile.Rows.Count; i++)
            {
                HprSceneRow row = profile.Rows[i];
                Require(row != null && row.ListIndex == i, "Invalid scene list order.");
                CheckGuid(row.Guid);
                Require(row.BuildIndex == (row.Enabled ? buildIndex++ : -1), "Invalid enabled scene order.");
            }
        }

        private static void WriteText(BinaryWriter writer, string value)
        {
            var bytes = Utf8.GetBytes(value ?? "");
            Require(bytes.Length <= MaxField, "A scene snapshot field is too long.");
            Require(writer.BaseStream.Position + 4 + bytes.Length <= MaxBytes, "Scene snapshot exceeds size limit.");
            writer.Write(bytes.Length);
            writer.Write(bytes);
        }

        private static string ReadText(BinaryReader reader)
        {
            int count = reader.ReadInt32();
            Require(count >= 0 && count <= MaxField && count <= reader.BaseStream.Length - reader.BaseStream.Position,
                "Invalid snapshot field length.");
            return Utf8.GetString(reader.ReadBytes(count));
        }

        private static bool ReadFlag(BinaryReader reader)
        {
            byte value = reader.ReadByte();
            Require(value <= 1, "Invalid snapshot flag.");
            return value == 1;
        }

        /// <summary>Build a bounded payload before opening a create-only user-selected file.</summary>
        public static void SaveNew(string path, HprSceneProfile profile, DateTimeOffset capturedUtc)
        {
            Validate(profile);
            byte[] payload;
            using (var buffer = new MemoryStream())
            using (var writer = new BinaryWriter(buffer, Utf8))
            {
                writer.Write(Magic);
                WriteText(writer, capturedUtc.ToUniversalTime().ToString("O", CultureInfo.InvariantCulture));
                WriteText(writer, profile.Id);
                WriteText(writer, profile.Title);
                WriteText(writer, profile.AssetPath);
                WriteText(writer, profile.Source);
                writer.Write(profile.Rows.Count);
                foreach (var row in profile.Rows)
                {
                    WriteText(writer, row.Path);
                    WriteText(writer, row.Guid);
                    WriteText(writer, row.Name);
                    writer.Write(row.Enabled);
                    writer.Write(row.Missing);
                    writer.Write(row.ListIndex);
                    writer.Write(row.BuildIndex);
                }
                writer.Flush();
                Require(buffer.Length <= MaxBytes, "Scene snapshot exceeds size limit.");
                payload = buffer.ToArray();
            }
            using (var output = new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.None))
                output.Write(payload, 0, payload.Length);
        }

        /// <summary>Read-only import. Historical references never become active build profiles.</summary>
        public static HprSceneBaseline Load(string path)
        {
            using (var input = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read))
            {
                Require(input.Length >= Magic.Length && input.Length <= MaxBytes, "Invalid snapshot size.");
                using (var reader = new BinaryReader(input, Utf8))
                {
                    Require(reader.ReadBytes(Magic.Length).SequenceEqual(Magic), "Unsupported scene snapshot version.");
                    var stamp = ReadText(reader);
                    Require(DateTimeOffset.TryParseExact(stamp, "O", CultureInfo.InvariantCulture,
                        DateTimeStyles.None, out DateTimeOffset time) && time.Offset == TimeSpan.Zero,
                        "Invalid snapshot UTC time.");
                    var profile = new HprSceneProfile
                    {
                        Id = ReadText(reader), Title = ReadText(reader), AssetPath = ReadText(reader),
                        Source = ReadText(reader), Active = false, HistoricalCapturedUtc = time
                    };
                    int rows = reader.ReadInt32();
                    Require(rows >= 0 && rows <= MaxRows, "Invalid snapshot scene count.");
                    for (int i = 0; i < rows; i++)
                    {
                        profile.Rows.Add(new HprSceneRow
                        {
                            Path = ReadText(reader), Guid = ReadText(reader), Name = ReadText(reader),
                            Enabled = ReadFlag(reader), Missing = ReadFlag(reader),
                            ListIndex = reader.ReadInt32(), BuildIndex = reader.ReadInt32()
                        });
                    }
                    Require(input.Position == input.Length, "Unexpected data at end of scene snapshot.");
                    Validate(profile);
                    return new HprSceneBaseline(profile, time);
                }
            }
        }
    }
}
