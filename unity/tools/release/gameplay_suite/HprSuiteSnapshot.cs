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
        public int SchemaVersion = 2;
        public string WeaponId;
        public string EnemyId;
        public SaveEntityData Player;
        public float PlayerStamina;
        public List<ItemQuantitySaveData> Inventory = new();
        public WeaponRuntimeSnapshot Weapon;
        public EnemyRuntimeSnapshot Enemy;
        public AbilityRuntimeSnapshot Abilities;
        public bool LootAwarded;
        public bool MedkitPickupActive;
        public bool KeyPickupActive;
        public bool DoorOpen;
    }

    /// <summary>Opt-in, one-slot local JSON example, not a generalized encrypted/cloud save SDK.</summary>
    public static class HprSuiteSnapshotStorage
    {
        public static void Save(string path, HprSuiteSnapshot snapshot)
        {
            if (snapshot == null || snapshot.SchemaVersion != 2)
                throw new ArgumentException("Invalid snapshot schema", nameof(snapshot));
            if (string.IsNullOrWhiteSpace(path))
                throw new ArgumentException("Missing file path", nameof(path));
            string parent = Path.GetDirectoryName(Path.GetFullPath(path));
            if (string.IsNullOrWhiteSpace(parent))
                throw new ArgumentException("Missing save directory", nameof(path));
            Directory.CreateDirectory(parent);
            string json = JsonUtility.ToJson(snapshot, true);
            if (json.Length > 1024 * 1024)
                throw new InvalidDataException("Refusing unusually large save");
            string temp = path + ".writing";
            try
            {
                File.WriteAllText(temp, json, new UTF8Encoding(false));
                // File.Replace atomically replaces an existing save on supported local filesystems.
                if (File.Exists(path)) File.Replace(temp, path, null);
                else File.Move(temp, path);
            }
            finally
            {
                if (File.Exists(temp)) File.Delete(temp);
            }
        }

        public static HprSuiteSnapshot Load(string path)
        {
            if (string.IsNullOrWhiteSpace(path) || !File.Exists(path))
                throw new FileNotFoundException("No gameplay-suite save at the requested path");
            var info = new FileInfo(path);
            if (info.Length == 0 || info.Length > 1024 * 1024)
                throw new InvalidDataException("Save is empty or exceeds the one-megabyte limit");
            HprSuiteSnapshot result = JsonUtility.FromJson<HprSuiteSnapshot>(File.ReadAllText(path, Encoding.UTF8));
            if (result == null || result.SchemaVersion != 2 || result.Player == null ||
                result.Inventory == null || result.Abilities == null)
                throw new InvalidDataException("Invalid or incompatible HPR suite save");
            return result;
        }
    }
}
