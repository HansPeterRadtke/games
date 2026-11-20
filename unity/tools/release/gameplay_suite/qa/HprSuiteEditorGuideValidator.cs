// Private cleanroom QA, excluded from shipped buyer package.
#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;
using UnityEngine.UIElements;
using HPR.GameplaySuite;

public static class HprSuiteEditorGuideValidator
{
    public static void Run()
    {
        string output = Environment.GetEnvironmentVariable("HPR_SUITE_EDITOR_UI_RECEIPT");
        if (string.IsNullOrWhiteSpace(output) || File.Exists(output))
            throw new InvalidOperationException("Need a fresh Editor UI validation receipt");

        HprSuiteIntegrationGuide.OpenGuide();
        HprSuiteIntegrationGuide guide = Resources
            .FindObjectsOfTypeAll<HprSuiteIntegrationGuide>().FirstOrDefault();
        if (guide == null)
            throw new InvalidOperationException("Integration Guide EditorWindow did not open");
        try
        {
            guide.CreateGUI();
            VisualElement root = guide.rootVisualElement;
            ScrollView scroll = root.Q<ScrollView>();
            if (scroll == null)
                throw new InvalidOperationException("Integration Guide missing responsive scroll layout");
            Label[] labels = root.Query<Label>().ToList().ToArray();
            Button[] buttons = root.Query<Button>().ToList().ToArray();
            if (buttons.Length < 8)
                throw new InvalidOperationException("Integration Guide missing practical first-use actions");
            if (!labels.Any(label => (label.text ?? "").Contains("PACKAGE FILES PRESENT")))
                throw new InvalidOperationException("Installed buyer archive is not reported as complete");
            if (!labels.Any(label => (label.text ?? "").Contains(Application.unityVersion)))
                throw new InvalidOperationException("Unity version missing from Editor diagnosis");
            if (!labels.Any(label => (label.text ?? "").Contains("not a runtime test")))
                throw new InvalidOperationException("UI falsely implies live runtime acceptance");
            File.WriteAllText(output,
                "editor_window_constructs_in_actual_unity=PASS\n" +
                "ui_toolkit_scroll_layout=PASS\n" +
                "action_buttons=" + buttons.Length + "\n" +
                "read_only_file_presence_not_runtime_claim=PASS\n" +
                "editor_version_display=PASS\n");
            Debug.Log("HPR_EDITOR_GUIDE_STRUCTURE_PASS");
        }
        finally
        {
            guide.Close();
        }
    }
}
#endif
