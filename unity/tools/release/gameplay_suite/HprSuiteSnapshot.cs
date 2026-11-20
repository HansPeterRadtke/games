// Copyright (c) Multiverse Studio. Included with HPR Gameplay Systems Suite.
// Demonstration of a versioned, restorable encounter using HPR modules.
using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using UnityEngine;
using HPR;

namespace HPR.GameplaySuite
{
    [Serializable]
    public sealed class HprSuiteSnapshot
    {
        public int SchemaVersion = 3;
        public string WeaponId;
        public string EnemyId;
        public SaveEntityData Player;
        public float PlayerStamina;
        public List<ItemQuantitySaveData> Inventory = new();
        public WeaponRuntimeSnapshot Weapon;
        public EnemyRuntimeSnapshot Enemy;
        public SerializableVector3 EnemyPosition;
        public SerializableQuaternion EnemyRotation;
        public bool AutomaticEnemy;
        public AbilityRuntimeSnapshot Abilities;
        public bool LootAwarded;
        public bool MedkitPickupActive;
        public bool KeyPickupActive;
        public bool DoorOpen;
    }

    /// <summary>Opt-in, one-slot local JSON example, not a generalized encrypted/cloud save SDK.</summary>
    public static class HprSuiteSnapshotStorage
    {
        private const int MaxSaveBytes = 1024 * 1024;
        private static readonly Encoding SaveEncoding = new UTF8Encoding(false);

        public static void Save(string path, HprSuiteSnapshot snapshot)
        {
            if (snapshot == null || snapshot.SchemaVersion != 3)
                throw new ArgumentException("Invalid snapshot schema", nameof(snapshot));
            if (string.IsNullOrWhiteSpace(path))
                throw new ArgumentException("Missing file path", nameof(path));
            string destination = Path.GetFullPath(path);
            string parent = Path.GetDirectoryName(destination);
            if (string.IsNullOrWhiteSpace(parent))
                throw new ArgumentException("Missing save directory", nameof(path));
            string json = JsonUtility.ToJson(snapshot, true);
            if (SaveEncoding.GetByteCount(json) > MaxSaveBytes)
                throw new InvalidDataException("Save exceeds the one-megabyte limit");

            Directory.CreateDirectory(parent);
            string temp = Path.Combine(parent, Path.GetRandomFileName());
            // Only clean up after exclusive creation succeeds. Another save or a
            // pre-existing sibling must never be opened for overwrite or removal.
            var output = new FileStream(temp, FileMode.CreateNew, FileAccess.Write, FileShare.None);
            try
            {
                using (output)
                using (var writer = new StreamWriter(output, SaveEncoding))
                    writer.Write(json);

                if (!File.Exists(destination))
                {
                    try
                    {
                        File.Move(temp, destination);
                        return;
                    }
                    catch (IOException) when (File.Exists(destination))
                    {
                        // A concurrent writer created the slot first.
                    }
                }
                File.Replace(temp, destination, null);
            }
            catch
            {
                File.Delete(temp);
                throw;
            }
        }

        public static HprSuiteSnapshot Load(string path)
        {
            if (string.IsNullOrWhiteSpace(path) || !File.Exists(path))
                throw new FileNotFoundException("No gameplay-suite save at the requested path");

            using var input = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read | FileShare.Delete);
            long length = input.Length;
            if (length == 0 || length > MaxSaveBytes)
                throw new InvalidDataException("Save is empty or exceeds the one-megabyte limit");
            using var reader = new BinaryReader(input);
            byte[] bytes = reader.ReadBytes((int)length);
            if (bytes.Length != length || input.ReadByte() != -1)
                throw new InvalidDataException("Save changed size while reading");
            // Retain BOM detection for existing saves, including files written by other tools.
            using var text = new StreamReader(new MemoryStream(bytes), SaveEncoding);
            HprSuiteSnapshot result = JsonUtility.FromJson<HprSuiteSnapshot>(text.ReadToEnd());
            if (result == null || result.SchemaVersion != 3 || result.Player == null ||
                result.Inventory == null || result.Abilities == null)
                throw new InvalidDataException("Invalid or incompatible HPR suite save");
            return result;
        }
    }
}
