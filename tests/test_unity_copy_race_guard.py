"""Buyer copy safety: recheck output immediately before Unity CopyAsset.

These are test-first source and review contracts; a genuine concurrent Unity
importer failure-injection test is still needed for product acceptance.
"""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
PROPOSAL=ROOT/"unity/tools/release/gameplay_suite/qa/HprSuiteIntegrationGuideRaceGuard.cs"
PATCH=ROOT/"doc/unity-product-research-2026-10-31/patches/hpr-copy-race-guard-2026-11-02.patch"


class CopyRaceGuard(unittest.TestCase):
    def test_rechecks_target_immediately_before_each_copy(self):
        source=PROPOSAL.read_text()
        section=source.split("// Copy all files first",1)[1].split("foreach (string source in sourcePaths)",1)[1].split("foreach (string source in sourcePaths)",1)[0]
        for part in ("AssetDatabase.LoadMainAssetAtPath(target)",
                     "File.Exists(physical)","Directory.Exists(physical)",
                     "File.Exists(physical + \".meta\")",
                     "Directory.Exists(physical + \".meta\")",
                     "output became occupied before copying"):
            with self.subTest(part=part):self.assertIn(part,section)
        self.assertLess(section.index("output became occupied before copying"),
                        section.index("AssetDatabase.CopyAsset(source, target)"))

    def test_partial_copy_failed_operation_included_even_if_copyasset_returns_false(self):
        src=PROPOSAL.read_text()
        self.assertIn("string lastAttemptedTarget = null;",src)
        self.assertIn("lastAttemptedTarget = target;",src)
        self.assertIn("lastAttemptedTarget = null;",src)
        self.assertIn("last attempted output may also exist",src.lower())
        self.assertIn("CopyAsset(source, target)",src)
        self.assertIn("catch (Exception copyFailure)",src)
        self.assertIn("Inspect the listed paths and their GUIDs",src)
        self.assertIn("copyFailure.Message",src)

    def test_no_automatic_asset_delete_or_retry_is_reintroduced(self):
        code=PROPOSAL.read_text()
        for banned in ("AssetDatabase.DeleteAsset(","File.Delete(",
                       "AssetDatabase.SaveAssets();", "Thread.Sleep("):
            self.assertNotIn(banned,code)
        self.assertIn("AssetDatabase.SaveAssetIfDirty(copy);",code)
        self.assertIn("No automatic cleanup was performed",code)

    def test_patch_scope_matches_one_authorized_file(self):
        diff=PATCH.read_text()
        self.assertIn("HprSuiteIntegrationGuide.cs",diff)
        heads=[line for line in diff.splitlines() if line.startswith(("--- ","+++ "))]
        self.assertEqual(2,len(heads))
        self.assertNotIn("+++ b/Assets/ExternalCustomerGame",diff)


if __name__=="__main__":unittest.main()
