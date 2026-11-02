// Controlled simulation of the Unity API surface used by the exact HPR copier.
// NO real Unity Editor, no importer, no external network, no customer files.
using System;
using System.Collections.Generic;
using System.IO;

namespace UnityEngine
{
    public class Object { }
    public static class Application { public static string dataPath; }
}

namespace UnityEditor
{
    public enum SerializedPropertyType { ObjectReference, String }
    public sealed class SerializedProperty
    {
        public SerializedPropertyType propertyType;
        public UnityEngine.Object objectReferenceValue;
        public string stringValue;
        public bool NextVisible(bool enterChildren) => false;
    }
    public sealed class SerializedObject
    {
        public SerializedObject(UnityEngine.Object source) { }
        public SerializedProperty GetIterator() => new SerializedProperty();
        public SerializedProperty FindProperty(string property) => null;
        public void ApplyModifiedPropertiesWithoutUndo() { }
    }
    public sealed class FakeAsset : UnityEngine.Object
    {
        public readonly string Path;
        public FakeAsset(string path) { Path = path; }
    }
    public static class AssetDatabase
    {
        public const string VendorA = "Assets/HPRGameplaySuite/Samples/AAbility.asset";
        public const string VendorZ = "Assets/HPRGameplaySuite/Samples/ZEffect.asset";
        public const string CustomerA = "Assets/Buyer/CustomerHeal.asset";
        public const string CustomerZ = "Assets/Buyer/CustomerHeal__HPR_ZEffect.asset";
        public static readonly Dictionary<string, UnityEngine.Object> Assets = new();
        public static readonly Dictionary<string, string> Guids = new();
        public static int CopyCalls;
        public static int SavedCopies;
        public static string Scenario;
        public static byte[] ExternalBuyerBytes;
        private static string Physical(string path) => System.IO.Path.Combine(
            UnityEngine.Application.dataPath,
            path.Substring("Assets/".Length).Replace('/', System.IO.Path.DirectorySeparatorChar));

        public static void Start(string root, string scenario)
        {
            Assets.Clear(); Guids.Clear(); CopyCalls = 0; SavedCopies = 0;
            Scenario = scenario;
            UnityEngine.Application.dataPath = System.IO.Path.Combine(root, "Assets");
            Directory.CreateDirectory(Physical(VendorA).Replace("AAbility.asset", ""));
            Directory.CreateDirectory(System.IO.Path.Combine(UnityEngine.Application.dataPath, "Buyer"));
            Create(VendorA, "11111111111111111111111111111111", "vendor_A_original");
            Create(VendorZ, "22222222222222222222222222222222", "vendor_Z_original");
            if (scenario == "initial-collision")
                Create(CustomerA, "55555555555555555555555555555555", "customer-owned-existing");
        }
        public static void Create(string path, string guid, string body)
        {
            string file = Physical(path);
            Directory.CreateDirectory(System.IO.Path.GetDirectoryName(file));
            File.WriteAllText(file, body);
            File.WriteAllText(file + ".meta", "fileFormatVersion: 2\nguid: " + guid + "\n");
            Assets[path] = new FakeAsset(path);
            Guids[path] = guid;
        }
        public static string[] GetDependencies(string source, bool recursive) =>
            new [] { VendorA, VendorZ };
        public static bool IsValidFolder(string path) => path == "Assets/Buyer";
        public static UnityEngine.Object LoadMainAssetAtPath(string path) =>
            Assets.TryGetValue(path, out var asset) ? asset : null;
        public static string AssetPathToGUID(string path) =>
            Guids.TryGetValue(path, out var value) ? value : "";
        public static string GetAssetPath(UnityEngine.Object asset) =>
            asset is FakeAsset item ? item.Path : "";

        public static bool CopyAsset(string source, string target)
        {
            CopyCalls++;
            if (target == CustomerZ && Scenario == "partial-no-file") return false;
            if (target == CustomerA && Scenario == "first-false-no-file") return false;
            if (target == CustomerZ && Scenario == "partial-false-file")
            {
                Create(target, "44444444444444444444444444444444", "partial-copied-file");
                return false;
            }
            string guid = target == CustomerA
                ? "33333333333333333333333333333333"
                : "44444444444444444444444444444444";
            Create(target, guid, "simulated-copy-of:" + source);
            if (target == CustomerA && Scenario == "race-after-preflight")
            {
                Create(CustomerZ,"55555555555555555555555555555555","concurrent-owner-asset");
                ExternalBuyerBytes = File.ReadAllBytes(Physical(CustomerZ));
            }
            return true;
        }
        public static void SaveAssetIfDirty(UnityEngine.Object asset) { SavedCopies++; }
        public static byte[] FileBytes(string path) => File.ReadAllBytes(Physical(path));
        public static bool FileExists(string path) => File.Exists(Physical(path));
    }
}
