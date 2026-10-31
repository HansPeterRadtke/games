"""Offline safety and assembly-scope checks for the integrated Unity candidate."""
import ast
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "unity/tools/release/gameplay_suite"


class UnityGameplaySuiteSourceTest(unittest.TestCase):
    def test_builder_is_nonpublishing(self):
        source = (SOURCE / "build_gameplay_suite.py").read_text()
        ast.parse(source)
        self.assertIn('INTERNAL_QA_CANDIDATE_NOT_SUBMITTED_NOT_PUBLISHED', source)
        self.assertIn('Assets" / "HPRGameplaySuite', source)
        self.assertIn('shutil.copytree(source / "Runtime", target / "Runtime")', source)
        self.assertNotIn('UploadPackage', source)
        self.assertNotIn('SubmitPackage', source)

    def test_all_internal_modules_present(self):
        source = (SOURCE / "build_gameplay_suite.py").read_text()
        declared = ast.literal_eval(source.split('MODULES = (', 1)[1].split('\n)', 1)[0].join(['(', ')']))
        self.assertEqual(len(declared), 10)
        self.assertEqual(len(set(declared)), 10)
        for name in declared:
            self.assertRegex(name, r'^com\.hpr\.[a-z]+$')
            p = ROOT / 'unity/packages' / name
            self.assertEqual(json.loads((p / 'package.json').read_text())['name'], name)
            self.assertTrue((p / 'LICENSE.md').is_file())
            self.assertTrue((p / 'ThirdPartyNotices.md').is_file())
            self.assertTrue((p / 'Runtime').is_dir())

    def test_interoperation_paths(self):
        source = (SOURCE / 'HprGameplaySuitePlayground.cs').read_text()
        for label in ('WeaponRuntimeState', 'EnemyRuntimeState', 'InventoryComponent',
                      'ActorStatsComponent', 'SaveEntityData', 'EventManager',
                      'DamageEvent', 'WeaponFireResult', 'EnemyAttackResult',
                      'RestoreCheckpoint', 'SaveCheckpoint', 'OnGUI'):
            self.assertIn(label, source)
        self.assertIn('TargetRoot = playerRoot', source)
        self.assertIn('playerStats.BindRuntimeEventBusSource(eventManager)', source)
        self.assertNotIn('File.Write', source)

    def test_one_export_root(self):
        s = (SOURCE / 'HprGameplaySuiteSceneBuilder.cs').read_text()
        self.assertIn('Assets/HPRGameplaySuite', s)
        self.assertIn('Demo/GameplaySuiteShowcase.unity', s)
        self.assertIn('AssetDatabase.ExportPackage(Root, archive, ExportPackageOptions.Recurse)', s)
        self.assertIn('ItemType.Consumable', s)
        self.assertIn('HprGameplaySuitePlayground', s)
        self.assertNotIn('AssetStoreApi', s)

    def test_cleanroom_script_contains_import_and_runtime_qa(self):
        script = (SOURCE / "validate_cleanroom.sh").read_text()
        for required in ("-importPackage", "HprGameplaySuiteCleanroomValidator.Run",
                         "HprGameplaySuiteRuntimeSmokeValidator.Run",
                         "Refusing to replace an existing test project"):
            self.assertIn(required, script)
        runtime = (SOURCE / "qa/HprGameplaySuiteRuntimeSmokeValidator.cs").read_text()
        for required in ("controller.Fire()", "controller.EnemyAttack()", "controller.Heal()",
                         "controller.SaveCheckpoint()", "controller.RestoreCheckpoint()",
                         "controller.ResetEncounter()"):
            self.assertIn(required, runtime)

    def test_curated_buyer_archive_has_no_legacy_demos_or_ui_dependency(self):
        builder = (SOURCE / "build_gameplay_suite.py").read_text()
        self.assertIn("standalone_module_demos_excluded", builder)
        self.assertIn("shutil.copytree(source /", builder)
        self.assertNotIn("com.unity.ugui", builder)
        readme = (SOURCE / "README.md").read_text()
        self.assertIn("Dependency-free cleanroom compilation", readme)
        checker = (SOURCE / "validate_release.py").read_text()
        self.assertIn("Old standalone demos/editors leaked", checker)
        self.assertIn("Unexpected dependency on UnityEngine.UI", checker)
        self.assertIn("ThirdPartyNotices.md", checker)
        script = (SOURCE / "validate_cleanroom.sh").read_text()
        self.assertNotIn("com.unity.ugui", script)

    def test_version_two_customer_features_and_validation(self):
        integration = (SOURCE / "HprGameplaySuitePlayground.cs").read_text()
        for contract in ("AbilityRunnerComponent", "CompositionRoot", "AssetRegistry",
                         "KeyDoorInteractable", "InventoryPickupInteractable",
                         "CaptureSnapshot()", "RestoreSnapshot(", "SaveToDisk(",
                         "LoadFromDisk(", "UsePulseAbility", "UseHealAbility"):
            self.assertIn(contract, integration)
        storage = (SOURCE / "HprSuiteSnapshot.cs").read_text()
        self.assertIn("SchemaVersion = 2", storage)
        self.assertIn("File.Replace", storage)
        self.assertIn("JsonUtility", storage)
        builder = (SOURCE / "build_gameplay_suite.py").read_text()
        for addition in ("HprSuiteSnapshot.cs", "HprSuiteIntegration.cs",
                         "QUICKSTART.md", "ARCHITECTURE.md"):
            self.assertIn(addition, builder)
        validator = (SOURCE / "qa/HprGameplaySuiteRuntimeSmokeValidator.cs").read_text()
        for step in ("ServicesAvailable", "WorldCatalogAvailable", "controller.Interact()",
                     "UseHealAbility()", "UsePulseAbility()", "SaveToDisk(slot)",
                     "LoadFromDisk(slot)", "corrupted disk slot rejected"):
            self.assertIn(step, validator)

    def test_material_creation_uses_pbr_roughness_mapping(self):
        source = (SOURCE / "HprGameplaySuiteSceneBuilder.cs").read_text()
        self.assertIn("float smoothness = 1f - Mathf.Clamp01(roughness)", source)
        self.assertIn('material.SetFloat("_Smoothness", smoothness)', source)
        self.assertIn('material.SetFloat("_Glossiness", smoothness)', source)

    def test_rejection_corrected(self):
        strategy = (ROOT / 'doc/package-launch-strategy.md').read_text()
        steps = (ROOT / 'doc/human-only-final-steps.md').read_text()
        self.assertIn('October 8', strategy)
        self.assertIn('were **declined**', steps)
        self.assertIn('**not a live publisher listing', strategy)


if __name__ == '__main__':
    unittest.main()
