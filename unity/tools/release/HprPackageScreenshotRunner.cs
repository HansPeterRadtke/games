using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace HPR
{
    public static class HprPackageScreenshotRunner
    {
        public static void CaptureFromEnvironment()
        {
            string? scenePath = Environment.GetEnvironmentVariable("HPR_SCREENSHOT_SCENE");
            string? outputPath = Environment.GetEnvironmentVariable("HPR_SCREENSHOT_OUTPUT");
            string? widthText = Environment.GetEnvironmentVariable("HPR_SCREENSHOT_WIDTH");
            string? heightText = Environment.GetEnvironmentVariable("HPR_SCREENSHOT_HEIGHT");

            if (string.IsNullOrWhiteSpace(scenePath) || string.IsNullOrWhiteSpace(outputPath))
            {
                Debug.LogError("Missing HPR_SCREENSHOT_SCENE or HPR_SCREENSHOT_OUTPUT environment variable.");
                EditorApplication.Exit(1);
                return;
            }

            int width = ParseDimension(widthText, 1920);
            int height = ParseDimension(heightText, 1080);

            try
            {
                EditorSceneManager.OpenScene(scenePath, OpenSceneMode.Single);
                Camera camera = GetOrCreateCaptureCamera();
                byte[] png = Render(camera, width, height);

                string? dir = Path.GetDirectoryName(outputPath);
                if (!string.IsNullOrEmpty(dir))
                {
                    Directory.CreateDirectory(dir);
                }

                File.WriteAllBytes(outputPath, png);
                AssetDatabase.Refresh();
                Debug.Log($"Saved screenshot to {outputPath}");
                EditorApplication.Exit(0);
            }
            catch (Exception ex)
            {
                Debug.LogException(ex);
                EditorApplication.Exit(1);
            }
        }

        private static int ParseDimension(string? text, int fallback)
        {
            return int.TryParse(text, out int parsed) && parsed > 0 ? parsed : fallback;
        }

        private static Camera GetOrCreateCaptureCamera()
        {
            Camera? existing = Resources.FindObjectsOfTypeAll<Camera>()
                .FirstOrDefault(camera =>
                    camera != null &&
                    camera.gameObject.scene.IsValid() &&
                    camera.gameObject.scene == SceneManager.GetActiveScene() &&
                    camera.enabled &&
                    camera.gameObject.activeInHierarchy);

            if (existing != null)
            {
                return existing;
            }

            Bounds bounds = BuildSceneBounds();
            GameObject lightObject = new GameObject("HPR Screenshot Light");
            lightObject.hideFlags = HideFlags.HideAndDontSave;
            Light light = lightObject.AddComponent<Light>();
            light.type = LightType.Directional;
            light.intensity = 1.2f;
            light.transform.rotation = Quaternion.Euler(40f, -25f, 0f);

            GameObject cameraObject = new GameObject("HPR Screenshot Camera");
            cameraObject.hideFlags = HideFlags.HideAndDontSave;
            Camera camera = cameraObject.AddComponent<Camera>();
            camera.backgroundColor = new Color(0.12f, 0.14f, 0.18f);
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.fieldOfView = 45f;

            Vector3 center = bounds.center;
            float extent = Mathf.Max(bounds.extents.x, bounds.extents.y, bounds.extents.z, 1f);
            camera.transform.position = center + new Vector3(extent * 1.6f, extent * 0.9f, -extent * 1.9f);
            camera.transform.LookAt(center);
            camera.nearClipPlane = 0.01f;
            camera.farClipPlane = Mathf.Max(500f, extent * 20f);
            return camera;
        }

        private static Bounds BuildSceneBounds()
        {
            Renderer[] renderers = Resources.FindObjectsOfTypeAll<Renderer>()
                .Where(renderer => renderer != null && renderer.gameObject.scene.IsValid() && renderer.gameObject.scene == SceneManager.GetActiveScene())
                .ToArray();

            if (renderers.Length == 0)
            {
                return new Bounds(Vector3.zero, Vector3.one * 5f);
            }

            Bounds bounds = renderers[0].bounds;
            for (int i = 1; i < renderers.Length; i++)
            {
                bounds.Encapsulate(renderers[i].bounds);
            }

            return bounds;
        }

        private static byte[] Render(Camera camera, int width, int height)
        {
            RenderTexture renderTexture = new RenderTexture(width, height, 24, RenderTextureFormat.ARGB32);
            RenderTexture previous = RenderTexture.active;
            RenderTexture.active = renderTexture;
            camera.targetTexture = renderTexture;
            camera.Render();

            Texture2D texture = new Texture2D(width, height, TextureFormat.RGBA32, false);
            texture.ReadPixels(new Rect(0f, 0f, width, height), 0, 0);
            texture.Apply(false, false);

            byte[] png = texture.EncodeToPNG();

            camera.targetTexture = null;
            RenderTexture.active = previous;
            UnityEngine.Object.DestroyImmediate(texture);
            renderTexture.Release();
            UnityEngine.Object.DestroyImmediate(renderTexture);
            return png;
        }
    }
}
