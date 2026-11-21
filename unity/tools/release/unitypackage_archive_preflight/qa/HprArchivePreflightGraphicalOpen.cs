#if UNITY_EDITOR
using System;
using HPR.ArchivePreflight;
using UnityEditor;
using UnityEngine;

// PRIVATE isolated GUI acceptance helper. No terms click, assets, imports,
// network calls or publisher actions. Not exported with buyer package.
[InitializeOnLoad]
public static class HprArchivePreflightGraphicalOpen
{
    static HprArchivePreflightGraphicalOpen()
    {
        if (Environment.GetEnvironmentVariable("HPR_PREFLIGHT_GUI_ACCEPTANCE") != "1") return;
        EditorApplication.delayCall += () =>
        {
            if (Application.isBatchMode) return;
            HprUnitypackageArchiveWindow.Open();
            Debug.Log("HPR_GUI_PREFLIGHT_WINDOW_OPEN_ATTEMPTED");
        };
    }
}
#endif
