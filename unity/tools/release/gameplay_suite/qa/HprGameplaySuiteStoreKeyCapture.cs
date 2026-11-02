// Private Unity 6.6 Editor-only QA: genuine scene camera key-image captures.
// Not part of the buyer archive or any published/approved Asset Store art.
// All output images must be visually reviewed before publisher submission.
#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class HprGameplaySuiteStoreKeyCapture
{
    private const string ScenePath =
        "Assets/HPRGameplaySuite/Demo/GameplaySuiteShowcase.unity";

    public static void Run()
    {
        string folder = Environment.GetEnvironmentVariable("HPR_STORE_KEY_MEDIA_DIR");
        string receipt = Environment.GetEnvironmentVariable("HPR_STORE_KEY_MEDIA_RECEIPT");
        if (string.IsNullOrWhiteSpace(folder) || string.IsNullOrWhiteSpace(receipt))
            throw new InvalidOperationException("Private output and receipt must be explicitly specified");

        string output = Path.GetFullPath(folder);
        string root = Directory.GetParent(Application.dataPath).FullName;
        if (output == root ||
            output.StartsWith(root + Path.DirectorySeparatorChar, StringComparison.Ordinal))
            throw new InvalidOperationException("Never create capture media inside a customer Unity project");
        if (!output.StartsWith("/data/tmp/", StringComparison.Ordinal) &&
            !output.StartsWith("/data/var/marketplace-account-setup/", StringComparison.Ordinal))
            throw new InvalidOperationException("Camera capture is restricted to this owner's private QA roots");
        // This private QA must create a NEW directory, never add a partial
        // capture to someone else's existing camera/media working directory.
        if (Directory.Exists(output) || File.Exists(output))
            throw new InvalidOperationException("Refusing existing Unity capture folder");
        for (DirectoryInfo parent = new DirectoryInfo(Path.GetDirectoryName(output));
             parent != null; parent = parent.Parent)
        {
            if (parent.Exists && (parent.Attributes & FileAttributes.ReparsePoint) != 0)
                throw new InvalidOperationException("Refusing symlinked private capture parent");
        }
        string receiptPath = Path.GetFullPath(receipt);
        if (!receiptPath.StartsWith(output + Path.DirectorySeparatorChar,
                                    StringComparison.Ordinal))
            throw new InvalidOperationException("Receipt must reside inside the new private image folder");
        if (File.Exists(receiptPath) || Directory.Exists(receiptPath))
            throw new InvalidOperationException("Refusing an existing key-art receipt");

        // The scene comes from a REAL previously imported HPR Unity package.
        // No synthetic or AI-generated art, asset regeneration or saved scene
        // editing occurs. This method only creates new private screenshot PNGs.
        EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
        Camera camera = Camera.main;
        if (camera == null)
            throw new InvalidOperationException("Imported Unity demo is missing its real Main Camera");
        Directory.CreateDirectory(output);

        string[] names = {
            "01-icon-actual-unity-camera.png",
            "02-card-actual-unity-camera.png",
            "03-cover-actual-unity-camera.png",
            "04-social-actual-unity-camera.png"
        };
        foreach (string name in names)
        {
            string path = Path.Combine(output, name);
            if (File.Exists(path) || Directory.Exists(path))
                throw new InvalidOperationException("Refusing existing key image: " + path);
        }

        Vector3 initialPosition = camera.transform.position;
        Quaternion initialRotation = camera.transform.rotation;
        float initialAspect = camera.aspect;
        try
        {
            // Distinct framing for icon, product card, cover and social art.
            // Final typography and branding are separate human art tasks.
            camera.transform.position = new Vector3(3.3f, 6f, -7f);
            camera.transform.LookAt(new Vector3(0f, 1f, 0f));
            Capture(camera, Path.Combine(output, "01-icon-actual-unity-camera.png"), 160, 160);

            camera.transform.position = new Vector3(5f, 8f, -9f);
            camera.transform.LookAt(Vector3.zero);
            Capture(camera, Path.Combine(output, "02-card-actual-unity-camera.png"), 420, 280);

            camera.transform.position = new Vector3(7f, 9f, -11f);
            camera.transform.LookAt(Vector3.zero);
            Capture(camera, Path.Combine(output, "03-cover-actual-unity-camera.png"), 1950, 1300);

            camera.transform.position = new Vector3(8f, 8f, -12f);
            camera.transform.LookAt(new Vector3(0f, 0.7f, 0f));
            Capture(camera, Path.Combine(output, "04-social-actual-unity-camera.png"), 1200, 630);
        }
        finally
        {
            camera.transform.SetPositionAndRotation(initialPosition, initialRotation);
            camera.aspect = initialAspect;
        }

        using (var receiptStream = new FileStream(receiptPath, FileMode.CreateNew,
                                                   FileAccess.Write, FileShare.None))
        using (var writer = new StreamWriter(receiptStream))
        {
            writer.Write("real_unity_imported_demo_scene=PASS\n" +
                         "icon_160x160_rendered=PASS\n" +
                         "card_420x280_rendered=PASS\n" +
                         "cover_1950x1300_rendered=PASS\n" +
                         "social_1200x630_rendered=PASS\n" +
                         "no_buyer_scene_was_saved=PASS\n" +
                         "human_marketing_visual_approval=NOT_PERFORMED\n");
        }
        Debug.Log("HPR_STORE_KEY_CAPTURE_FROM_ACTUAL_UNITY_SCENE_PASS");
    }

    private static void Capture(Camera camera, string path, int width, int height)
    {
        if (File.Exists(path))
            throw new InvalidOperationException("Refusing existing key image: " + path);
        RenderTexture target = null;
        Texture2D pixels = null;
        RenderTexture original = camera.targetTexture;
        RenderTexture previous = RenderTexture.active;
        float oldAspect = camera.aspect;
        try
        {
            target = new RenderTexture(width, height, 24, RenderTextureFormat.ARGB32);
            target.Create();
            if (!target.IsCreated())
                throw new InvalidOperationException("Unity camera RenderTexture allocation failed");
            camera.targetTexture = target;
            camera.aspect = (float)width / height;
            // Unity URP 17.6 requires warming the initial Lit shader render.
            // The prior real capture recorded a black first arena frame.
            camera.Render();
            camera.Render();
            RenderTexture.active = target;
            pixels = new Texture2D(width, height, TextureFormat.RGB24, false);
            pixels.ReadPixels(new Rect(0, 0, width, height), 0, 0);
            pixels.Apply();
            byte[] png = pixels.EncodeToPNG();
            if (png == null || png.Length < 2000)
                throw new InvalidOperationException("Unity camera image was blank or unexpectedly tiny");
            // O_EXCL / CreateNew refuses even a dangling symlink and protects
            // against a race between the initial path check and the write.
            using (var outputFile = new FileStream(path, FileMode.CreateNew,
                                                  FileAccess.Write, FileShare.None))
                outputFile.Write(png, 0, png.Length);
            Debug.Log("HPR_STORE_KEY_IMAGE_SAVED " + path + " " +
                      width + "x" + height + " " + png.Length + " bytes");
        }
        finally
        {
            camera.targetTexture = original;
            camera.aspect = oldAspect;
            RenderTexture.active = previous;
            if (pixels != null)
                UnityEngine.Object.DestroyImmediate(pixels);
            if (target != null)
            {
                target.Release();
                UnityEngine.Object.DestroyImmediate(target);
            }
        }
    }
}
#endif
