// Private QA entry point for command-line Play Mode. Never exported to buyers.
#if UNITY_EDITOR
using System;
using UnityEditor;
using UnityEngine;

public static class HprShowcasePlayAfterStartup
{
    public static void Run()
    {
        // Immediate Play can interrupt Unity Search startup indexing.
        double earliest = EditorApplication.timeSinceStartup + 20;
        void StartWhenIdle()
        {
            if (EditorApplication.timeSinceStartup < earliest ||
                EditorApplication.isCompiling || EditorApplication.isUpdating)
                return;
            EditorApplication.update -= StartWhenIdle;
            try
            {
                HprGameplaySuitePlaymodeValidator.Run();
            }
            catch (Exception error)
            {
                Debug.LogException(error);
                EditorApplication.Exit(1);
            }
        }
        EditorApplication.update += StartWhenIdle;
    }
}
#endif
