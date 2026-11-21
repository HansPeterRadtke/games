#if UNITY_EDITOR
using System;
using System.IO;
using System.Text;
using UnityEditor;
using UnityEngine;

// In a brand-new disposable Unity project, preserve an actual serialized
// buyer-owned reference before importing a second conflicting package.
// Report the real observed post-import reference without inventing success.
public static class HprCaseOnlyReferenceBuyerProbe
{
    private static string Receipt(bool after)
    {
        string output=Environment.GetEnvironmentVariable("HPR_CASE_ONLY_REFERENCE_PROOF_DIR") ?? "";
        if (!Application.isBatchMode || !Path.IsPathRooted(output) ||
            !output.StartsWith("/data/var/marketplace-account-setup/unity-20261121-wave52/",StringComparison.Ordinal) ||
            !Directory.Exists(output))
            throw new InvalidOperationException("Expected an existing private reference proof directory");
        string target=Path.Combine(output,after ? "buyer-reference-after.txt" : "buyer-reference-before.txt");
        if (File.Exists(target)) throw new IOException("Refusing to overwrite private buyer reference proof");
        return target;
    }

    public static void Prepare()
    {
        string receipt=Receipt(false);
        const string path="Assets/HPRUpgradeExample/Example.txt";
        const string holder="Assets/BuyerOwned/ExistingReference.asset";
        if (File.Exists(holder)) throw new IOException("Pre-existing buyer asset; refuse to overwrite");
        var original=AssetDatabase.LoadAssetAtPath<TextAsset>(path);
        if (original==null) throw new InvalidOperationException("First original archive not imported");
        if (!AssetDatabase.IsValidFolder("Assets/BuyerOwned"))
            AssetDatabase.CreateFolder("Assets","BuyerOwned");
        var data=ScriptableObject.CreateInstance<HprCaseOnlyReferenceHolder>();
        data.referenced=original;
        AssetDatabase.CreateAsset(data,holder);
        EditorUtility.SetDirty(data);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        var loaded=AssetDatabase.LoadAssetAtPath<HprCaseOnlyReferenceHolder>(holder);
        if (loaded==null || loaded.referenced==null)
            throw new InvalidOperationException("Buyer reference was not serialized correctly");
        string guid=AssetDatabase.AssetPathToGUID(path);
        using (var file=new FileStream(receipt,FileMode.CreateNew,FileAccess.Write,FileShare.None))
        using (var w=new StreamWriter(file,new UTF8Encoding(false)))
        {
            w.WriteLine("unity_version="+Application.unityVersion);
            w.WriteLine("buyer_ref_before_alive="+(loaded.referenced!=null));
            w.WriteLine("original_source_guid="+guid);
            w.WriteLine("reference_asset_path="+holder);
            w.WriteLine("reference_target_path="+AssetDatabase.GetAssetPath(loaded.referenced));
        }
        Debug.Log("HPR_CASE_ONLY_SERIALIZED_BUYER_REFERENCE_PREPARED");
    }

    public static void Audit()
    {
        string receipt=Receipt(true);
        const string holder="Assets/BuyerOwned/ExistingReference.asset";
        var loaded=AssetDatabase.LoadAssetAtPath<HprCaseOnlyReferenceHolder>(holder);
        if (loaded==null) throw new InvalidOperationException("Buyer-owned serialized holder is missing");
        bool alive=loaded.referenced!=null;
        string newPath="Assets/HPRUpgradeExample/example.TXT";
        using (var file=new FileStream(receipt,FileMode.CreateNew,FileAccess.Write,FileShare.None))
        using (var w=new StreamWriter(file,new UTF8Encoding(false)))
        {
            w.WriteLine("unity_version="+Application.unityVersion);
            w.WriteLine("buyer_holder_survived=true");
            w.WriteLine("serialized_reference_after_alive="+alive);
            w.WriteLine("actual_reference_target_path="+(alive ? AssetDatabase.GetAssetPath(loaded.referenced) : "<MISSING>"));
            w.WriteLine("actual_incoming_asset_guid="+AssetDatabase.AssetPathToGUID(newPath));
            w.WriteLine("evidence=DISPOSABLE_OWNED_PROJECT_NOT_CUSTOMER_IMPACT");
        }
        Debug.Log("HPR_CASE_ONLY_SERIALIZED_BUYER_REFERENCE_AUDITED");
    }
}
#endif
