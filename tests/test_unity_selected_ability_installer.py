"""Source-level gates for the optional, explicitly invoked Unity Editor integration prototype.

The actual GameObject, Undo, serialized inspector and scene behavior must
also pass the separate real Unity Editor validator before acceptance.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "unity/tools/release/gameplay_suite/qa/HprSelectedAbilityInstaller.cs"
REAL_VALIDATOR = ROOT / "unity/tools/release/gameplay_suite/qa/HprSelectedAbilityInstallerValidator.cs"


class SelectedAbilityInstallerSourceContract(unittest.TestCase):
    def test_explicit_customer_selection_and_read_only_preflight(self):
        text = SOURCE.read_text(encoding="utf-8")
        for required in (
            "ValidateSelection", "AttachExplicitly", "Selection.activeGameObject",
            "EditorUtility.IsPersistent", "IAbilityResourcePool",
            "AssetDatabase.GetAssetPath", "Assets/HPRGameplaySuite",
            "PrefabUtility", "Undo.AddComponent<AbilityRunnerComponent>",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)
        for forbidden in ("[InitializeOnLoad]", "AssetDatabase.SaveAssets()",
                          "EditorSceneManager.SaveScene(", "AssetDatabase.DeleteAsset("):
            self.assertNotIn(forbidden, text)

    def test_persistent_editors_and_undo_property_writes(self):
        text = SOURCE.read_text(encoding="utf-8")
        for required in (
            "new SerializedObject(", "configuredAbilities",
            "unlockAllConfiguredAbilities", "resourcePoolBehaviour",
            "ApplyModifiedProperties", "Undo.RecordObject",
            "EditorSceneManager.MarkSceneDirty",
            "EditorSceneManager.GetActiveScene",
            "Undo.RevertAllDownToGroup",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)

    def test_actual_customer_ux_control(self):
        text = SOURCE.read_text(encoding="utf-8")
        for required in (
            "CreateGUI()", "UnityEditor.UIElements", "ObjectField",
            "HelpBox", "Button", "SetEnabled", "Undo", "Scene",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)

    def test_unity_validator_requires_reversible_safety(self):
        text = REAL_VALIDATOR.read_text(encoding="utf-8")
        for required in (
            "HprSelectedAbilityInstaller.ValidateSelection",
            "HprSelectedAbilityInstaller.AttachExplicitly",
            "Undo.PerformUndo", "EditorSceneManager.OpenScene",
            "EditorSceneManager.SaveScene", "HPR_SELECTED_ABILITY",
            "ExistingPlayerController", "AssetDatabase.AssetPathToGUID",
        ):
            with self.subTest(required=required):
                self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
