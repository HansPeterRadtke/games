// HPR Animator Contract Audit. Editor only, read-only, and dependency-free.
#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Linq;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;

namespace HPR.AnimatorContract
{
    [Serializable]
    public sealed class AnimatorContractFinding
    {
        public string severity;
        public string asset;
        public string scope;
        public string parameter;
        public string rule;
        public string detail;
    }

    [Serializable]
    public sealed class AnimatorContractReport
    {
        public string unityVersion;
        public string status;
        public int controllersChecked;
        public int transitionsChecked;
        public int statesChecked;
        public int definiteFindings;
        public bool incomplete;
        public List<AnimatorContractFinding> findings = new List<AnimatorContractFinding>();
    }

    /// <summary>
    /// Examines Animator Controller transition and state parameter references.
    /// Scans only editable assets under Assets/; no automatic fixes or source writes.
    /// </summary>
    public sealed class HprAnimatorContractAudit : EditorWindow
    {
        private const int MaxControllers = 10000;
        private const int MaxFindings = 1000;
        private const int MaxStateMachines = 10000;
        private AnimatorContractReport report;
        private Vector2 scroll;

        [MenuItem("Tools/HPR/Animator Contract Audit")]
        public static void Open()
        {
            var window = GetWindow<HprAnimatorContractAudit>("Animator Contract Audit");
            window.minSize = new Vector2(480, 310);
            window.Show();
        }

        private void OnGUI()
        {
            GUILayout.Space(8);
            GUILayout.Label("ANIMATOR CONTRACT AUDIT", EditorStyles.boldLabel);
            EditorGUILayout.HelpBox("Read-only check for missing or incompatible Animator Controller parameters. " +
                "Review results before editing controllers; no assets will be changed.", MessageType.Info);
            if (GUILayout.Button("Scan Animator Controllers (read only)", GUILayout.Height(32)))
            {
                try { report = ScanProject(); }
                catch (Exception e) { report = null; Debug.LogException(e); }
            }
            if (report == null)
            {
                EditorGUILayout.LabelField("No scan has run.");
                return;
            }
            GUILayout.Label("Controllers: " + report.controllersChecked + " | States: " + report.statesChecked +
                " | Transitions: " + report.transitionsChecked + " | Findings: " + report.definiteFindings);
            GUILayout.Label("Status: " + report.status);
            if (GUILayout.Button("Export JSON report (choose new file)", GUILayout.Height(26)))
                ExportManually();
            scroll = GUILayout.BeginScrollView(scroll);
            foreach (var f in report.findings)
            {
                GUILayout.BeginVertical(EditorStyles.helpBox);
                GUILayout.Label(f.rule + ": " + f.parameter + " (" + f.severity + ")", EditorStyles.boldLabel);
                GUILayout.Label(f.asset + " > " + f.scope, EditorStyles.wordWrappedLabel);
                GUILayout.Label(f.detail, EditorStyles.wordWrappedLabel);
                if (GUILayout.Button("Select Controller", GUILayout.Width(145)))
                {
                    var asset = AssetDatabase.LoadAssetAtPath<AnimatorController>(f.asset);
                    if (asset != null) { Selection.activeObject = asset; EditorGUIUtility.PingObject(asset); }
                }
                GUILayout.EndVertical();
            }
            GUILayout.EndScrollView();
        }

        private void ExportManually()
        {
            if (report == null) return;
            string selected = EditorUtility.SaveFilePanel("Save Animator Contract Audit", "",
                "hpr-animator-contract-report.json", "json");
            if (string.IsNullOrWhiteSpace(selected)) return;
            try { SaveReportFresh(report, selected); }
            catch (IOException problem) { Debug.LogWarning("Report not saved: " + problem.Message); }
        }

        // The scanner never writes; explicit user-selected export refuses overwrite.
        public static void SaveReportFresh(AnimatorContractReport current, string destination)
        {
            if (current == null || string.IsNullOrWhiteSpace(destination) ||
                !Path.IsPathRooted(destination))
                throw new ArgumentException("A completed report and absolute destination are required.");
            using (var stream = new FileStream(destination, FileMode.CreateNew,
                FileAccess.Write, FileShare.None))
            using (var writer = new StreamWriter(stream, new UTF8Encoding(false)))
                writer.Write(JsonUtility.ToJson(current, true));
        }

        private static void Add(AnimatorContractReport report, string rule, string asset,
                                string scope, string parameter, string detail)
        {
            if (report.findings.Count >= MaxFindings) { report.incomplete = true; return; }
            report.definiteFindings++;
            report.findings.Add(new AnimatorContractFinding { severity = "ERROR", rule = rule,
                asset = asset, scope = scope, parameter = parameter, detail = detail });
        }

        public static AnimatorContractReport ScanProject()
        {
            var report = new AnimatorContractReport { unityVersion = Application.unityVersion };
            var guids = AssetDatabase.FindAssets("t:AnimatorController", new[] { "Assets" });
            if (guids.Length > MaxControllers) report.incomplete = true;
            foreach (string guid in guids.OrderBy(s => s, StringComparer.Ordinal).Take(MaxControllers))
            {
                string path = AssetDatabase.GUIDToAssetPath(guid);
                if (!path.StartsWith("Assets/", StringComparison.Ordinal) ||
                    !path.EndsWith(".controller", StringComparison.OrdinalIgnoreCase)) continue;
                var controller = AssetDatabase.LoadAssetAtPath<AnimatorController>(path);
                if (controller == null)
                {
                    report.incomplete = true;
                    Add(report, "UNREADABLE_CONTROLLER", path, "Asset", "", "Animator Controller could not be loaded.");
                    continue;
                }
                ScanController(controller, path, report);
            }
            report.status = report.incomplete ? "INCOMPLETE" : report.definiteFindings > 0 ?
                "ISSUES_FOUND" : "NO_ISSUES_IN_CHECKED_CONTRACTS";
            return report;
        }

        public static AnimatorContractReport ScanController(AnimatorController controller, string assetPath)
        {
            var report = new AnimatorContractReport { unityVersion = Application.unityVersion };
            ScanController(controller, assetPath, report);
            report.status = report.incomplete ? "INCOMPLETE" : report.definiteFindings > 0 ?
                "ISSUES_FOUND" : "NO_ISSUES_IN_CHECKED_CONTRACTS";
            return report;
        }

        private static void ScanController(AnimatorController controller, string assetPath,
                                           AnimatorContractReport report)
        {
            if (controller == null) { report.incomplete = true; return; }
            report.controllersChecked++;
            var parameters = controller.parameters.GroupBy(p => p.name, StringComparer.Ordinal)
                .ToDictionary(g => g.Key, g => g.ToArray(), StringComparer.Ordinal);
            foreach (var pair in parameters)
                if (pair.Value.Length > 1) Add(report, "DUPLICATE_PARAMETER", assetPath, "Parameters",
                    pair.Key, "More than one parameter has exactly this name.");
            var visited = new HashSet<AnimatorStateMachine>();
            foreach (var layer in controller.layers)
                if (layer.stateMachine != null)
                    ScanMachine(layer.stateMachine, layer.name, assetPath, parameters, report, visited);
        }

        private static void ValidateReference(string parameter, string scope, string assetPath,
            Dictionary<string, AnimatorControllerParameter[]> available, AnimatorContractReport report,
            AnimatorConditionMode? conditionMode = null)
        {
            if (string.IsNullOrEmpty(parameter))
            {
                Add(report, "EMPTY_PARAMETER", assetPath, scope, "", "A parameter-binding field is empty.");
                return;
            }
            if (!available.TryGetValue(parameter, out var entries))
            {
                Add(report, "MISSING_PARAMETER", assetPath, scope, parameter,
                    "The Animator Controller does not declare the referenced parameter.");
                return;
            }
            if (entries.Length != 1) return; // Already reported ambiguous duplicate name.
            if (conditionMode.HasValue)
            {
                var m = conditionMode.Value;
                var type = entries[0].type;
                bool valid = type == AnimatorControllerParameterType.Float ?
                    m == AnimatorConditionMode.Greater || m == AnimatorConditionMode.Less :
                    type == AnimatorControllerParameterType.Int ?
                    m == AnimatorConditionMode.Greater || m == AnimatorConditionMode.Less ||
                    m == AnimatorConditionMode.Equals || m == AnimatorConditionMode.NotEqual :
                    type == AnimatorControllerParameterType.Bool ?
                    m == AnimatorConditionMode.If || m == AnimatorConditionMode.IfNot :
                    type == AnimatorControllerParameterType.Trigger && m == AnimatorConditionMode.If;
                if (!valid)
                    Add(report, "PARAMETER_TYPE_MISMATCH", assetPath, scope, parameter,
                        "Condition " + m + " is not compatible with parameter type " + type + ".");
            }
        }

        private static void ValidateStateValue(string name, string scope, string path,
            Dictionary<string, AnimatorControllerParameter[]> parameters, AnimatorContractReport report,
            AnimatorControllerParameterType expected)
        {
            ValidateReference(name, scope, path, parameters, report);
            if (!string.IsNullOrEmpty(name) && parameters.TryGetValue(name, out var matches) &&
                matches.Length == 1 && matches[0].type != expected)
                Add(report, "STATE_PARAMETER_TYPE_MISMATCH", path, scope, name,
                    "Active state value requires " + expected + ", but the controller defines " +
                    matches[0].type + ".");
        }

        private static void ScanTransitions(AnimatorTransitionBase[] transitions, string scope,
            string path, Dictionary<string, AnimatorControllerParameter[]> parameters,
            AnimatorContractReport report)
        {
            if (transitions == null) return;
            foreach (var transition in transitions)
            {
                if (transition == null) continue;
                report.transitionsChecked++;
                foreach (var condition in transition.conditions)
                    ValidateReference(condition.parameter, scope, path, parameters, report, condition.mode);
            }
        }

        private static void ValidateBlendFloat(string name, string scope, string path,
            Dictionary<string, AnimatorControllerParameter[]> parameters, AnimatorContractReport report)
        {
            ValidateReference(name, scope, path, parameters, report);
            if (!string.IsNullOrEmpty(name) && parameters.TryGetValue(name, out var entries) &&
                entries.Length == 1 && entries[0].type != AnimatorControllerParameterType.Float)
                Add(report, "BLEND_PARAMETER_TYPE_MISMATCH", path, scope, name,
                    "Blend Tree parameters must use Float; found " + entries[0].type + ".");
        }

        private static void ScanBlendTree(BlendTree tree, string scope, string path,
            Dictionary<string, AnimatorControllerParameter[]> parameters, AnimatorContractReport report,
            HashSet<BlendTree> visited)
        {
            if (tree == null || !visited.Add(tree)) return;
            if (visited.Count > MaxStateMachines) { report.incomplete = true; return; }
            if (tree.blendType != BlendTreeType.Direct)
                ValidateBlendFloat(tree.blendParameter, scope + "/X", path, parameters, report);
            if (tree.blendType != BlendTreeType.Simple1D && tree.blendType != BlendTreeType.Direct)
                ValidateBlendFloat(tree.blendParameterY, scope + "/Y", path, parameters, report);
            int index = 0;
            foreach (var child in tree.children)
            {
                string where = scope + "/Child " + index++;
                if (tree.blendType == BlendTreeType.Direct && child.motion != null)
                    ValidateBlendFloat(child.directBlendParameter, where + "/Weight", path, parameters, report);
                if (child.motion is BlendTree nested)
                    ScanBlendTree(nested, where + "/" + nested.name, path, parameters, report, visited);
            }
        }

        private static void ScanMachine(AnimatorStateMachine machine, string scope, string path,
            Dictionary<string, AnimatorControllerParameter[]> parameters, AnimatorContractReport report,
            HashSet<AnimatorStateMachine> visited)
        {
            if (machine == null || !visited.Add(machine)) return;
            if (visited.Count > MaxStateMachines) { report.incomplete = true; return; }
            ScanTransitions(machine.anyStateTransitions, scope + "/Any State", path, parameters, report);
            ScanTransitions(machine.entryTransitions, scope + "/Entry", path, parameters, report);
            foreach (var stateItem in machine.states)
            {
                var state = stateItem.state;
                if (state == null) { report.incomplete = true; continue; }
                report.statesChecked++;
                string at = scope + "/" + state.name;
                ScanTransitions(state.transitions, at, path, parameters, report);
                if (state.speedParameterActive)
                    ValidateStateValue(state.speedParameter, at + "/Speed", path, parameters, report,
                        AnimatorControllerParameterType.Float);
                if (state.timeParameterActive)
                    ValidateStateValue(state.timeParameter, at + "/Time", path, parameters, report,
                        AnimatorControllerParameterType.Float);
                if (state.mirrorParameterActive)
                    ValidateStateValue(state.mirrorParameter, at + "/Mirror", path, parameters, report,
                        AnimatorControllerParameterType.Bool);
                if (state.cycleOffsetParameterActive)
                    ValidateStateValue(state.cycleOffsetParameter, at + "/Cycle Offset", path, parameters, report,
                        AnimatorControllerParameterType.Float);
                if (state.motion is BlendTree blend)
                    ScanBlendTree(blend, at + "/BlendTree", path, parameters, report,
                        new HashSet<BlendTree>());
            }
            foreach (var child in machine.stateMachines)
            {
                var nested = child.stateMachine;
                if (nested == null) { report.incomplete = true; continue; }
                ScanTransitions(machine.GetStateMachineTransitions(nested), scope + "/" + nested.name + "/Exit",
                    path, parameters, report);
                ScanMachine(nested, scope + "/" + nested.name, path, parameters, report, visited);
            }
        }
    }
}
#endif
