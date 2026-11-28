// PRIVATE source + real Unity integration fixture; excluded from exported product.
#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Security.Cryptography;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;
using HPR.AnimationEventAudit;

public static class HprEventAuditNativeQa
{
    private const string Root = "Assets/HPRPrivateEventAuditQA";
    private static string ExpectedReceipt => Environment.GetEnvironmentVariable("HPR_EVENT_AUDIT_RECEIPT");
    private static void Require(bool condition, string explanation)
    { if (!condition) throw new InvalidOperationException(explanation); }
    private static string Hash(string path) => Convert.ToBase64String(SHA256.Create().ComputeHash(File.ReadAllBytes(path)));

    public static void Export()
    {
        Require(Application.isBatchMode, "Private native exporter only");
        string archive = Environment.GetEnvironmentVariable("HPR_EVENT_AUDIT_ARCHIVE");
        Require(!string.IsNullOrEmpty(archive) && !File.Exists(archive), "New private archive path required");
        AssetDatabase.ExportPackage("Assets/HPRAnimationEventAudit", archive, ExportPackageOptions.Recurse);
        Require(new FileInfo(archive).Length > 4000, "Actual Unity package export unavailable");
        Debug.Log("HPR_ANIMATION_EVENT_EXPORT_PASS");
    }

    private static void Make(string label, string function, string secondFunction = null)
    {
        var clip = new AnimationClip { name = label, frameRate = 60f };
        clip.SetCurve("", typeof(Transform), "m_LocalPosition.x",
            AnimationCurve.Linear(0f, 0f, 1f, 0.1f));
        string clipPath = Root + "/" + label + ".anim";
        AssetDatabase.CreateAsset(clip, clipPath);
        var one = new AnimationEvent { functionName = function, time = .25f };
        AnimationUtility.SetAnimationEvents(clip, secondFunction != null ?
            new[] { one, new AnimationEvent { functionName = secondFunction, time = .25f } } : new[] { one });
        string controllerPath = Root + "/" + label + ".controller";
        var controller = AnimatorController.CreateAnimatorControllerAtPath(controllerPath);
        Require(controller != null && controller.layers.Length > 0, "Unity did not create Animator controller");
        var state = controller.layers[0].stateMachine.AddState(label);
        state.motion = clip;
        EditorUtility.SetDirty(controller);
        var go = new GameObject(label + "-Animator");
        try
        {
            var animator = go.AddComponent<Animator>();
            animator.runtimeAnimatorController = controller;
            go.AddComponent<HprEventAuditFixtureReceiver>();
            var prefab = PrefabUtility.SaveAsPrefabAsset(go, Root + "/" + label + ".prefab");
            Require(prefab != null, "Actual prefab save failed");
        }
        finally { UnityEngine.Object.DestroyImmediate(go); }
    }

    public static void Run()
    {
        Require(Application.isBatchMode, "Native private QA uses batch mode");
        Require(!AssetDatabase.IsValidFolder(Root), "Use a fresh private buyer project without prior fixture");
        Require(!string.IsNullOrEmpty(ExpectedReceipt) && !File.Exists(ExpectedReceipt),
            "New test receipt required");
        Directory.CreateDirectory(Root);
        AssetDatabase.Refresh();
        // Independent method signature checks against compiled real attached
        // MonoBehaviour receiver type, including Unity 6.6 event info type.
        var receiverMethods = typeof(HprEventAuditFixtureReceiver).GetMethods(
            BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
        Require(HprEventReceiverScanner.ReceiverSignatureStatus(receiverMethods, "OnStep") == "FOUND" &&
            HprEventReceiverScanner.ReceiverSignatureStatus(receiverMethods, "OnHiddenValid") == "FOUND" &&
            HprEventReceiverScanner.ReceiverSignatureStatus(receiverMethods, "TakesFloat") == "FOUND" &&
            HprEventReceiverScanner.ReceiverSignatureStatus(receiverMethods, "TakesEvent") == "FOUND" &&
            HprEventReceiverScanner.ReceiverSignatureStatus(receiverMethods, "TwoArguments") == "BAD_SIGNATURE" &&
            HprEventReceiverScanner.ReceiverSignatureStatus(receiverMethods, "ReturnsAValue") == "BAD_SIGNATURE" &&
            HprEventReceiverScanner.ReceiverSignatureStatus(receiverMethods, "DoesNotExist") == "MISSING" &&
            HprEventReceiverScanner.ReceiverSignatureStatus(receiverMethods, "") == "EMPTY",
            "Compiled real receiver method signature classification failed");
#if UNITY_6000_6_OR_NEWER
        Require(HprEventReceiverScanner.ReceiverSignatureStatus(receiverMethods, "TakesEventInfo") == "FOUND",
            "Valid current Unity AnimationEventInfo ref struct receiver not recognized");
#endif
        Make("Good", "OnStep");
        Make("Missing", "DoesNotExist");
        Make("Signature", "TwoArguments");
        Make("Duplicate", "OnStep", "OnStep");
        // A different callback name at the SAME timestamp is the actual
        // hidden marker reported by users; unlike identical events this
        // fixture also has an otherwise-missing second receiver.
        Make("HiddenOtherName", "OnStep", "DoesNotExist");
        AssetDatabase.SaveAssets();
        string[] protectedPaths = Directory.GetFiles(Root, "*", SearchOption.TopDirectoryOnly)
            .Where(p => p.EndsWith(".anim") || p.EndsWith(".prefab") ||
                p.EndsWith(".controller")).OrderBy(p => p).ToArray();
        Require(protectedPaths.Length == 15, "Expected five real prefabs, clips and controllers");
        string[] before = protectedPaths.Select(Hash).ToArray();
        string manifestBefore = Hash("Packages/manifest.json");
        var report = HprEventReceiverScanner.Scan();
        Require(report.status == "FAIL" && report.prefabsInspected == 5 &&
            report.animatorsWithControllers == 5 && report.animationEventsInspected == 7,
            "Actual native scan failed to cover five saved prefab/controller/event fixtures");
        var folderReport = HprEventReceiverScanner.Scan(Root);
        Require(folderReport.status == report.status && folderReport.prefabsInspected == 5 &&
            folderReport.findings.Count == report.findings.Count &&
            folderReport.scope.Contains(Root),
            "Folder-scoped native scan failed to match project-wide real prefab results");
        var invalidScope = HprEventReceiverScanner.Scan("Packages");
        Require(invalidScope.status == "INCOMPLETE" &&
                invalidScope.findings.Any(x => x.code == "SCAN_UNVERIFIED"),
            "Unsupported non-Assets folder was incorrectly reported as successfully scanned");
        Require(report.findings.Count(x => x.code == "NO_RECEIVER_METHOD") == 2 &&
            report.findings.Count(x => x.code == "INVALID_RECEIVER_SIGNATURE") == 1 &&
            report.findings.Count(x => x.code == "OVERLAPPING_EVENT_MARKERS") == 2 &&
            report.findings.Any(x => x.code == "OVERLAPPING_EVENT_MARKERS" &&
                x.prefabPath.EndsWith("/HiddenOtherName.prefab") &&
                x.explanation.Contains("'OnStep'")),
            "Native scan missed hidden differently named event or other receiver contracts");
        Require(report.findings.Count == 5 && report.failures == 3 && report.reviews == 2,
            "Actual real prefab finding classification/count incorrect");
        var reportPath = Path.ChangeExtension(ExpectedReceipt, ".json");
        HprEventReceiverScanner.ExportNewJson(reportPath, report);
        string reportText = File.ReadAllText(reportPath);
        Require(reportText.Contains("NO_RECEIVER_METHOD") &&
            reportText.Contains("OVERLAPPING_EVENT_MARKERS") &&
            reportText.Contains("HPRPrivateEventAuditQA"), "Reported JSON lost native prefab evidence");
        string reportBefore = Hash(reportPath);
        bool refusedOverwrite = false;
        try { HprEventReceiverScanner.ExportNewJson(reportPath, report); }
        catch (IOException) { refusedOverwrite = true; }
        Require(refusedOverwrite && Hash(reportPath) == reportBefore, "Audit overwrote existing JSON output");
        string illegalOutput = "ProjectSettings/HprForbiddenEventAudit.json";
        bool refusedProjectWrite = false;
        try { HprEventReceiverScanner.ExportNewJson(illegalOutput, report); }
        catch (IOException) { refusedProjectWrite = true; }
        Require(refusedProjectWrite && !File.Exists(illegalOutput), "Audit allowed writing inside Unity project");
        var window = HprAnimationEventAuditWindow.Open();
        Require(window != null, "Real installed EditorWindow failed to open");
        try
        {
            const BindingFlags flags = BindingFlags.Instance | BindingFlags.NonPublic;
            typeof(HprAnimationEventAuditWindow).GetField("report", flags).SetValue(window, report);
            var current = (HprEventAuditReport)typeof(HprAnimationEventAuditWindow)
                .GetField("report", flags).GetValue(window);
            Require(current != null && current.failures == 3 && current.reviews == 2,
                "Native Editor window lost its receiver findings");
        }
        finally { window.Close(); }
        Require(manifestBefore == Hash("Packages/manifest.json") &&
            before.SequenceEqual(protectedPaths.Select(Hash)),
            "Read-only scan/report/window changed a prefab/clip/controller or package manifest");
        File.WriteAllText(ExpectedReceipt,
            "HPR_ANIMATION_EVENT_REAL_NATIVE_PASS\n" +
            "Unity=" + Application.unityVersion + "\n" +
            "real_prefabs=5\nreal_clips=5\nevents_scanned=7\n" +
            "missing_receiver=2\ninvalid_signature=1\noverlapping_same_time=2\n" +
            "overlap_with_different_name=PASS\nscoped_folder_scan=PASS\n" +
            "non_assets_scope_rejected=PASS\n" +
            "actual_editor_window=PASS\nreceiver_signatures=PASS\n" +
            "current_unity_event_info_receiver=PASS\n" +
            "create_only_json=PASS\nproject_write_rejected=PASS\n" +
            "real_asset_hashes_and_manifest_unchanged=PASS\n");
        Debug.Log("HPR_ANIMATION_EVENT_REAL_NATIVE_PASS");
    }
}
#endif
