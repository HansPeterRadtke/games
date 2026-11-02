"""Contracts for a buyer-owned ability resource adapter that survives Unity reload.

Static checks supplement, not replace, the real Unity Editor scene Save/Open
and Play-mode stamina/heal tests.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
QA = ROOT / "unity/tools/release/gameplay_suite/qa"
SOURCE_ONLY = Path("/data/var/marketplace-account-setup/hpr-unity-sample-copy-isolated-save-20261102/source")
MODULES = SOURCE_ONLY / "unity/tools/release/gameplay_suite"


class SerializedStatsAdapter(unittest.TestCase):
    def test_stats_source_is_editor_serialized(self):
        code = (QA/"HprSuiteIntegrationProposed.cs").read_text()
        self.assertIn("[SerializeField] private ActorStatsComponent stats;",code)
        self.assertIn("GetComponent<ActorStatsComponent>()",code)
        self.assertIn("public ActorStatsComponent StatsSource",code)
        self.assertIn("public bool HasValidStatsSource",code)
        self.assertIn("public void Bind(ActorStatsComponent source)",code)
        self.assertIn("source.gameObject != gameObject",code)
        self.assertIn("SpendAbilityCost",code)
        self.assertIn("if (source == null",code)
        self.assertNotIn("AssetDatabase.SaveAssets(",code)

    def test_editor_preflight_rejects_inoperative_pool(self):
        code = (QA/"HprSelectedAbilityInstallerProposed.cs").read_text()
        self.assertIn("HprSuiteAbilityPool",code)
        self.assertIn("HasValidStatsSource",code)
        self.assertIn("missing an ActorStatsComponent",code)
        self.assertIn("resourceProvider is IAbilityResourcePool",code)

    def test_actual_unity_fixture_checks_saved_scene_and_playmode(self):
        code = (QA/"HprCustomerStatsAdapterValidator.cs").read_text()
        for term in (
            "HprSuiteAbilityPool", "ActorStatsComponent",
            "HPR_STATS_ADAPTER_RECEIPT",
            "EditorSceneManager.OpenScene",
            "EditorSceneManager.SaveScene",
            "HprSelectedAbilityInstaller.AttachExplicitly",
            "Undo.PerformUndo",
            "AbilityRunnerComponent", "Stamina",
            "CustomerHealing.asset",
            "ExistingPlayerController",
        ):
            with self.subTest(term=term):
                self.assertIn(term,code)

    def test_only_two_product_files_in_proposal(self):
        integration = (QA/"HprSuiteIntegrationProposed.cs").read_text()
        installer = (QA/"HprSelectedAbilityInstallerProposed.cs").read_text()
        self.assertIn("namespace HPR.GameplaySuite",integration)
        self.assertIn("namespace HPR.GameplaySuite.Experimental",installer)
        self.assertNotIn("AssetDatabase.DeleteAsset(",installer)


if __name__ == "__main__":
    unittest.main()
