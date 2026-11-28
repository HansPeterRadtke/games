// PRIVATE native GUI screenshot QA. Does not ship with buyer archive.
#if UNITY_EDITOR
using System;
using System.Reflection;
using UnityEditor;
using UnityEngine;
using HPR.AnimationEventAudit;
public static class HprEventAuditPreview
{
    private static HprAnimationEventAuditWindow monitoredWindow;
    private static string firstScanTime;
    private static readonly FieldInfo ReportField = typeof(HprAnimationEventAuditWindow).GetField(
        "report", BindingFlags.Instance | BindingFlags.NonPublic);

    private static void DetectRealButtonRescan()
    {
        if (monitoredWindow == null) { EditorApplication.update -= DetectRealButtonRescan; return; }
        var current = (HprEventAuditReport)ReportField.GetValue(monitoredWindow);
        if (current == null || current.scannedUtc == firstScanTime) return;
        if (current.status != "FAIL" || current.failures != 3 || current.reviews != 2)
            throw new InvalidOperationException("Actual rescan button returned an incorrect native result");
        EditorApplication.update -= DetectRealButtonRescan;
        Debug.Log("HPR_ANIMATION_EVENT_REAL_BUTTON_RESCAN_PASS");
    }

    public static void Open()
    {
        var report = HprEventReceiverScanner.Scan();
        if (report.status != "FAIL" || report.failures != 3 || report.reviews != 2)
            throw new InvalidOperationException("Actual saved prefab fixture is missing or changed");
        var window = HprAnimationEventAuditWindow.Open();
        const BindingFlags flags = BindingFlags.Instance | BindingFlags.NonPublic;
        typeof(HprAnimationEventAuditWindow).GetField("report", flags).SetValue(window, report);
        monitoredWindow = window;
        firstScanTime = report.scannedUtc;
        EditorApplication.update += DetectRealButtonRescan;
        window.position = new Rect(120, 80, 1100, 825);
        window.Focus(); window.Repaint();
        Debug.Log("HPR_ANIMATION_EVENT_REAL_PREVIEW_READY");
    }
}
#endif
