"""Regression contracts for a reversible, explicit, scene-only HPR detach.

Source gates supplement, but cannot replace, the real Unity Editor Undo/Redo
and original customer asset byte-preservation acceptance test.
"""
from pathlib import Path
import unittest

SOURCE = (Path(__file__).resolve().parents[1] /
          "unity/tools/release/gameplay_suite/qa/HprSelectedAbilityInstaller.cs")
VALIDATOR = (Path(__file__).resolve().parents[1] /
             "unity/tools/release/gameplay_suite/qa/HprSelectedAbilityDetachValidator.cs")


class ExplicitDetachContract(unittest.TestCase):
    def test_attach_and_detach_both_expose_read_only_gates(self):
        src = SOURCE.read_text()
        for needle in (
            "public static string ValidateRemoval(",
            "public static bool RemoveExplicitly(",
            "ValidateSelection(",
            "Undo.DestroyObjectImmediate(",
            "Undo.RevertAllDownToGroup(",
            "EditorSceneManager.MarkSceneDirty(",
            "PrefabUtility.IsPartOfPrefabAsset(",
            "EditorUtility.IsPersistent(",
            "EditorApplication.isPlayingOrWillChangePlaymode",
            "target.scene != EditorSceneManager.GetActiveScene()",
            "GetComponents<AbilityRunnerComponent>()",
        ):
            with self.subTest(needle=needle):
                self.assertIn(needle, src)
        for forbidden in ("AssetDatabase.DeleteAsset(", "AssetDatabase.SaveAssets()",
                          "EditorSceneManager.SaveScene(", "File.Delete("):
            self.assertNotIn(forbidden, src)

    def test_remove_is_explicit_and_has_separate_customer_consent(self):
        src = SOURCE.read_text()
        for needle in (
            "Remove HPR runner", "RemoveRequested",
            "EditorUtility.DisplayDialog(", "removeButton.SetEnabled(",
            "Undo available", "RemoveExplicitly(target)",
        ):
            self.assertIn(needle, src)

    def test_real_unity_qa_includes_remove_undo_redo(self):
        src = VALIDATOR.read_text()
        for needle in (
            "HprSelectedAbilityInstaller.RemoveExplicitly",
            "HprSelectedAbilityInstaller.ValidateRemoval",
            "Undo.PerformUndo()",
            "Undo.PerformRedo()",
            "ExistingPlayerController",
            "AssetDatabase.AssetPathToGUID",
            "HPR_SELECTED_ABILITY_DETACH_RECEIPT",
        ):
            self.assertIn(needle, src)


if __name__ == "__main__":
    unittest.main()
