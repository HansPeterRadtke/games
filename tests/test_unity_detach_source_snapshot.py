"""Read-only source reproducibility checks for a detached Unity Editor proposal."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT/"unity/tools/release/gameplay_suite/qa/verify_detach_overlay.py"
spec = importlib.util.spec_from_file_location("verify_detach_overlay", MOD)
overlay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(overlay)

REL = "unity/tools/release/gameplay_suite/"
DOCS = ("README.md","QUICKSTART.md","ARCHITECTURE.md")
BASE = """// Internal Unity buyer-release QA candidate.\npublic static class HprSelectedAbilityInstaller { }\n"""
DETACH = """// Internal Unity buyer-release QA candidate.\npublic static class HprSelectedAbilityInstaller {
public static string ValidateRemoval(object target) => null;
public static bool RemoveExplicitly(object target) => true;
void RemoveRequested(){Undo.DestroyObjectImmediate(runner);}
void UndoCleanup(){Undo.RevertAllDownToGroup(group);}
void Confirm(){EditorUtility.DisplayDialog("title", "text", "yes");}
void Mark(){EditorSceneManager.MarkSceneDirty(scene);}
void Reject(){PrefabUtility.IsPartOfPrefabAsset(target);}
void RefusePlay(){bool active=EditorApplication.isPlayingOrWillChangePlaymode;}
}
"""


class OverlayProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="hpr_source_overlay_")
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.base=self.root/"frozen"
        self.draft=self.root/"candidate"
        for root in (self.base,self.draft):
            module=root/REL
            module.mkdir(parents=True)
            (module/"HprSelectedAbilityInstaller.cs").write_text(BASE)
            (module/"HprSelectedAbilityInstaller.cs.meta").write_text(
                "fileFormatVersion: 2\nguid: ffffffffffffffffffffffffffffffff\n")
            for name in DOCS:
                (module/name).write_text("old documentation\n")
        dest=self.draft/REL
        (dest/"HprSelectedAbilityInstaller.cs").write_text(DETACH)
        for name in DOCS:
            (dest/name).write_text("internal SOURCE-ONLY, not yet released, current immutable buyer package unchanged\n")

    def test_exactly_four_permitted_edits_with_all_guid_bytes_stable(self):
        report=overlay.verify_overlay(self.base,self.draft)
        self.assertEqual("PASS",report["result"])
        self.assertEqual(4,len(report["changed_paths"]))
        self.assertEqual(1,report["unchanged_meta_file_count"])
        self.assertTrue(report["read_only"])
        self.assertTrue(report["not_a_published_package"])

    def test_meta_guid_changed_is_not_accepted(self):
        (self.draft/REL/"HprSelectedAbilityInstaller.cs.meta").write_text("guid: 00000000000000000000000000000000")
        with self.assertRaises(ValueError):
            overlay.verify_overlay(self.base,self.draft)

    def test_added_or_missing_file_is_rejected(self):
        (self.draft/REL/"UnexpectedFile.cs").write_text("side effect")
        with self.assertRaises(ValueError):
            overlay.verify_overlay(self.base,self.draft)
        (self.draft/REL/"UnexpectedFile.cs").unlink()
        (self.draft/REL/"HprSelectedAbilityInstaller.cs.meta").unlink()
        with self.assertRaises(ValueError):
            overlay.verify_overlay(self.base,self.draft)

    def test_unchanged_relative_source_symlink_does_not_fake_a_content_change(self):
        for root in (self.base, self.draft):
            (root/REL/"LocalInstallerAlias.cs").symlink_to("HprSelectedAbilityInstaller.cs")
        report=overlay.verify_overlay(self.base,self.draft)
        self.assertEqual("PASS",report["result"])
        self.assertEqual(0,report["non_shipping_external_symlinks"])

    def test_nonshipping_original_absolute_helper_symlink_is_disclosed(self):
        legacy=Path("unity/tools/assetstore/helper_project/Packages")
        for root in (self.base, self.draft):
            folder=root/legacy
            folder.mkdir(parents=True)
            (folder/"com.hpr.foundation").symlink_to(
                "/data/src/github/games/unity/packages/com.hpr.foundation")
        report=overlay.verify_overlay(self.base,self.draft)
        self.assertEqual("PASS",report["result"])
        self.assertEqual(1,report["non_shipping_external_symlinks"])
        self.assertFalse(report["entire_repository_snapshot_hermetic"])

    def test_symlink_to_outside_is_rejected(self):
        private=self.root/"outside.txt"
        private.write_text("SECRET OUTSIDE THE ORIGINAL TREE")
        (self.draft/REL/"UnsafeLink").symlink_to(private)
        with self.assertRaises(ValueError):
            overlay.verify_overlay(self.base,self.draft)

    def test_missing_reversible_component_method_or_misleading_docs_rejected(self):
        src=self.draft/REL/"HprSelectedAbilityInstaller.cs"
        src.write_text(BASE+"// pretends to be a feature")
        with self.assertRaises(ValueError):
            overlay.verify_overlay(self.base,self.draft)
        src.write_text(DETACH)
        (self.draft/REL/"QUICKSTART.md").write_text("shipped complete production package")
        with self.assertRaises(ValueError):
            overlay.verify_overlay(self.base,self.draft)

    def test_dangerous_delete_or_auto_scene_save_api_rejected(self):
        file=self.draft/REL/"HprSelectedAbilityInstaller.cs"
        for expression in ("AssetDatabase.DeleteAsset(", "EditorSceneManager.SaveScene("):
            file.write_text(DETACH+expression)
            with self.assertRaises(ValueError):
                overlay.verify_overlay(self.base,self.draft)


if __name__ == "__main__":
    unittest.main()
