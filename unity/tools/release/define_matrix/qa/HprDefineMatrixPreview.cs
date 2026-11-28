// Private screenshot fixture. Never include in customer archive.
#if UNITY_EDITOR && UNITY_6000_1_OR_NEWER
using System;
using UnityEditor;
using UnityEngine;
using HPR.DefineMatrix;

public static class HprDefineMatrixPreview
{
    public static void Open()
    {
        var window = HprDefineMatrixWindow.OpenWindow();
        if (window == null) throw new InvalidOperationException("Define Matrix window unavailable");
        window.position = new Rect(140f, 80f, 980f, 730f);
        window.Focus();
        window.Repaint();
        Debug.Log("HPR_DEFINE_PREVIEW_WINDOW_OPENED");
    }
}
#endif
