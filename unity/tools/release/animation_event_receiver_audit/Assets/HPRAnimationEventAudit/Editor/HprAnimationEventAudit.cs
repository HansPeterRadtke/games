// Copyright (c) Multiverse. Original private pre-release Unity Editor extension.
// Read-only diagnostic; does NOT repair events or modify clips/prefabs/controllers.
#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using UnityEditor;
using UnityEngine;

namespace HPR.AnimationEventAudit
{
    [Serializable]
    public sealed class HprEventFinding
    {
        public string severity, code, prefabPath, animatorPath, clipPath, clipName;
        public string functionName, explanation;
        public float eventTime;
        public int eventIndex;
    }

    [Serializable]
    public sealed class HprEventAuditReport
    {
        public string schema = "hpr-animation-event-audit-v1";
        public string status = "NOT_RUN";
        public string unityVersion;
        public string scannedUtc;
        public string scope = "Saved prefab Animator controllers, referenced clips and attached MonoBehaviour event receivers under Assets only.";
        public string limitations = "Not a Player/runtime test. No scene-only animators, legacy Animation, runtime controllers, dynamic added receivers, external package prefabs, or unseen clips. Signature matching is conservative and cannot guarantee event delivery under blending or frame skipping.";
        public int prefabsInspected, animatorsWithControllers, clipsInspected, animationEventsInspected;
        public List<HprEventFinding> findings = new List<HprEventFinding>();
        public int failures, reviews;
    }

    public static class HprEventReceiverScanner
    {
        public const int MaxPrefabs = 1500;
        public const int MaxClips = 6000;
        public const int MaxEvents = 12000;
        public const int MaxFindings = 3000;
        private const BindingFlags ReceiverFlags = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance;

        private static void Add(HprEventAuditReport r, string severity, string code,
            string prefab, string animator, string clipPath, string clipName,
            string name, float time, int index, string explanation)
        {
            if (r.findings.Count >= MaxFindings)
                throw new InvalidOperationException("Finding limit reached: scan cannot be reported complete.");
            r.findings.Add(new HprEventFinding { severity = severity, code = code,
                prefabPath = prefab, animatorPath = animator, clipPath = clipPath,
                clipName = clipName, functionName = name, eventTime = time,
                eventIndex = index, explanation = explanation });
            if (severity == "FAIL") r.failures++;
            else r.reviews++;
        }

        private static bool ValidReceiver(MethodInfo method)
        {
            if (method == null || method.IsStatic || method.IsAbstract ||
                method.ContainsGenericParameters || method.ReturnType != typeof(void)) return false;
            var args = method.GetParameters();
            if (args.Length == 0) return true;
            if (args.Length != 1 || args[0].IsOut || args[0].ParameterType.IsByRef) return false;
            Type parameter = args[0].ParameterType;
            return parameter == typeof(int) || parameter == typeof(float) ||
                parameter == typeof(string) || parameter == typeof(AnimationEvent) ||
                // Unity 6.6 adds a non-allocating ref struct callback parameter.
                // Compare the actual loaded method type to preserve source
                // compatibility with older Unity versions lacking the class.
                parameter.FullName == "UnityEngine.AnimationEventInfo" ||
                typeof(UnityEngine.Object).IsAssignableFrom(parameter);
        }

        public static string ReceiverSignatureStatus(IEnumerable<MethodInfo> methods, string name)
        {
            if (string.IsNullOrWhiteSpace(name)) return "EMPTY";
            if (methods == null) return "UNKNOWN";
            var matches = methods.Where(m => m != null && m.Name == name).ToArray();
            if (matches.Length == 0) return "MISSING";
            return matches.Any(ValidReceiver) ? "FOUND" : "BAD_SIGNATURE";
        }

        private static string RelativeTransformPath(Transform item, Transform prefabRoot)
        {
            if (item == prefabRoot) return "(prefab root)";
            var parts = new List<string>();
            var current = item;
            while (current != null && current != prefabRoot)
            {
                parts.Add(current.name);
                current = current.parent;
            }
            parts.Reverse();
            return string.Join("/", parts);
        }

        public static HprEventAuditReport Scan(string folder = "Assets")
        {
            var report = new HprEventAuditReport { unityVersion = Application.unityVersion,
                scannedUtc = DateTimeOffset.UtcNow.ToString("O") };
            report.scope = "Saved prefab Animator clips and same-GameObject receivers under " + (folder ?? "(null)");
            try
            {
                if (EditorApplication.isCompiling || EditorApplication.isUpdating)
                    throw new InvalidOperationException("The Editor is compiling or importing. Rescan after it finishes.");
                if (string.IsNullOrEmpty(folder) ||
                    (folder != "Assets" && !folder.StartsWith("Assets/", StringComparison.Ordinal)) ||
                    !AssetDatabase.IsValidFolder(folder))
                    throw new InvalidOperationException("Choose an actual saved folder under Assets.");
                string[] ids = AssetDatabase.FindAssets("t:Prefab", new[] { folder });
                if (ids == null || ids.Length > MaxPrefabs)
                    throw new InvalidOperationException("Prefab count exceeds scan limit or discovery failed. Choose a smaller Assets subfolder.");
                var paths = ids.Select(AssetDatabase.GUIDToAssetPath)
                    .Where(p => !string.IsNullOrEmpty(p))
                    .Distinct(StringComparer.Ordinal).OrderBy(p => p, StringComparer.Ordinal).ToArray();
                if (paths.Length != ids.Length)
                    throw new InvalidOperationException("Prefab discovery has missing or duplicate identifiers.");
                foreach (string path in paths)
                {
                    var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(path);
                    if (prefab == null) throw new InvalidOperationException("Cannot load prefab: " + path);
                    report.prefabsInspected++;
                    foreach (Animator animator in prefab.GetComponentsInChildren<Animator>(true))
                    {
                        if (animator == null || animator.runtimeAnimatorController == null) continue;
                        report.animatorsWithControllers++;
                        var clips = animator.runtimeAnimatorController.animationClips;
                        if (clips == null) throw new InvalidOperationException("Cannot inspect controller clips: " + path);
                        // Identity comparison by actual clip references avoids
                        // deprecated Unity InstanceID APIs in current Editors.
                        var unique = new HashSet<AnimationClip>();
                        foreach (AnimationClip clip in clips)
                        {
                            if (clip == null || !unique.Add(clip)) continue;
                            if (++report.clipsInspected > MaxClips)
                                throw new InvalidOperationException("Clip scan limit reached.");
                            string clipAssetPath = AssetDatabase.GetAssetPath(clip);
                            if (string.IsNullOrEmpty(clipAssetPath))
                                throw new InvalidOperationException("Runtime-created clip cannot be certified: " + clip.name);
                            var events = AnimationUtility.GetAnimationEvents(clip);
                            if (events == null) throw new InvalidOperationException("Event list unavailable: " + clipAssetPath);
                            var firstFunctionAtTime = new Dictionary<float, string>();
                            MonoBehaviour[] receivers = animator.GetComponents<MonoBehaviour>();
                            if (receivers == null) throw new InvalidOperationException("Receiver list unavailable: " + path);
                            string hierarchy = RelativeTransformPath(animator.transform, prefab.transform);
                            if (receivers.Any(receiver => receiver == null))
                                Add(report, "REVIEW", "MISSING_RECEIVER_COMPONENT", path, hierarchy,
                                    clipAssetPath, clip.name, "", -1, -1,
                                    "Missing attached script on Animator GameObject; event lookup may be incomplete.");
                            var methods = new List<MethodInfo>();
                            foreach (MonoBehaviour receiver in receivers)
                            {
                                if (receiver == null) continue;
                                methods.AddRange(receiver.GetType().GetMethods(ReceiverFlags));
                            }
                            for (int i = 0; i < events.Length; i++)
                            {
                                AnimationEvent e = events[i];
                                if (++report.animationEventsInspected > MaxEvents)
                                    throw new InvalidOperationException("Event scan limit reached.");
                                if (e == null)
                                {
                                    Add(report, "FAIL", "NULL_EVENT", path, hierarchy, clipAssetPath,
                                        clip.name, "", -1, i, "An event entry could not be read.");
                                    continue;
                                }
                                string name = e.functionName ?? "";
                                string state = ReceiverSignatureStatus(methods, name);
                                if (state == "EMPTY")
                                    Add(report, "FAIL", "EMPTY_FUNCTION_NAME", path, hierarchy, clipAssetPath,
                                        clip.name, name, e.time, i,
                                        "Animation Event has no function selected; this can cause a receiver warning.");
                                else if (state == "MISSING")
                                    Add(report, "FAIL", "NO_RECEIVER_METHOD", path, hierarchy, clipAssetPath,
                                        clip.name, name, e.time, i,
                                        "No attached MonoBehaviour on this Animator GameObject declares the named function.");
                                else if (state == "BAD_SIGNATURE")
                                    Add(report, "FAIL", "INVALID_RECEIVER_SIGNATURE", path, hierarchy, clipAssetPath,
                                        clip.name, name, e.time, i,
                                        "A method with this name exists but has no supported void/zero-or-one-argument signature.");
                                else if (state == "UNKNOWN")
                                    Add(report, "REVIEW", "RECEIVER_UNCERTAIN", path, hierarchy, clipAssetPath,
                                        clip.name, name, e.time, i, "Receiver method inspection unavailable.");
                                // Unity's Animation window can visually stack markers at
                                // one time even when the hidden callback name differs.
                                // This is review-only: simultaneous events can be intentional.
                                if (firstFunctionAtTime.TryGetValue(e.time, out string otherFunction))
                                    Add(report, "REVIEW", "OVERLAPPING_EVENT_MARKERS", path, hierarchy,
                                        clipAssetPath, clip.name, name, e.time, i,
                                        "Another event, '" + otherFunction + "', shares this exact timestamp. " +
                                        "Markers can visually overlap, including when callback names differ. " +
                                        "Both may be intentional; inspect the clip timeline before changing them.");
                                else
                                    firstFunctionAtTime.Add(e.time, name);
                                if (float.IsNaN(e.time) || float.IsInfinity(e.time) || e.time < 0 || e.time > clip.length + 0.001f)
                                    Add(report, "REVIEW", "EVENT_TIME_OUTSIDE_CLIP", path, hierarchy,
                                        clipAssetPath, clip.name, name, e.time, i,
                                        "Event time is outside the clip's saved length; inspect the importer.");
                            }
                        }
                    }
                }
                if (report.animationEventsInspected == 0)
                    Add(report, "REVIEW", "NO_TESTABLE_EVENTS", "Assets", "", "", "", "", -1, -1,
                        "No saved prefab Animator-linked animation events were found. This is not proof that the project has none.");
                report.status = report.failures > 0 ? "FAIL" : report.reviews > 0 ? "REVIEW" : "CLEAR_WITH_LIMITS";
            }
            catch (Exception error)
            {
                report.status = "INCOMPLETE";
                AddIncompleteSafely(report, error.GetType().Name + ": " + error.Message);
            }
            return report;
        }

        private static void AddIncompleteSafely(HprEventAuditReport report, string reason)
        {
            if (report.findings.Count >= MaxFindings) report.findings.RemoveAt(report.findings.Count - 1);
            report.findings.Add(new HprEventFinding { severity = "INCOMPLETE", code = "SCAN_UNVERIFIED",
                prefabPath = "Assets", explanation = reason });
        }

        public static void ExportNewJson(string destination, HprEventAuditReport report)
        {
            if (report == null || report.status == "NOT_RUN")
                throw new InvalidOperationException("Run an audit before export.");
            if (string.IsNullOrWhiteSpace(destination) ||
                !destination.EndsWith(".json", StringComparison.OrdinalIgnoreCase))
                throw new ArgumentException("Choose a new .json output path.");
            // Avoid Unity importing private project paths/report payloads.
            string project = Path.GetFullPath(Path.GetDirectoryName(Application.dataPath));
            string target = Path.GetFullPath(destination);
            string prefix = project.EndsWith(Path.DirectorySeparatorChar.ToString()) ?
                project : project + Path.DirectorySeparatorChar;
            if (target.StartsWith(prefix, StringComparison.OrdinalIgnoreCase) ||
                string.Equals(project, target, StringComparison.OrdinalIgnoreCase))
                throw new IOException("Create the private audit report outside the Unity project.");
            byte[] encoded = new UTF8Encoding(false).GetBytes(JsonUtility.ToJson(report, true) + "\n");
            if (encoded.Length > 2 * 1024 * 1024)
                throw new InvalidOperationException("Audit report exceeds the supported size limit.");
            using (var file = new FileStream(destination, FileMode.CreateNew, FileAccess.Write, FileShare.None))
                file.Write(encoded, 0, encoded.Length);
        }
    }

    public sealed class HprAnimationEventAuditWindow : EditorWindow
    {
        private HprEventAuditReport report;
        private Vector2 scroll;
        private bool showReview = true;
        private bool showFailures = true;
        private DefaultAsset selectedFolder;
        private string status = "Run a new read-only scan to inspect saved prefab receivers.";

        [MenuItem("Tools/HPR/Animation Event Receiver Audit")]
        public static HprAnimationEventAuditWindow Open()
        {
            var window = GetWindow<HprAnimationEventAuditWindow>("Animation Event Audit");
            window.minSize = new Vector2(780, 430);
            window.Show();
            return window;
        }
        private void OnGUI()
        {
            EditorGUILayout.LabelField("HPR ANIMATION EVENT RECEIVER AUDIT", EditorStyles.boldLabel);
            EditorGUILayout.HelpBox("Inspect saved prefab Animator clips and same-GameObject script receivers. " +
                "No changes, automatic fixes, builds or external requests. Scans do not certify runtime event delivery.",
                MessageType.Info);
            selectedFolder = (DefaultAsset)EditorGUILayout.ObjectField(
                "Scan folder (optional)", selectedFolder, typeof(DefaultAsset), false);
            if (GUILayout.Button("Scan saved prefab animation events", GUILayout.Height(29)))
            {
                string folder = selectedFolder == null ? "Assets" : AssetDatabase.GetAssetPath(selectedFolder);
                report = HprEventReceiverScanner.Scan(folder);
                status = "Completed read-only inspection: " + report.status;
            }
            if (report == null)
            {
                EditorGUILayout.HelpBox(status, MessageType.Info);
                return;
            }
            var message = report.status == "INCOMPLETE" || report.status == "FAIL" ? MessageType.Error :
                report.status == "REVIEW" ? MessageType.Warning : MessageType.Info;
            EditorGUILayout.LabelField("Scope: " + report.scope, EditorStyles.wordWrappedLabel);
            EditorGUILayout.HelpBox("Result: " + report.status + "   ·   " + report.prefabsInspected +
                " prefabs   ·   " + report.animatorsWithControllers + " animators   ·   " +
                report.clipsInspected + " clips   ·   " + report.animationEventsInspected +
                " events   ·   " + report.failures + " failures   ·   " + report.reviews + " reviews", message);
            EditorGUILayout.BeginHorizontal();
            showFailures = EditorGUILayout.ToggleLeft("Show failures", showFailures, GUILayout.Width(135));
            showReview = EditorGUILayout.ToggleLeft("Show reviews and incomplete", showReview);
            EditorGUILayout.EndHorizontal();
            scroll = EditorGUILayout.BeginScrollView(scroll);
            int visible = 0;
            foreach (HprEventFinding item in report.findings)
            {
                if (item.severity == "FAIL" && !showFailures ||
                    item.severity != "FAIL" && !showReview) continue;
                visible++;
                EditorGUILayout.BeginVertical(EditorStyles.helpBox);
                EditorGUILayout.LabelField(item.severity + "  |  " + item.code, EditorStyles.boldLabel);
                EditorGUILayout.LabelField("Prefab: " + item.prefabPath, EditorStyles.wordWrappedLabel);
                if (!string.IsNullOrEmpty(item.animatorPath))
                    EditorGUILayout.LabelField("Animator: " + item.animatorPath, EditorStyles.wordWrappedLabel);
                if (!string.IsNullOrEmpty(item.clipPath))
                    EditorGUILayout.LabelField("Clip: " + item.clipPath + "  ·  " + item.clipName,
                        EditorStyles.wordWrappedLabel);
                if (item.eventIndex >= 0)
                    EditorGUILayout.LabelField("Event #" + (item.eventIndex + 1) + ": " +
                        (string.IsNullOrEmpty(item.functionName) ? "(no function)" : item.functionName) +
                        " at " + item.eventTime.ToString("0.###") + " seconds");
                EditorGUILayout.HelpBox(item.explanation, item.severity == "FAIL" ||
                    item.severity == "INCOMPLETE" ? MessageType.Error : MessageType.Warning);
                if (!string.IsNullOrEmpty(item.prefabPath) && item.prefabPath.StartsWith("Assets/", StringComparison.Ordinal))
                    if (GUILayout.Button("Locate saved prefab", GUILayout.Width(165)))
                    {
                        var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(item.prefabPath);
                        if (prefab != null) EditorGUIUtility.PingObject(prefab);
                    }
                EditorGUILayout.EndVertical();
            }
            EditorGUILayout.EndScrollView();
            if (visible == 0) EditorGUILayout.LabelField("No findings under the selected filters.");
            EditorGUILayout.HelpBox(report.limitations, MessageType.Info);
            if (GUILayout.Button("Export a NEW read-only JSON report…", GUILayout.Height(26)))
            {
                string file = EditorUtility.SaveFilePanel("Create a new private audit report",
                    "", "hpr-animation-event-audit", "json");
                if (!string.IsNullOrEmpty(file))
                {
                    try { HprEventReceiverScanner.ExportNewJson(file, report);
                        status = "Created report outside Unity. Review project paths before sharing."; }
                    catch (Exception ex) { status = "Export refused: " + ex.Message; }
                }
            }
            EditorGUILayout.HelpBox(status, MessageType.None);
        }
    }
}
#endif
