"""Contract for failing safely when HPR asset-copy partially succeeds.

A failure after Unity CopyAsset is not permission to delete an asset
whose ownership may have changed. This is a source-level regression:
real Editor failure-injection acceptance remains separately required.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PROPOSAL = ROOT/"unity/tools/release/gameplay_suite/qa/HprSuiteIntegrationGuideSafeCopy.cs"
PATCH = ROOT/"doc/unity-product-research-2026-10-31/patches/hpr-copy-failure-preserve-new-assets-2026-11-02.patch"


class CopyFailureDoesNotDeleteCustomerAssets(unittest.TestCase):
    def test_failed_copy_preserves_all_created_assets_for_explicit_review(self):
        source = PROPOSAL.read_text()
        self.assertIn("var newlyCreated = new List<string>();",source)
        self.assertIn("catch (Exception copyFailure)",source)
        self.assertIn("partial hpr asset copy",source.lower())
        self.assertIn("string.Join(",source)
        self.assertIn("new InvalidOperationException(",source)
        self.assertNotIn("AssetDatabase.DeleteAsset(",source)
        self.assertIn("Unity created some assets",source)

    def test_source_guid_collision_and_existing_file_guards_remain(self):
        source = PROPOSAL.read_text()
        for marker in ("uniqueDestinations.Add(target)",
                       "File.Exists(physical)", "File.Exists(physical + \".meta\")",
                       "AssetDatabase.LoadMainAssetAtPath(target) != null",
                       "newGuid.Length != 32", "sourceGuids[source]",
                       "AssetDatabase.CopyAsset(source, target)",
                       "AssetDatabase.SaveAssetIfDirty(copy)"):
            with self.subTest(marker=marker):
                self.assertIn(marker,source)

    def test_ui_explains_partial_outputs_remain_and_no_automatic_retry(self):
        source = PROPOSAL.read_text()
        self.assertIn("New customer-owned files may remain",source)
        self.assertIn("review the listed paths",source.lower())
        self.assertIn("No automatic cleanup",source)

    def test_existing_collision_preflight_and_no_implicit_uninstall_remain(self):
        source=PROPOSAL.read_text()
        self.assertIn("AssetDatabase.IsValidFolder(directory)",source)
        self.assertIn("Unity could not copy sample asset",source)
        self.assertIn("No automatic cleanup",source)
        self.assertNotIn("File.Delete(",source)
        self.assertNotIn("AssetDatabase.MoveAsset(",source)

    def test_patch_is_limited_to_one_integration_guide(self):
        diff=PATCH.read_text()
        self.assertIn("HprSuiteIntegrationGuide.cs",diff)
        self.assertIn("-                for (int i = newlyCreated.Count - 1;",diff)
        self.assertNotIn("+                    AssetDatabase.DeleteAsset(",diff)
        headers=[line for line in diff.splitlines() if line.startswith(("+++","---"))]
        self.assertEqual(2,len(headers))


if __name__ == "__main__":
    unittest.main()
