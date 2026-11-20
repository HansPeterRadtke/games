// Original HPR Project Preflight bundle UI. Editor only, no asset mutations.
#if UNITY_EDITOR
using System;
using System.IO;
using System.Text;
using HPR.InputReadiness;
using HPR.AnimatorContract;
using UnityEditor;
using UnityEngine;

namespace HPR.ProjectPreflight
{
    [Serializable]
    public sealed class HprProjectPreflightReport
    {
        public string unityVersion;
        public string status;
        public InputAuditReport input;
        public AnimatorContractReport animator;
    }

    public sealed class HprProjectPreflightWindow : EditorWindow
    {
        private HprProjectPreflightReport last;
        private Vector2 scroll;
        private string message = "No project preflight has run.";

        [MenuItem("Tools/HPR/Project Preflight Bundle")]
        public static void Open()
        {
            var w = GetWindow<HprProjectPreflightWindow>("HPR Project Preflight");
            w.minSize = new Vector2(610, 360);
            w.Show();
        }

        // Runs only against the active Unity project. The scan never changes
        // PlayerSettings, controllers, scenes, prefabs or package dependencies.
        public static HprProjectPreflightReport ScanBoth()
        {
            var project = Directory.GetParent(Application.dataPath).FullName;
            var report = new HprProjectPreflightReport
            {
                unityVersion = Application.unityVersion,
                input = HprInputReadinessAudit.Analyze(project),
                animator = HprAnimatorContractAudit.ScanProject()
            };
            report.status = Classify(report.input, report.animator);
            return report;
        }

        internal static string Classify(InputAuditReport input, AnimatorContractReport animator)
        {
            if (input == null || animator == null || input.result == "INCOMPLETE" ||
                animator.status == "INCOMPLETE" || input.findingsTruncated || input.scriptScanTruncated ||
                animator.incomplete) return "INCOMPLETE";
            if (input.definiteRisks > 0 || animator.definiteFindings > 0 || input.result == "RISKS_FOUND")
                return "ISSUES_FOUND";
            if (input.uncertainRisks > 0 || input.result == "REVIEW_REQUIRED")
                return "REVIEW_REQUIRED";
            return "NO_ISSUES_IN_CHECKED_CONTRACTS";
        }

        // The only permitted disk write is explicit create-only JSON export.
        public static void SaveReportFresh(HprProjectPreflightReport report, string path)
        {
            if (report == null || string.IsNullOrWhiteSpace(path) || !Path.IsPathRooted(path))
                throw new ArgumentException("A completed report and an absolute destination are required.");
            using (var stream = new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.None))
            using (var writer = new StreamWriter(stream, new UTF8Encoding(false)))
                writer.Write(JsonUtility.ToJson(report, true));
        }

        private void ExportManually()
        {
            if (last == null) return;
            var path = EditorUtility.SaveFilePanel("Save HPR Project Preflight", "",
                "hpr-project-preflight.json", "json");
            if (string.IsNullOrEmpty(path)) return;
            try { SaveReportFresh(last, path); message = "Report saved to the chosen NEW file."; }
            catch (IOException e) { message = "Report not written: " + e.Message; }
        }

        private void OnGUI()
        {
            GUILayout.Space(8);
            GUILayout.Label("HPR PROJECT PREFLIGHT", EditorStyles.boldLabel);
            EditorGUILayout.HelpBox("Run two non-destructive audits before migrating Input handling " +
                "or editing Animator parameters. This is a heuristic, not a guarantee of Player compatibility.",
                MessageType.Info);
            if (GUILayout.Button("Run Input + Animator audits (read only)", GUILayout.Height(32)))
            {
                try { message = "Scanning both contracts..."; last = ScanBoth();
                      message = "Scan complete. Review any findings before modifying assets."; }
                catch (Exception e) { last = null; message = "Scan failed: " + e.Message;
                                      Debug.LogException(e); }
            }
            EditorGUILayout.BeginHorizontal();
            if (GUILayout.Button("Open Input Auditor")) HprInputReadinessAudit.Open();
            if (GUILayout.Button("Open Animator Auditor")) HprAnimatorContractAudit.Open();
            EditorGUILayout.EndHorizontal();
            EditorGUI.BeginDisabledGroup(last == null);
            if (GUILayout.Button("Export combined JSON to NEW file")) ExportManually();
            EditorGUI.EndDisabledGroup();
            EditorGUILayout.HelpBox(message, MessageType.None);
            if (last == null) return;
            GUILayout.Label("Combined status: " + last.status, EditorStyles.boldLabel);
            scroll = EditorGUILayout.BeginScrollView(scroll);
            GUILayout.Label("Input — mode: " + last.input.inputHandling + ", input package: " +
                last.input.inputSystemPackage + ", definite: " + last.input.definiteRisks +
                ", review: " + last.input.uncertainRisks);
            foreach (var finding in last.input.findings)
            {
                EditorGUILayout.LabelField(finding.severity + " " + finding.rule + " — " + finding.asset +
                    (finding.line > 0 ? ":" + finding.line : ""), EditorStyles.wordWrappedLabel);
            }
            GUILayout.Space(8);
            GUILayout.Label("Animator — controllers: " + last.animator.controllersChecked +
                ", states: " + last.animator.statesChecked +
                ", findings: " + last.animator.definiteFindings);
            foreach (var finding in last.animator.findings)
                EditorGUILayout.LabelField(finding.rule + " — " + finding.asset + " > " +
                    finding.scope + " (" + finding.parameter + ")", EditorStyles.wordWrappedLabel);
            EditorGUILayout.EndScrollView();
        }
    }
}
#endif
