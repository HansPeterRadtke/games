"""Contract for honest Editor-rendered Unity key-art capture, not fake visuals."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/"unity/tools/release/gameplay_suite/qa/HprGameplaySuiteStoreKeyCapture.cs"


class StoreKeyRenderContract(unittest.TestCase):
    def test_all_key_image_dimensions_are_exact(self):
        text=SOURCE.read_text()
        for filename,width,height in (
            ("icon",160,160),("card",420,280),
            ("cover",1950,1300),("social",1200,630)):
            self.assertRegex(text,re.compile(
                r'\"[0-9][0-9]-'+re.escape(filename)+r'-actual-unity-camera\.png\"[^\n]*'
                r'\b'+str(width)+r'\s*,\s*'+str(height)+r'\b'))
        self.assertIn("HPR_STORE_KEY_MEDIA_RECEIPT",text)
        self.assertIn("HPR_STORE_KEY_CAPTURE_FROM_ACTUAL_UNITY_SCENE_PASS",text)

    def test_real_scene_and_camera_render_used_without_fake_ai_art(self):
        text=SOURCE.read_text()
        for item in (
            "Assets/HPRGameplaySuite/Demo/GameplaySuiteShowcase.unity",
            "EditorSceneManager.OpenScene",
            "Camera.main", "RenderTexture",
            "camera.Render();", "ReadPixels", "EncodeToPNG",
            "camera.transform.SetPositionAndRotation",
            "camera.aspect",
        ):
            self.assertIn(item,text)
        for disallowed in ("AssetDatabase.SaveAssets();",
                           "EditorSceneManager.SaveScene(",
                           "AssetDatabase.DeleteAsset(",
                           "image_gen", "stable_diffusion"):
            self.assertNotIn(disallowed,text)

    def test_preflight_fails_on_preexisting_media_file_and_requires_private_output(self):
        text=SOURCE.read_text()
        for token in ("HPR_STORE_KEY_MEDIA_DIR", "File.Exists(path)",
                      "Refusing existing key image",
                      "Environment.GetEnvironmentVariable",
                      "Directory.CreateDirectory"):
            self.assertIn(token,text)

    def test_capture_outputs_are_create_only_and_confined_to_private_root(self):
        text=SOURCE.read_text()
        for marker in ("output == root", "FileMode.CreateNew",
                       "receiptPath.StartsWith(output + Path.DirectorySeparatorChar",
                       "FileAttributes.ReparsePoint"):
            with self.subTest(marker=marker):
                self.assertIn(marker,text)
        self.assertNotIn("File.WriteAllBytes(path, png);",text)
        self.assertNotIn("File.WriteAllText(receipt,",text)

    def test_shader_warmup_and_render_target_cleanup(self):
        text=SOURCE.read_text()
        self.assertGreaterEqual(text.count("camera.Render();"),2)
        self.assertIn("RenderTexture.active = previous;",text)
        self.assertIn("camera.targetTexture = original;",text)
        self.assertIn("target.Release();",text)
        self.assertIn("UnityEngine.Object.DestroyImmediate(pixels)",text)


if __name__ == "__main__":
    unittest.main()
