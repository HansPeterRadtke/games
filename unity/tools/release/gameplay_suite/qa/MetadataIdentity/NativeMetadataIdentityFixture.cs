// Private negative control: change importer metadata only in this disposable copy.
#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEngine;

public static class NativeMetadataIdentityFixture
{
    private const string Root = "/data/var/marketplace-account-setup/hpr-metadata-identity-20261109";
    private const string Target = "Assets/HPRGameplaySuite/Modules/com.hpr.abilities/Runtime/AbilityRunnerComponent.cs";
    public static void Run()
    {
        string project = Path.GetFullPath(Path.Combine(Application.dataPath, ".."));
        string receipt = Path.Combine(Root, "NATIVE_METADATA_RESULT.json");
        if (project != Path.Combine(Root, "project") || File.Exists(receipt))
            throw new InvalidOperationException("Fresh explicitly isolated metadata fixture required");
        var script = AssetDatabase.LoadAssetAtPath<MonoScript>(Target);
        if (script == null || script.GetClass() == null || !typeof(MonoBehaviour).IsAssignableFrom(script.GetClass()))
            throw new InvalidOperationException("Expected an imported packaged MonoBehaviour");
        int before = MonoImporter.GetExecutionOrder(script);
        string guid = AssetDatabase.AssetPathToGUID(Target);
        if (before != 0 || string.IsNullOrEmpty(guid))
            throw new InvalidOperationException("Expected untouched default execution order");
        MonoImporter.SetExecutionOrder(script, 123);
        AssetDatabase.SaveAssets();
        int after = MonoImporter.GetExecutionOrder(script);
        if (after != 123 || guid != AssetDatabase.AssetPathToGUID(Target))
            throw new InvalidOperationException("Execution order change or stable GUID control failed");
        File.WriteAllText(receipt, JsonUtility.ToJson(new Observation {
            engine = Application.unityVersion, target = Target, guid = guid,
            beforeOrder = before, afterOrder = after, passed = true }, true));
        Debug.Log("HPR_NATIVE_SAME_GUID_METADATA_CONTROL_PASS");
    }
    [Serializable] private sealed class Observation
    {
        public string engine, target, guid;
        public int beforeOrder, afterOrder;
        public bool passed;
    }
}
#endif
