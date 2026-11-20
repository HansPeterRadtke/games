#if UNITY_EDITOR
using System;
using System.IO;
using System.Reflection;
using HPR.InputReadiness;
using UnityEditor;
using UnityEngine;

// Private, actual Unity Editor screenshot setup. No synthetic screenshot artwork
// and no UI dialog acceptance: the report is computed from this real project.
public static class HprInputEditorPreview
{
    public static void Show()
    {
        if (Application.isBatchMode) throw new InvalidOperationException("Graphical Unity Editor required");
        var w = EditorWindow.GetWindow<HprInputReadinessAudit>();
        w.titleContent = new GUIContent("HPR Input Compatibility Audit");
        w.position = new Rect(90f, 115f, 1100f, 720f);
        w.Show();
        w.CreateGUI();
        var report = HprInputReadinessAudit.Analyze(Directory.GetParent(Application.dataPath).FullName);
        var type = typeof(HprInputReadinessAudit);
        var flags = BindingFlags.Instance | BindingFlags.NonPublic;
        type.GetField("lastReport", flags).SetValue(w, report);
        type.GetMethod("ShowReport", flags).Invoke(w, null);
        w.Repaint();
        w.Focus();
        Debug.Log("HPR_UI_ACTUAL_EDITOR_PREVIEW_READY mode=" + report.inputHandling +
                  " scripts=" + report.scriptsRead + " definite_risks=" + report.definiteRisks +
                  " uncertain=" + report.uncertainRisks);
    }
}
#endif
