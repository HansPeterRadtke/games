"""Regression checks for no implicit flushing of unrelated buyer assets.

BuildShowcase is internal-only, Adapt Demo Materials is an explicit
customer menu action. Neither must call global AssetDatabase.SaveAssets.
"""
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/"unity/tools/release/gameplay_suite/qa"
PATCH=ROOT/"doc/unity-product-research-2026-10-31/patches/hpr-demo-material-save-scope-2026-11-02.patch"
FIXTURE=QA/"HprDemoMaterialDirtyIsolationValidator.cs"

class DemoBuilderSaveScope(unittest.TestCase):
    def test_diff_removes_both_global_save_calls(self):
        diff=PATCH.read_text()
        self.assertEqual(2,diff.count("-            AssetDatabase.SaveAssets();"))
        self.assertNotIn("+            AssetDatabase.SaveAssets();",diff)
        self.assertIn("SaveAssetIfDirty(material)",diff)
        self.assertIn("SaveAssetIfDirty(asset)",diff)
        self.assertIn("SaveOwnedSamplesOnly",diff)

    def test_remapped_source_saves_only_under_packaged_samples(self):
        source=QA/"HprGameplaySuiteSceneBuilderScoped.cs"
        body=source.read_text()
        self.assertNotIn("AssetDatabase.SaveAssets();",body)
        self.assertIn('path.StartsWith(Samples + "/"',body)
        self.assertIn("AssetDatabase.FindAssets",body)
        self.assertIn("AssetDatabase.SaveAssetIfDirty(asset)",body)
        self.assertIn("AssetDatabase.SaveAssetIfDirty(material)",body)
        self.assertIn("private static void SaveOwnedSamplesOnly()",body)

    def test_actual_unity_editor_probe_preserves_unsaved_customer_asset(self):
        text=FIXTURE.read_text()
        for part in ("HPR_DEMO_MATERIAL_DIRTY_RECEIPT",
                     "EditorUtility.SetDirty", "EditorUtility.IsDirty",
                     "File.OpenRead", "SHA256", "HprGameplaySuiteSceneBuilder.AdaptDemoMaterials",
                     "HPRGameplaySuite/Samples", "OriginalCustomerScene.unity"):
            with self.subTest(part=part):
                self.assertIn(part,text)
        self.assertNotIn("AssetDatabase.SaveAssets();",text)

if __name__=="__main__":
    unittest.main()
