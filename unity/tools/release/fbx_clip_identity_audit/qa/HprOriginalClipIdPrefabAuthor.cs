#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEngine;

// Original first-party QA prefab author, never shipped in a buyer package.
// May only write in a fresh isolated Unity project populated by the runner.
public static class HprOriginalClipIdPrefabAuthor
{
    public static void Build()
    {
        string report = Environment.GetEnvironmentVariable("HPR_CLIP_ID_PREFAB_AUTHOR_RECEIPT") ?? "";
        if (!Application.isBatchMode || !Path.IsPathRooted(report) ||
            !report.StartsWith("/data/var/marketplace-account-setup/unity-20261122-wave55/", StringComparison.Ordinal) ||
            File.Exists(report))
            throw new InvalidOperationException("A fresh, private author receipt path is required.");
        const string model = "Assets/HPRFbxClipIdentity/Samples/OriginalMotion.fbx";
        const string dir = "Assets/HPRFbxClipIdentity/Samples/Prefabs";
        const string output = dir + "/OriginalMotionTeachingPrefab.prefab";
        var original = AssetDatabase.LoadAssetAtPath<GameObject>(model);
        if (original == null)
            throw new InvalidOperationException("First-party source FBX does not import as a model.");
        if (AssetDatabase.IsValidFolder(dir) || AssetDatabase.LoadAssetAtPath<GameObject>(output) != null)
            throw new InvalidOperationException("Refusing to overwrite an existing prefab folder or file.");
        string targetFile = Path.Combine(Directory.GetParent(Application.dataPath).FullName, output);
        if (File.Exists(targetFile))
            throw new InvalidOperationException("A prefab file already exists.");
        string folder = AssetDatabase.CreateFolder("Assets/HPRFbxClipIdentity/Samples", "Prefabs");
        if (String.IsNullOrEmpty(folder))
            throw new InvalidOperationException("Unity did not create the original prefab folder.");
        GameObject container = new GameObject("HPR Clip Identity - Original Animated FBX");
        try
        {
            var imported = PrefabUtility.InstantiatePrefab(original) as GameObject;
            if (imported == null)
                throw new InvalidOperationException("Unity could not create a genuine original FBX instance.");
            imported.transform.SetParent(container.transform, false);
            imported.transform.localPosition = Vector3.zero;
            imported.transform.localRotation = Quaternion.identity;
            imported.transform.localScale = Vector3.one;
            var prefab = PrefabUtility.SaveAsPrefabAsset(container, output);
            if (prefab == null)
                throw new InvalidOperationException("PrefabUtility.SaveAsPrefabAsset did not return a prefab.");
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            var loaded = AssetDatabase.LoadAssetAtPath<GameObject>(output);
            if (loaded == null)
                throw new InvalidOperationException("Original prefab does not reopen in Unity.");
            var mesh = loaded.GetComponentsInChildren<MeshFilter>(true);
            if (mesh.Length == 0 || Array.Exists(mesh, x => x.sharedMesh == null))
                throw new InvalidOperationException("Prefab has no valid original mesh reference.");
            var dependencies = AssetDatabase.GetDependencies(output, true);
            if (Array.IndexOf(dependencies, model) < 0)
                throw new InvalidOperationException("Prefab does not depend on original FBX model.");
            using (var file = new FileStream(report, FileMode.CreateNew, FileAccess.Write, FileShare.None))
            using (var writer = new StreamWriter(file))
            {
                writer.WriteLine("unity_version=" + Application.unityVersion);
                writer.WriteLine("prefab_asset=" + output);
                writer.WriteLine("original_model=" + model);
                writer.WriteLine("original_model_guid=" + AssetDatabase.AssetPathToGUID(model));
                writer.WriteLine("prefab_guid=" + AssetDatabase.AssetPathToGUID(output));
                writer.WriteLine("prefab_mesh_count=" + mesh.Length);
                writer.WriteLine("actual_unity_prefab_with_original_fbx_mesh_reference=PASS");
            }
            Debug.Log("HPR_CLIP_ID_PREFAB_NATIVE_AUTHOR_PASS");
        }
        finally { UnityEngine.Object.DestroyImmediate(container); }
    }
}
#endif
