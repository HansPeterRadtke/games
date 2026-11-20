#if UNITY_EDITOR
using System;
using System.Linq;
using System.Reflection;
using UnityEditor;
using UnityEditor.Build.Profile;
using UnityEngine;
public static class HprBuildProfileInspect
{
    public static void Run()
    {
        if (!Application.isBatchMode) throw new InvalidOperationException("Private QA only");
        var t = typeof(BuildProfile);
        var flags = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static;
        Debug.Log("HPR_BP_TYPE_" + t.AssemblyQualifiedName);
        foreach (var p in t.GetProperties(flags).Where(p => p.Name.IndexOf("platform", StringComparison.OrdinalIgnoreCase) >= 0 || p.Name.IndexOf("target", StringComparison.OrdinalIgnoreCase) >= 0))
            Debug.Log("HPR_BP_PROP " + p.ToString() + " writable=" + p.CanWrite);
        foreach (var m in t.GetMethods(flags).Where(m => m.Name.IndexOf("platform", StringComparison.OrdinalIgnoreCase) >= 0 || m.Name.IndexOf("target", StringComparison.OrdinalIgnoreCase) >= 0 || m.Name.IndexOf("create", StringComparison.OrdinalIgnoreCase) >= 0).Take(35))
            Debug.Log("HPR_BP_METHOD " + m.ToString());
        foreach (var f in t.GetFields(flags).Where(f => f.Name.IndexOf("platform", StringComparison.OrdinalIgnoreCase) >= 0 || f.Name.IndexOf("target", StringComparison.OrdinalIgnoreCase) >= 0))
            Debug.Log("HPR_BP_FIELD " + f.FieldType.FullName + " " + f.Name);
        foreach (var x in t.Assembly.GetTypes().Where(x => x.Name.Contains("BuildProfile") && (x.Name.Contains("Platform") || x.Name.Contains("Creator"))).Take(22))
            Debug.Log("HPR_BP_OTHER_TYPE " + x.FullName);
        Debug.Log("HPR_BP_INSPECT_DONE");
    }
}
#endif
