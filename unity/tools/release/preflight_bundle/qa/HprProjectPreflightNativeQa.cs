#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using HPR.InputReadiness;
using HPR.AnimatorContract;
using HPR.ProjectPreflight;
using UnityEditor;
using UnityEngine;

// PRIVATE test fixture only; must never be included in sale archive.
public static class HprProjectPreflightNativeQa
{
    private static void Check(bool condition, string message)
    { if (!condition) throw new InvalidOperationException("HPR_PREFLIGHT_QA: " + message); }

    public static void Run()
    {
        string output = Environment.GetEnvironmentVariable("HPR_PREFLIGHT_QA_OUT");
        Check(Application.isBatchMode && !string.IsNullOrWhiteSpace(output) &&
            output.StartsWith("/data/var/marketplace-account-setup/", StringComparison.Ordinal) &&
            !Directory.Exists(output) && !File.Exists(output), "fresh private QA output required");
        Directory.CreateDirectory(output);
        var report = HprProjectPreflightWindow.ScanBoth();
        Check(report != null && report.input != null && report.animator != null, "combined reports missing");
        Check(report.unityVersion == Application.unityVersion &&
            report.input.editorVersion == Application.unityVersion &&
            report.animator.unityVersion == Application.unityVersion, "wrong editor version");
        Check(report.animator.controllersChecked >= 1, "real Animator assets were not scanned");
        Check(report.input.scriptsRead >= 1, "real runtime source was not scanned");
        Check(report.status == HprProjectPreflightWindow.Classify(report.input, report.animator),
            "live combined status disagrees with independent classification");
        Check(HprProjectPreflightWindow.Classify(new InputAuditReport { result = "INCOMPLETE" },
                   new AnimatorContractReport { status = "NO_ISSUES_IN_CHECKED_CONTRACTS" }) == "INCOMPLETE",
                   "incomplete input did not fail closed");
        Check(HprProjectPreflightWindow.Classify(new InputAuditReport { result = "NO_OBVIOUS_RISK_DETECTED" },
                   new AnimatorContractReport { status = "INCOMPLETE" }) == "INCOMPLETE",
                   "incomplete animator did not fail closed");
        Check(HprProjectPreflightWindow.Classify(new InputAuditReport { result = "REVIEW_REQUIRED", uncertainRisks = 1 },
                   new AnimatorContractReport { status = "NO_ISSUES_IN_CHECKED_CONTRACTS" }) == "REVIEW_REQUIRED",
                   "uncertain input erroneously considered clean");
        Check(HprProjectPreflightWindow.Classify(new InputAuditReport { result = "NO_OBVIOUS_RISK_DETECTED" },
                   new AnimatorContractReport { status = "ISSUES_FOUND", definiteFindings = 1 }) == "ISSUES_FOUND",
                   "broken Animator contract omitted from combined status");
        string target = Path.Combine(output, "combined-report.json");
        HprProjectPreflightWindow.SaveReportFresh(report, target);
        string first = File.ReadAllText(target);
        Check(first.Contains("inputHandling") && first.Contains("controllersChecked") &&
              first.Contains("unityVersion"), "combined JSON fields missing");
        bool overwriteBlocked = false;
        try { HprProjectPreflightWindow.SaveReportFresh(report, target); }
        catch (IOException) { overwriteBlocked = true; }
        Check(overwriteBlocked && File.ReadAllText(target) == first, "existing combined report overwritten");
        File.WriteAllText(Path.Combine(output, "receipt.txt"),
            "actual_both_audits_scanned=PASS\n" +
            "input_and_animator_versions=PASS\n" +
            "incomplete_input_fails_closed=PASS\n" +
            "incomplete_animator_fails_closed=PASS\n" +
            "uncertain_input_requires_review=PASS\n" +
            "animator_risk_propagates=PASS\n" +
            "create_only_json_export=PASS\n" +
            "json_contains_both_reports=PASS\n");
        Debug.Log("HPR_PROJECT_PREFLIGHT_NATIVE_QA_PASS " + report.status +
                  " scripts=" + report.input.scriptsRead +
                  " controllers=" + report.animator.controllersChecked +
                  " animator_findings=" + report.animator.definiteFindings +
                  " input_risks=" + report.input.definiteRisks);
    }
}
#endif
