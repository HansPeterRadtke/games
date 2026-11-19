#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using HPR.InputReadiness;
using UnityEditor;
using UnityEngine;
using UnityEngine.UIElements;

public static class HprInputReadinessQa
{
    private static void Assert(bool condition, string detail)
    {
        if (!condition) throw new InvalidOperationException("INPUT_AUDIT_QA: " + detail);
    }
    private static void Make(string root, int? mode, bool package)
    {
        Directory.CreateDirectory(Path.Combine(root, "ProjectSettings"));
        Directory.CreateDirectory(Path.Combine(root, "Packages"));
        Directory.CreateDirectory(Path.Combine(root, "Assets", "Scripts"));
        File.WriteAllText(Path.Combine(root, "ProjectSettings", "ProjectSettings.asset"),
            mode.HasValue ? "PlayerSettings:\n  activeInputHandler: " + mode.Value + "\n" : "PlayerSettings:\n");
        File.WriteAllText(Path.Combine(root, "Packages", "manifest.json"),
            package ? "{\"dependencies\":{\"com.unity.inputsystem\":\"1.20.1\"}}" : "{\"dependencies\":{}}");
        File.WriteAllText(Path.Combine(root, "Assets", "Scripts", "InputSource.cs"),
@"using UnityEngine;
public class InputSource : MonoBehaviour {
   // Input.GetKey(KeyCode.A) is only a comment.
   string warning = ""Input.GetKey(KeyCode.A)"";
#if ENABLE_LEGACY_INPUT_MANAGER
   void OldGuarded() { if (Input.GetKey(KeyCode.A)) Debug.Log(""old""); }
#endif
#if UNITY_EDITOR
   void EditorOnly() { if (Input.GetKey(KeyCode.C)) Debug.Log(""editor""); }
#endif
   void PlayerCode() { if (Input.GetKeyDown(KeyCode.B)) Debug.Log(""player""); }
#if CUSTOM_TARGET_SYMBOL
   void UnknownBuildPath() { if (UnityEngine.Input.GetAxis(""Horizontal"") != 0) Debug.Log(""unknown""); }
#endif
}");
    }
    public static void Run()
    {
        string dest = Environment.GetEnvironmentVariable("HPR_INPUT_QA_OUT");
        Assert(Application.isBatchMode && !string.IsNullOrEmpty(dest) &&
            Path.IsPathRooted(dest) && dest.StartsWith("/data/var/marketplace-account-setup/", StringComparison.Ordinal) &&
            !Directory.Exists(dest) && !File.Exists(dest), "Fresh private destination required");
        Directory.CreateDirectory(dest);
        var summary = new List<string>();
        foreach (int mode in new[] { 0, 1, 2 })
        {
            string sub = Path.Combine(dest, "mode-" + mode);
            Make(sub, mode, mode != 0);
            var report = HprInputReadinessAudit.Analyze(sub);
            Assert(report.scriptsRead == 1, "One runtime source should be scanned");
            Assert(report.inputHandling == (mode == 0 ? "Legacy only" : mode == 1 ? "New only" : "Both"), "Input mode detected incorrectly");
            int expected = mode == 1 ? 1 : 0;
            Assert(report.definiteRisks == expected, "Unexpected incompatible definite legacy findings in mode " + mode);
            Assert(report.uncertainRisks == (mode == 1 ? 1 : 0), "Unknown conditional not classified correctly");
            Assert(report.findings.All(x => x.line != 4 && x.line != 3 && x.line != 9), "Comment/string/editor and known guard produced a false-positive");
            summary.Add("mode" + mode + "=PASS");
        }
        string absent = Path.Combine(dest, "missing-package"); Make(absent, 1, false);
        var missing = HprInputReadinessAudit.Analyze(absent);
        Assert(missing.findings.Any(x => x.rule == "MISSING_INPUT_PACKAGE"), "Must flag new mode with absent package");
        summary.Add("missing_package=PASS");
        string oldWithPackage = Path.Combine(dest, "legacy-with-new-api"); Make(oldWithPackage, 0, true);
        File.WriteAllText(Path.Combine(oldWithPackage, "Assets", "Scripts", "InputSource.cs"),
            "using UnityEngine.InputSystem;\npublic class OldModeModernInput { void Update(){ if (Keyboard.current != null) {} } }\n");
        var legacyApiConflict = HprInputReadinessAudit.Analyze(oldWithPackage);
        Assert(legacyApiConflict.findings.Any(x => x.rule == "NEW_API_IN_LEGACY_ONLY") &&
               legacyApiConflict.result == "RISKS_FOUND", "Legacy-only mode did not report unguarded newer Input API");
        summary.Add("new_api_in_legacy_only=PASS");
        string malformed = Path.Combine(dest, "unknown-mode"); Make(malformed, null, true);
        var unknown = HprInputReadinessAudit.Analyze(malformed);
        Assert(unknown.findings.Any(x => x.rule == "UNKNOWN_INPUT_MODE"), "Must fail closed on absent setting");
        summary.Add("unknown_mode=PASS");
        var window = ScriptableObject.CreateInstance<HprInputReadinessAudit>();
        try
        {
            window.CreateGUI();
            var buttons = window.rootVisualElement.Query<Button>().ToList();
            Assert(buttons.Count == 2 && buttons.Any(x => x.text.StartsWith("Scan")) &&
                buttons.Any(x => x.text.StartsWith("Export")), "Editor UX missing visible Scan and Export controls");
            Assert(buttons.Single(x => x.text.StartsWith("Export")).enabledSelf == false,
                "No export allowed before a user scans");
            summary.Add("actual_editor_window_controls=PASS");
            var scriptedRisk = HprInputReadinessAudit.Analyze(Path.Combine(dest, "mode-1"));
            var flags = System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic;
            typeof(HprInputReadinessAudit).GetField("lastReport", flags).SetValue(window, scriptedRisk);
            typeof(HprInputReadinessAudit).GetMethod("ShowReport", flags).Invoke(window, null);
            buttons = window.rootVisualElement.Query<Button>().ToList();
            int expectedButtons = 2 + scriptedRisk.findings.Count(x =>
                x.line > 0 && x.asset.StartsWith("Assets/", StringComparison.Ordinal));
            Assert(buttons.Count == expectedButtons && buttons.Any(x => x.text.Contains("InputSource.cs:")),
                "Input risk did not expose the expected source-location buttons");
            Assert(buttons.Single(x => x.text.StartsWith("Export")).enabledSelf,
                "Export should become available only after a report is displayed");
            // Do not click navigation or file-export buttons in automated tests.
            summary.Add("read_only_source_navigation_controls=PASS");
        }
        finally { UnityEngine.Object.DestroyImmediate(window); }
        string current = Directory.GetParent(Application.dataPath).FullName;
        var live = HprInputReadinessAudit.Analyze(current);
        Assert(live.editorVersion == Application.unityVersion && live.scriptsRead >= 1,
            "Actual Unity project was not scanned");
        File.WriteAllText(Path.Combine(dest, "current-project.json"), JsonUtility.ToJson(live, true));
        summary.Add("actual_unity_project_scanned=PASS");
        File.WriteAllLines(Path.Combine(dest, "qa-receipt.txt"), summary);
        Debug.Log("HPR_INPUT_READINESS_QA_PASS " + string.Join(",", summary));
    }
}
#endif
