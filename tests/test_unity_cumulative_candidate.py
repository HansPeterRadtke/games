"""Strict source provenance for all three independent Unity improvements.

No Unity Editor, publisher operation, or user project edit occurs here.
"""
from pathlib import Path
import importlib.util
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/"unity/tools/release/gameplay_suite/qa"
import sys
sys.path.insert(0, str(QA))
SPEC=importlib.util.spec_from_file_location("hpr_cumulative_candidate",QA/"verify_cumulative_candidate.py")
checker=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)

REL=Path("unity/tools/release/gameplay_suite")


class CumulativeBuyerSource(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="hpr_merged_candidate_")
        self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name)/"base"
        self.proposed=Path(self.temp.name)/"proposal"
        for root in (self.base,self.proposed):
            folder=root/REL
            folder.mkdir(parents=True)
            (folder/"HprSuiteIntegration.cs").write_text("old runtime source")
            (folder/"HprSuiteIntegrationGuide.cs").write_text("AssetDatabase.SaveAssets();")
            (folder/"HprSelectedAbilityInstaller.cs").write_text("old editor source")
            for name in ("README.md","QUICKSTART.md","ARCHITECTURE.md"):
                (folder/name).write_text("original help")
            (folder/"HprSelectedAbilityInstaller.cs.meta").write_text(
                "guid: "+"f"*32)
        p=self.proposed/REL
        (p/"HprSuiteIntegration.cs").write_text(
            "[SerializeField] private ActorStatsComponent stats;\n"
            "public bool HasValidStatsSource => StatsSource != null;\n"
            "GetComponent<ActorStatsComponent>();")
        (p/"HprSelectedAbilityInstaller.cs").write_text(
            "Undo.DestroyObjectImmediate(runner); "
            "HprSuiteAbilityPool valid; "
            "pool.HasValidStatsSource; "
            "public static bool RemoveExplicitly() => true;")
        (p/"HprSuiteIntegrationGuide.cs").write_text(
            "AssetDatabase.SaveAssetIfDirty(copy); File.Exists(physical + \".meta\")")
        for name in ("README.md","QUICKSTART.md","ARCHITECTURE.md"):
            (p/name).write_text("source-only proposal, not yet shipped or approved")

    def test_correct_six_changed_paths_with_metadata_identity(self):
        result=checker.verify(self.base,self.proposed)
        self.assertEqual("PASS",result["status"])
        self.assertEqual(6,len(result["changed_paths"]))
        self.assertEqual(1,result["unchanged_guid_meta_count"])
        self.assertTrue(result["full_source_tree_same_paths"])
        self.assertTrue(result["read_only"])

    def test_unexpected_source_added_or_removed_is_rejected(self):
        (self.proposed/REL/"UnauthorizedSettings.asset").write_text("new")
        with self.assertRaises(ValueError):
            checker.verify(self.base,self.proposed)
        (self.proposed/REL/"UnauthorizedSettings.asset").unlink()
        (self.proposed/REL/"ARCHITECTURE.md").unlink()
        with self.assertRaises(ValueError):
            checker.verify(self.base,self.proposed)

    def test_unrelated_guid_change_rejected(self):
        (self.proposed/REL/"HprSelectedAbilityInstaller.cs.meta").write_text("guid: "+"1"*32)
        with self.assertRaises(ValueError):
            checker.verify(self.base,self.proposed)

    def test_broad_global_save_reintroduced_rejected(self):
        (self.proposed/REL/"HprSuiteIntegrationGuide.cs").write_text("AssetDatabase.SaveAssets();")
        with self.assertRaises(ValueError):
            checker.verify(self.base,self.proposed)

    def test_native_stats_reference_missing_rejected(self):
        (self.proposed/REL/"HprSuiteIntegration.cs").write_text("no native stats")
        with self.assertRaises(ValueError):
            checker.verify(self.base,self.proposed)

    def test_customer_detach_or_validation_missing_rejected(self):
        (self.proposed/REL/"HprSelectedAbilityInstaller.cs").write_text("old editor")
        with self.assertRaises(ValueError):
            checker.verify(self.base,self.proposed)

    def test_any_external_symlink_added_after_original_is_rejected(self):
        secret=Path(self.temp.name)/"not_hpr"
        secret.write_text("private")
        (self.proposed/REL/"FakeRuntime.cs").symlink_to(secret)
        with self.assertRaises(ValueError):
            checker.verify(self.base,self.proposed)


if __name__=="__main__":
    unittest.main()
