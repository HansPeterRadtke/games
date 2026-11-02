"""Test-first regression for not flushing unrelated dirty buyer assets.

These source contracts supplement a genuine Unity Editor test with a dirty
customer ScriptableObject. They do NOT claim a Unity runtime test passed.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "doc/unity-product-research-2026-10-31/patches/hpr-copy-save-only-authored-assets-2026-11-02.patch"
VALIDATOR = ROOT / "unity/tools/release/gameplay_suite/qa/HprUnrelatedDirtyAssetValidator.cs"


class ScopedAssetCopySaves(unittest.TestCase):
    def test_patch_replaces_broad_save_with_target_only(self):
        patch=PATCH.read_text()
        self.assertIn("-                AssetDatabase.SaveAssets();",patch)
        self.assertIn("+                    AssetDatabase.SaveAssetIfDirty(copy);",patch)
        self.assertIn("foreach (string target in destinations.Values)",patch)
        self.assertNotIn("+                AssetDatabase.SaveAssets();",patch)
        self.assertIn("Nothing else was saved",patch)

    def test_real_editor_fixture_has_unsaved_customer_asset_and_immutable_disk_check(self):
        source=VALIDATOR.read_text()
        for token in ("HprSuiteIntegrationGuide.CopySampleToCustomerPath",
                      "EditorUtility.SetDirty", "AssetDatabase.GetAssetPath",
                      "File.OpenRead", "SHA256", "HPR_DIRTY_ASSET_ISOLATION_RECEIPT",
                      "OriginalCustomerScene.unity",
                      "finally", "CustomerHealing.asset",
                      "UnrelatedDirty"):
            with self.subTest(token=token):
                self.assertIn(token,source)
        self.assertNotIn("AssetDatabase.SaveAssets();",source)

    def test_patch_is_only_targeted_save_operation(self):
        lines=PATCH.read_text().splitlines()
        changed=[line for line in lines if line.startswith(("+","-")) and not line.startswith(("+++","---"))]
        self.assertTrue(any("AssetDatabase.SaveAssets" in line for line in changed))
        self.assertFalse(any("SaveAssetIfDirty" in line and line.startswith("-") for line in changed))
        self.assertFalse(any("File.Delete" in line for line in changed))


if __name__ == "__main__":
    unittest.main()
