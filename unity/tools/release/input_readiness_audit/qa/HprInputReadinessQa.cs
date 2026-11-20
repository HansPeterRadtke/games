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
        string complex = Path.Combine(dest, "boolean-preprocessor"); Make(complex, 1, true);
        File.WriteAllText(Path.Combine(complex, "Assets", "Scripts", "InputSource.cs"),
@"using UnityEngine;
#if ENABLE_INPUT_SYSTEM || ENABLE_LEGACY_INPUT_MANAGER
public class Either { void Run() { Input.GetKeyDown(KeyCode.A); } }
#endif
#if ENABLE_LEGACY_INPUT_MANAGER && CUSTOM_TARGET
public class Never { void Run() { Input.GetKeyDown(KeyCode.B); } }
#endif
#if !(ENABLE_LEGACY_INPUT_MANAGER || UNITY_EDITOR)
public class OnlyNew { void Run() { Input.GetKeyDown(KeyCode.C); } }
#endif
#if ENABLE_INPUT_SYSTEM && CUSTOM_TARGET
public class Uncertain { void Run() { Input.GetKeyDown(KeyCode.D); } }
#endif
");
        var complexReport = HprInputReadinessAudit.Analyze(complex);
        Assert(complexReport.definiteRisks == 2 && complexReport.uncertainRisks == 1,
            "Boolean branch parsing did not distinguish active, inactive and uncertain Player paths");
        Assert(complexReport.findings.All(x => x.line != 6), "Known inactive composite branch was scanned");
        summary.Add("boolean_preprocessor_conditions=PASS");
        string literals = Path.Combine(dest, "multiline-literals"); Make(literals, 1, true);
        File.WriteAllText(Path.Combine(literals, "Assets", "Scripts", "InputSource.cs"),
            "using UnityEngine;\npublic class MultiLine {\n" +
            "  string oldVerbatim = @\"first line\nInput.GetKeyDown(KeyCode.A) is literal only\nlast line\";\n" +
            "  string raw = \"\"\"first raw line\nInput.GetKeyDown(KeyCode.B) is literal raw\nlast raw line\"\"\";\n" +
            "  void Actual() { if (Input.GetKeyDown(KeyCode.C)) {} }\n" +
            "}\n");
        var literalScan = HprInputReadinessAudit.Analyze(literals);
        Assert(literalScan.definiteRisks == 1 && literalScan.uncertainRisks == 0 &&
               literalScan.findings.Single(x => x.rule == "LEGACY_API_IN_NEW_ONLY").line == 9,
               "Multi-line verbatim and raw strings caused false positives or masked true API calls");
        summary.Add("multiline_source_strings=PASS");
        string aliasProject = Path.Combine(dest, "legacy-alias-calls"); Make(aliasProject, 1, true);
        File.WriteAllText(Path.Combine(aliasProject, "Assets", "Scripts", "InputSource.cs"),
            "using OldDevice = UnityEngine.Input;\n" +
            "class AliasProbe { bool Old() => OldDevice.GetKeyDown(UnityEngine.KeyCode.Space); }\n" +
            "class MoreLegacy { object X() => UnityEngine.Input.mouseScrollDelta; }\n");
        var aliasReport = HprInputReadinessAudit.Analyze(aliasProject);
        Assert(aliasReport.definiteRisks == 2 && aliasReport.uncertainRisks == 0 &&
               aliasReport.findings.Count(x => x.rule == "LEGACY_API_IN_NEW_ONLY") == 2,
               "Aliased legacy API or additional legacy property was missed");
        summary.Add("legacy_input_aliases_and_properties=PASS");
        string interpolation = Path.Combine(dest, "interpolated-call"); Make(interpolation, 1, true);
        File.WriteAllText(Path.Combine(interpolation, "Assets", "Scripts", "InputSource.cs"),
            "using UnityEngine;\npublic class InterpolatedProbe {\n" +
            "  // $\"Input.GetKeyDown(KeyCode.Z)\" is only a comment.\n" +
            "  string suspect = $\"{Input.GetKeyDown(KeyCode.A)}\";\n" +
            "}\n");
        var interpolationReport = HprInputReadinessAudit.Analyze(interpolation);
        Assert(interpolationReport.definiteRisks == 0 && interpolationReport.uncertainRisks == 1 &&
               interpolationReport.findings.Single(x => x.rule == "INTERPOLATED_INPUT_CALL").line == 4,
               "Interpolated expression was missed or a plain comment was treated as executing input");
        summary.Add("interpolated_expression_review_only=PASS");
        string oversized = Path.Combine(dest, "oversized-script"); Make(oversized, 1, true);
        File.WriteAllText(Path.Combine(oversized, "Assets", "Scripts", "InputSource.cs"),
            new string(' ', 1024 * 1024 + 1));
        var oversizedReport = HprInputReadinessAudit.Analyze(oversized);
        Assert(oversizedReport.scriptScanTruncated && oversizedReport.result == "INCOMPLETE" &&
               oversizedReport.findings.Any(x => x.rule == "OVERSIZE_SCRIPT"),
               "Oversized source was skipped without an INCOMPLETE result");
        summary.Add("oversized_source_incomplete=PASS");
        string crowded = Path.Combine(dest, "finding-cap"); Make(crowded, 1, true);
        var crowdedSource = new System.Text.StringBuilder("using UnityEngine;\n");
        for (int i = 0; i < 1005; i++)
            crowdedSource.AppendLine("public class AuditLine" + i + " { bool Key() => Input.GetKeyDown(KeyCode.Space); }");
        File.WriteAllText(Path.Combine(crowded, "Assets", "Scripts", "InputSource.cs"), crowdedSource.ToString());
        var crowdedReport = HprInputReadinessAudit.Analyze(crowded);
        Assert(crowdedReport.findingsTruncated && crowdedReport.result == "INCOMPLETE" &&
               crowdedReport.findings.Count == 1000,
               "Finding cap silently treated incomplete scan as successful");
        summary.Add("finding_cap_incomplete=PASS");
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
