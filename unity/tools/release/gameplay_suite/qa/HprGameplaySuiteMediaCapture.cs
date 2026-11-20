// Editor-only, non-shipping QA: render the REAL imported Unity demo scene to PNG.
// No AI imagery, generated mockups, external artwork or changes to the buyer archive.
#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using HPR.GameplaySuite;

public static class HprGameplaySuiteMediaCapture
{
    public static void Run()
    {
        const string scene = "Assets/HPRGameplaySuite/Demo/GameplaySuiteShowcase.unity";
        string output = Environment.GetEnvironmentVariable("HPR_SUITE_MEDIA_DIR");
        if (string.IsNullOrWhiteSpace(output))
            throw new InvalidOperationException("HPR_SUITE_MEDIA_DIR not set");
        EditorSceneManager.OpenScene(scene, OpenSceneMode.Single);
        Camera camera = Camera.main;
        if (camera == null) throw new InvalidOperationException("Imported scene missing Main Camera");
        Directory.CreateDirectory(output);
        CameraShot(camera, Path.Combine(output, "01-arena-actual-unity-camera.png"));
        Vector3 initialPos = camera.transform.position;
        Quaternion initialRotation = camera.transform.rotation;
        try
        {
            camera.transform.position = new Vector3(5.0f, 9f, -9f);
            camera.transform.LookAt(new Vector3(0, 0, 0));
            CameraShot(camera, Path.Combine(output, "02-encounter-actual-unity-camera.png"));
        }
        finally
        {
            camera.transform.SetPositionAndRotation(initialPos, initialRotation);
        }
        Debug.Log("HPR_MEDIA_CAPTURE_PASS: camera rendered real imported Unity scene to PNG");
    }

    private static void CameraShot(Camera camera, string path)
    {
        RenderTexture target = null;
        Texture2D pixels = null;
        RenderTexture original = camera.targetTexture;
        RenderTexture previous = RenderTexture.active;
        try
        {
            target = new RenderTexture(1600, 900, 24, RenderTextureFormat.ARGB32);
            target.Create();
            if (!target.IsCreated()) throw new InvalidOperationException("Graphics render target creation failed");
            camera.targetTexture = target;
            camera.Render();
            RenderTexture.active = target;
            pixels = new Texture2D(1600, 900, TextureFormat.RGB24, false);
            pixels.ReadPixels(new Rect(0, 0, 1600, 900), 0, 0);
            pixels.Apply();
            byte[] png = pixels.EncodeToPNG();
            if (png.Length < 20000) throw new InvalidOperationException("Unexpectedly small Unity camera image");
            File.WriteAllBytes(path, png);
            Debug.Log("HPR_MEDIA_SAVED " + path + " " + png.Length + " bytes");
        }
        finally
        {
            camera.targetTexture = original;
            RenderTexture.active = previous;
            if (pixels != null) UnityEngine.Object.DestroyImmediate(pixels);
            if (target != null) { target.Release(); UnityEngine.Object.DestroyImmediate(target); }
        }
    }
}
#endif
