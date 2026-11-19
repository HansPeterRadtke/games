// Original HPR Unity Input Compatibility Auditor. Editor only; never changes a project.
#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEditor.Build.Profile;
using UnityEngine;
using UnityEngine.UIElements;

namespace HPR.InputReadiness
{
    [Serializable]
    public sealed class InputAuditFinding
    {
        public string severity;
        public string rule;
        public string asset;
        public int line;
        public string detail;
    }

    [Serializable]
    public sealed class InputAuditReport
    {
        public string editorVersion;
        public string inputHandling;
        public string inputSystemPackage;
        public string activeBuildProfile;
        public string result;
        public int scriptsRead;
        public int definiteRisks;
        public int uncertainRisks;
        public bool findingsTruncated;
        public bool scriptScanTruncated;
        public List<InputAuditFinding> findings = new List<InputAuditFinding>();
    }

    /// <summary>
    /// Read-only migration preflight, deliberately not an automatic code converter.
    /// Reports source heuristics with their limits, without touching buyer settings or assets.
    /// </summary>
    public sealed class HprInputReadinessAudit : EditorWindow
    {
        private const int MaximumScripts = 10000;
        private const long MaximumScriptBytes = 1024 * 1024;
        private const int MaximumFindings = 1000;
        private const string LegacyMember =
            @"(?:GetKey(?:Down|Up)?|GetButton(?:Down|Up)?|GetAxis(?:Raw)?|GetMouseButton(?:Down|Up)?|" +
            @"GetTouch|GetJoystickNames|GetAccelerationEvent|ResetInputAxes|mousePosition|mouseScrollDelta|" +
            @"touchCount|touches|anyKey(?:Down)?|inputString|acceleration(?:Events?|EventCount)?|" +
            @"gyro|compass|deviceOrientation|multiTouchEnabled|simulateMouseWithTouches|backButtonLeavesApp)\b";
        private static readonly Regex LegacyCalls = new Regex(
            @"(?<![\w.])(?:(?:UnityEngine)\s*\.\s*)?Input\s*\.\s*" + LegacyMember,
            RegexOptions.Compiled);
        private static readonly Regex LegacyAliasDeclaration = new Regex(
            @"^\s*using\s+(?<alias>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?:global::)?UnityEngine\s*\.\s*Input\s*;",
            RegexOptions.Compiled);
        private static readonly Regex LegacyAliasCall = new Regex(
            @"(?<![\w.])(?<alias>[A-Za-z_][A-Za-z0-9_]*)\s*\.\s*" + LegacyMember,
            RegexOptions.Compiled);

        private static bool HasLegacyCall(string source, HashSet<string> aliases)
        {
            if (LegacyCalls.IsMatch(source)) return true;
            foreach (Match match in LegacyAliasCall.Matches(source))
                if (aliases.Contains(match.Groups["alias"].Value)) return true;
            return false;
        }
        private static readonly Regex NewApi = new Regex(
            @"\b(?:UnityEngine\s*\.\s*)?InputSystem\b|\b(?:Keyboard|Mouse|Gamepad)\s*\.\s*current\b",
            RegexOptions.Compiled);
        private InputAuditReport lastReport;
        private ScrollView results;
        private Label state;
        private Button export;

        [MenuItem("Tools/HPR/Input Compatibility Audit")]
        public static void Open()
        {
            var w = GetWindow<HprInputReadinessAudit>();
            w.titleContent = new GUIContent("Input Compatibility Audit");
            w.minSize = new Vector2(440, 320);
            w.Show();
        }

        public void CreateGUI()
        {
            rootVisualElement.Clear();
            var body = new ScrollView();
            rootVisualElement.Add(body);
            var title = new Label("INPUT COMPATIBILITY AUDIT");
            title.style.unityFontStyleAndWeight = FontStyle.Bold;
            title.style.fontSize = 17;
            body.Add(title);
            body.Add(new Label("Check legacy input use before switching your project to the new Input System."));
            body.Add(new Label("This is a read-only heuristic. It cannot prove every code path, package or scene is safe."));
            state = new Label("No scan has run. Your assets and project settings will not be edited.");
            body.Add(state);
            var run = new Button(() =>
            {
                state.text = "Scanning project scripts. No changes are being made.";
                EditorApplication.delayCall += () =>
                {
                    if (this == null || state == null) return;
                    try { lastReport = Analyze(Directory.GetParent(Application.dataPath).FullName); ShowReport(); }
                    catch (Exception e) { lastReport = null; state.text = "Audit stopped: " + e.Message; export.SetEnabled(false); }
                };
            }) { text = "Scan input compatibility (read only)" };
            body.Add(run);
            export = new Button(ExportManually) { text = "Export report as JSON (choose file)" };
            export.SetEnabled(false);
            body.Add(export);
            results = new ScrollView();
            results.style.flexGrow = 1;
            body.Add(results);
        }

        private void ShowReport()
        {
            results.Clear();
            state.text = "Mode: " + lastReport.inputHandling + " | Input System package: " +
                         lastReport.inputSystemPackage + " | Potential risks: " + lastReport.definiteRisks +
                         " | Needs review: " + lastReport.uncertainRisks;
            results.Add(new Label("Files examined: " + lastReport.scriptsRead +
                                  ". Result: " + lastReport.result));
            foreach (var f in lastReport.findings)
            {
                string description = f.severity + ": " + f.asset +
                    (f.line > 0 ? ":" + f.line : "") + " — " + f.detail;
                if (f.line > 0 && f.asset.StartsWith("Assets/", StringComparison.Ordinal))
                {
                    // User explicitly chooses to open one source location; never edit it.
                    var sourceLink = new Button(() =>
                    {
                        var script = AssetDatabase.LoadAssetAtPath<MonoScript>(f.asset);
                        if (script == null || !AssetDatabase.OpenAsset(script, f.line))
                            state.text = "This script cannot be opened automatically. Locate it in the Project window.";
                    }) { text = description };
                    sourceLink.style.whiteSpace = WhiteSpace.Normal;
                    results.Add(sourceLink);
                }
                else
                {
                    var label = new Label(description);
                    label.style.whiteSpace = WhiteSpace.Normal;
                    results.Add(label);
                }
            }
            export.SetEnabled(true);
        }

        private void ExportManually()
        {
            if (lastReport == null) return;
            string path = EditorUtility.SaveFilePanel("Export input compatibility report", "", "unity-input-audit.json", "json");
            if (string.IsNullOrWhiteSpace(path)) return;
            try
            {
                using (var stream = new FileStream(path, FileMode.CreateNew, FileAccess.Write, FileShare.None))
                using (var writer = new StreamWriter(stream, new UTF8Encoding(false)))
                    writer.Write(JsonUtility.ToJson(lastReport, true));
                state.text = "Report created. No project asset or configuration was changed.";
            }
            catch (IOException error) { state.text = "Report not saved: " + error.Message; }
        }

        private enum Certainty { No, Yes, Unknown }
        private struct Branch
        {
            public Certainty parent;
            public Certainty prior;
        }
        private static Certainty And(Certainty a, Certainty b) => a == Certainty.No || b == Certainty.No ?
            Certainty.No : a == Certainty.Yes && b == Certainty.Yes ? Certainty.Yes : Certainty.Unknown;
        private static Certainty Or(Certainty a, Certainty b) => a == Certainty.Yes || b == Certainty.Yes ?
            Certainty.Yes : a == Certainty.No && b == Certainty.No ? Certainty.No : Certainty.Unknown;
        private static Certainty Not(Certainty a) => a == Certainty.Yes ? Certainty.No :
            a == Certainty.No ? Certainty.Yes : Certainty.Unknown;

        private static Certainty Symbol(string s, int mode, bool installed)
        {
            if (s == "ENABLE_LEGACY_INPUT_MANAGER") return mode == 0 || mode == 2 ? Certainty.Yes :
                mode == 1 ? Certainty.No : Certainty.Unknown;
            if (s == "ENABLE_INPUT_SYSTEM") return mode == 1 || mode == 2 ?
                (installed ? Certainty.Yes : Certainty.Unknown) : mode == 0 ? Certainty.No : Certainty.Unknown;
            if (s == "UNITY_EDITOR") return Certainty.No; // Inspect Player paths, not editor code.
            return Certainty.Unknown; // Other user/platform defines are not guessed.
        }
        // C# preprocessor condition grammar: identifiers, true/false, !, &&, ||,
        // and parentheses. Unknown symbols use three-valued logic: branches with
        // unknown compilation symbols remain REVIEW, never a false unconditional PASS.
        private sealed class ConditionParser
        {
            private readonly string expression;
            private readonly int mode;
            private readonly bool installed;
            private int index;

            public ConditionParser(string expression, int mode, bool installed)
            {
                int comment = expression.IndexOf("//", StringComparison.Ordinal);
                this.expression = comment >= 0 ? expression.Substring(0, comment) : expression;
                this.mode = mode;
                this.installed = installed;
            }

            private void SkipSpaces()
            {
                while (index < expression.Length && char.IsWhiteSpace(expression[index])) index++;
            }

            private bool Take(string token)
            {
                SkipSpaces();
                if (index + token.Length > expression.Length ||
                    string.CompareOrdinal(expression, index, token, 0, token.Length) != 0) return false;
                index += token.Length;
                return true;
            }

            private Certainty Atom()
            {
                SkipSpaces();
                if (Take("("))
                {
                    Certainty nested = ParseOr();
                    return Take(")") ? nested : Certainty.Unknown;
                }
                int start = index;
                if (index < expression.Length &&
                    (char.IsLetter(expression[index]) || expression[index] == '_'))
                {
                    index++;
                    while (index < expression.Length &&
                        (char.IsLetterOrDigit(expression[index]) || expression[index] == '_')) index++;
                    string name = expression.Substring(start, index - start);
                    if (name == "true") return Certainty.Yes;
                    if (name == "false") return Certainty.No;
                    return Symbol(name, mode, installed);
                }
                // Unsupported directive syntax must not be interpreted as definitely true.
                if (index < expression.Length) index++;
                return Certainty.Unknown;
            }

            private Certainty Unary() => Take("!") ? Not(Unary()) : Atom();
            private Certainty ParseAnd()
            {
                Certainty result = Unary();
                while (Take("&&")) result = And(result, Unary());
                return result;
            }
            private Certainty ParseOr()
            {
                Certainty result = ParseAnd();
                while (Take("||")) result = Or(result, ParseAnd());
                return result;
            }
            public Certainty Evaluate()
            {
                if (expression.Length > 512) return Certainty.Unknown;
                Certainty result = ParseOr();
                SkipSpaces();
                return index == expression.Length ? result : Certainty.Unknown;
            }
        }

        private static Certainty Condition(string expression, int mode, bool installed) =>
            new ConditionParser(expression, mode, installed).Evaluate();
        private static void Add(InputAuditReport report, string severity, string rule,
                                string asset, int line, string detail)
        {
            if (report.findings.Count >= MaximumFindings)
            {
                report.findingsTruncated = true;
                return;
            }
            report.findings.Add(new InputAuditFinding
            { severity = severity, rule = rule, asset = asset, line = line, detail = detail });
            if (severity == "RISK") report.definiteRisks++;
            else if (severity == "REVIEW") report.uncertainRisks++;
        }

        private static IEnumerable<string> Scripts(string root)
        {
            var pending = new Stack<string>();
            pending.Push(Path.Combine(root, "Assets"));
            while (pending.Count > 0)
            {
                string dir = pending.Pop();
                if (!Directory.Exists(dir) || (File.GetAttributes(dir) & FileAttributes.ReparsePoint) != 0) continue;
                if (Path.GetFileName(dir) == "Editor" || Path.GetFileName(dir) == "Tests") continue;
                foreach (string sub in Directory.GetDirectories(dir).OrderByDescending(p => p, StringComparer.Ordinal))
                    pending.Push(sub);
                foreach (string file in Directory.GetFiles(dir, "*.cs").OrderBy(p => p, StringComparer.Ordinal))
                    if ((File.GetAttributes(file) & FileAttributes.ReparsePoint) == 0) yield return file;
            }
        }

        private struct SourceLexState
        {
            public bool BlockComment;
            public bool VerbatimString;
            public bool InterpolatedVerbatim;
            public int RawQuotes;
            public bool InterpolatedRaw;
        }

        private static int QuoteRun(string input, int index)
        {
            int count = 0;
            while (index + count < input.Length && input[index + count] == '"') count++;
            return count;
        }

        // Preserve lexical state across physical lines for verbatim and raw C#
        // strings; a previous per-line scanner spuriously reported old Input calls
        // inside a multi-line literal as executable code.
        private static string MaskCommentsAndStrings(string input, ref SourceLexState state,
                                                     out bool uncertainInterpolation)
        {
            var sb = new StringBuilder(input.Length);
            uncertainInterpolation = state.InterpolatedVerbatim || state.InterpolatedRaw;
            bool quote = false, character = false, escaped = false;
            for (int i = 0; i < input.Length; i++)
            {
                char c = input[i], next = i + 1 < input.Length ? input[i + 1] : '\0';
                if (state.BlockComment)
                {
                    if (c == '*' && next == '/') { state.BlockComment = false; sb.Append("  "); i++; }
                    else sb.Append(' ');
                }
                else if (state.RawQuotes > 0)
                {
                    int run = c == '"' ? QuoteRun(input, i) : 0;
                    if (run >= state.RawQuotes)
                    {
                        for (int n = 0; n < run; n++) sb.Append(' ');
                        i += run - 1;
                        state.RawQuotes = 0;
                        state.InterpolatedRaw = false;
                    }
                    else sb.Append(' ');
                }
                else if (state.VerbatimString)
                {
                    if (c == '"' && next == '"') { sb.Append("  "); i++; }
                    else if (c == '"') { sb.Append(' '); state.VerbatimString = false; state.InterpolatedVerbatim = false; }
                    else sb.Append(' ');
                }
                else if (quote || character)
                {
                    sb.Append(' ');
                    if (escaped) escaped = false;
                    else if (c == '\\') escaped = true;
                    else if ((quote && c == '"') || (character && c == '\''))
                    { quote = false; character = false; }
                }
                else if (c == '/' && next == '/') { sb.Append(' ', input.Length - i); break; }
                else if (c == '/' && next == '*') { state.BlockComment = true; sb.Append("  "); i++; }
                else if ((c == '@' && next == '"') ||
                         (c == '$' && next == '@' && i + 2 < input.Length && input[i + 2] == '"') ||
                         (c == '@' && next == '$' && i + 2 < input.Length && input[i + 2] == '"'))
                {
                    int prefix = next == '"' ? 2 : 3;
                    state.VerbatimString = true;
                    state.InterpolatedVerbatim = prefix == 3;
                    if (state.InterpolatedVerbatim) uncertainInterpolation = true;
                    for (int n = 0; n < prefix; n++) sb.Append(' ');
                    i += prefix - 1;
                }
                else if (c == '"' && QuoteRun(input, i) >= 3)
                {
                    int run = QuoteRun(input, i);
                    state.RawQuotes = run;
                    state.InterpolatedRaw = i > 0 && input[i - 1] == '$';
                    if (state.InterpolatedRaw) uncertainInterpolation = true;
                    for (int n = 0; n < run; n++) sb.Append(' ');
                    i += run - 1;
                }
                else if (c == '$' && next == '"')
                {
                    uncertainInterpolation = true;
                    quote = true;
                    sb.Append("  ");
                    i++;
                }
                else if (c == '"') { quote = true; sb.Append(' '); }
                else if (c == '\'') { character = true; sb.Append(' '); }
                else sb.Append(c);
            }
            // Interpolation expressions may execute input APIs. The simple lexer
            // cannot parse C# interpolation braces, so such matches are REVIEW,
            // never silently ignored nor asserted definitely executable.
            uncertainInterpolation = uncertainInterpolation &&
                (LegacyCalls.IsMatch(input) || NewApi.IsMatch(input));
            return sb.ToString();
        }

        /// <summary>Read-only, deterministic project audit. No imports, backups, deletes or configuration edits.</summary>
        public static InputAuditReport Analyze(string projectRoot)
        {
            var report = new InputAuditReport { editorVersion = Application.unityVersion,
                inputHandling = "Unknown", inputSystemPackage = "Not detected",
                activeBuildProfile = "No custom build profile", result = "INCOMPLETE" };
            string settings = Path.Combine(projectRoot, "ProjectSettings", "ProjectSettings.asset");
            string manifest = Path.Combine(projectRoot, "Packages", "manifest.json");
            int mode = -1;
            if (File.Exists(settings))
            {
                var matches = Regex.Matches(File.ReadAllText(settings), @"(?m)^\s*activeInputHandler:\s*(\d+)\s*$");
                if (matches.Count == 1 && int.TryParse(matches[0].Groups[1].Value, out int parsed) && parsed <= 2)
                    mode = parsed;
            }
            // A custom active Build Profile may override global PlayerSettings.
            // The serialized override field is not a public stable API; fail closed
            // instead of falsely claiming the global mode is the effective one.
            bool activeOverride = false;
            string currentRoot = Directory.GetParent(Application.dataPath).FullName;
            if (string.Equals(Path.GetFullPath(projectRoot).TrimEnd(Path.DirectorySeparatorChar),
                              Path.GetFullPath(currentRoot).TrimEnd(Path.DirectorySeparatorChar),
                              StringComparison.Ordinal))
            {
                var profile = BuildProfile.GetActiveBuildProfile();
                if (profile != null)
                {
                    report.activeBuildProfile = AssetDatabase.GetAssetPath(profile);
                    if (string.IsNullOrWhiteSpace(report.activeBuildProfile))
                        report.activeBuildProfile = profile.name;
                    // Unity 6.6 does not expose a stable public API for determining
                    // whether the active profile overrides this specific serialized
                    // Player setting. Treat any custom active profile as unknown.
                    activeOverride = true;
                    mode = -1;
                    Add(report, "RISK", "ACTIVE_BUILD_PROFILE_OVERRIDE", report.activeBuildProfile, 0,
                        "The selected Build Profile may override Player Settings. Global input mode is not authoritative; " +
                        "inspect File > Build Profiles > Player Settings and test the effective Player build.");
                }
            }
            report.inputHandling = mode == 0 ? "Legacy only" : mode == 1 ? "New only" :
                                   mode == 2 ? "Both" : "Unknown";
            if (mode == -1 && !activeOverride) Add(report, "RISK", "UNKNOWN_INPUT_MODE", "ProjectSettings/ProjectSettings.asset", 0,
                "Cannot determine active input handling; do not assume compatibility.");
            bool installed = false;
            if (File.Exists(manifest))
            {
                string json = File.ReadAllText(manifest);
                var match = Regex.Match(json, "\\\"com\\.unity\\.inputsystem\\\"\\s*:\\s*\\\"([^\\\"]+)\\\"");
                installed = match.Success;
                report.inputSystemPackage = match.Success ? match.Groups[1].Value : "Not installed";
            }
            else Add(report, "RISK", "MISSING_MANIFEST", "Packages/manifest.json", 0,
                "Package manifest missing: installed input backend cannot be verified.");
            if ((mode == 1 || mode == 2) && !installed)
                Add(report, "RISK", "MISSING_INPUT_PACKAGE", "Packages/manifest.json", 0,
                    "New Input backend is configured but the Input System package was not found in the manifest.");
            if (mode == 0)
                Add(report, "INFO", "LEGACY_DEPRECATION", "ProjectSettings/ProjectSettings.asset", 0,
                    "Legacy input is deprecated; plan migration before future Unity versions remove it.");
            if (!Directory.Exists(Path.Combine(projectRoot, "Assets")))
            {
                Add(report, "RISK", "MISSING_ASSETS", "Assets", 0, "No Assets directory to inspect.");
                return report;
            }
            foreach (var file in Scripts(projectRoot))
            {
                if (++report.scriptsRead > MaximumScripts)
                {
                    report.scriptsRead = MaximumScripts;
                    report.scriptScanTruncated = true;
                    Add(report, "RISK", "SCAN_LIMIT", "Assets", 0,
                        "More than ten thousand scripts; this audit was truncated.");
                    break;
                }
                string relative = file.Substring(projectRoot.TrimEnd(Path.DirectorySeparatorChar).Length + 1)
                    .Replace('\\', '/');
                if (new FileInfo(file).Length > MaximumScriptBytes)
                {
                    report.scriptScanTruncated = true;
                    Add(report, "REVIEW", "OVERSIZE_SCRIPT", relative, 0,
                        "Script larger than one megabyte was not scanned; results are INCOMPLETE.");
                    continue;
                }
                SourceLexState lex = new SourceLexState();
                var branches = new Stack<Branch>();
                var aliases = new HashSet<string>(StringComparer.Ordinal);
                var current = Certainty.Yes;
                int lineNo = 0;
                foreach (var line in File.ReadLines(file))
                {
                    lineNo++;
                    string directive = line.Trim();
                    if (directive.StartsWith("#if ", StringComparison.Ordinal))
                    {
                        Certainty cond = Condition(directive.Substring(4), mode, installed);
                        branches.Push(new Branch { parent = current, prior = cond });
                        current = And(current, cond);
                        continue;
                    }
                    if (directive.StartsWith("#elif ", StringComparison.Ordinal) && branches.Count > 0)
                    {
                        var frame = branches.Pop();
                        Certainty cond = Condition(directive.Substring(6), mode, installed);
                        current = And(frame.parent, And(Not(frame.prior), cond));
                        frame.prior = Or(frame.prior, cond);
                        branches.Push(frame);
                        continue;
                    }
                    if (directive == "#else" && branches.Count > 0)
                    {
                        var frame = branches.Peek(); current = And(frame.parent, Not(frame.prior)); continue;
                    }
                    if (directive == "#endif" && branches.Count > 0)
                    {
                        current = branches.Pop().parent; continue;
                    }
                    bool interpolatedCall;
                    string source = MaskCommentsAndStrings(line, ref lex, out interpolatedCall);
                    if (current == Certainty.No) continue;
                    bool certain = current == Certainty.Yes;
                    var alias = LegacyAliasDeclaration.Match(source);
                    if (alias.Success) aliases.Add(alias.Groups["alias"].Value);
                    bool legacy = HasLegacyCall(source, aliases);
                    if (mode == 1 && legacy)
                        Add(report, certain ? "RISK" : "REVIEW", "LEGACY_API_IN_NEW_ONLY",
                            relative, lineNo, "Possible old UnityEngine.Input call in a new-only Player; check the actual execution path.");
                    if (mode == 1 && !legacy && interpolatedCall && HasLegacyCall(line, aliases))
                        Add(report, "REVIEW", "INTERPOLATED_INPUT_CALL", relative, lineNo,
                            "Possible executable legacy input API inside an interpolated string; inspect the expression.");
                    if (!installed && NewApi.IsMatch(source))
                        Add(report, certain ? "RISK" : "REVIEW", "NEW_API_WITHOUT_PACKAGE",
                            relative, lineNo, "Possible Input System API reference but com.unity.inputsystem is not installed.");
                    else if (installed && mode == 0 && NewApi.IsMatch(source))
                        Add(report, certain ? "RISK" : "REVIEW", "NEW_API_IN_LEGACY_ONLY",
                            relative, lineNo, "Possible newer Input System API in a legacy-only Player; confirm the runtime code path.");
                    if ((!installed || mode == 0) && !NewApi.IsMatch(source) && interpolatedCall && NewApi.IsMatch(line))
                        Add(report, "REVIEW", "INTERPOLATED_NEW_INPUT", relative, lineNo,
                            "Possible executable new input API inside an interpolated string; inspect the expression.");
                }
            }
            report.result = report.findingsTruncated || report.scriptScanTruncated ? "INCOMPLETE" :
                report.definiteRisks > 0 ? "RISKS_FOUND" :
                report.uncertainRisks > 0 ? "REVIEW_REQUIRED" : "NO_OBVIOUS_RISK_DETECTED";
            return report;
        }
    }
}
#endif
