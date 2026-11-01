"""Offline safety and assembly-scope checks for the integrated Unity candidate."""
import ast
import json
import runpy
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
        self.assertIn("SchemaVersion = 3", storage)
        self.assertIn("File.Replace", storage)
        self.assertIn("JsonUtility", storage)
        builder = (SOURCE / "build_gameplay_suite.py").read_text()
        for addition in ("HprSuiteArenaMotor.cs", "HprSuiteSnapshot.cs", "HprSuiteIntegration.cs",
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

    def test_aiming_enemy_physics_and_snapshot_version(self):
        script = (SOURCE / "HprGameplaySuitePlayground.cs").read_text()
        for required in ("FireAt(", "Physics.RaycastAll(", "AdvanceEnemy(", "automaticEnemy",
                         "EnemyPosition =", "EnemyRotation =", "TryGetPointerAim", "Objective =>"):
            self.assertIn(required, script)
        scene = (SOURCE / "HprGameplaySuiteSceneBuilder.cs").read_text()
        for required in ("CharacterController", "HprSuiteArenaMotor", "orthographic = true",
                         "UnityEngine.Rendering.GraphicsSettings.currentRenderPipeline"):
            self.assertIn(required, scene)
        self.assertIn("SchemaVersion = 3", (SOURCE / "HprSuiteSnapshot.cs").read_text())
        self.assertIn("Adapt Demo Materials to Current Render Pipeline", scene)
        self.assertIn('Shader.Find("Universal Render Pipeline/Lit")', scene)
        self.assertIn("No other project materials, packages or render settings changed", scene)

    def test_buyer_editor_installation_and_scene_open_actions(self):
        scene = (SOURCE / "HprGameplaySuiteSceneBuilder.cs").read_text()
        for action in ("Verify Installation", "Open Showcase",
                       "SaveCurrentModifiedScenesIfUserWantsTo",
                       "AssetDatabase.FindAssets", "EditorUtility.DisplayDialog"):
            self.assertIn(action, scene)
        self.assertNotIn("UnityEditorInternal", scene)

    def test_nondestructive_builder_and_modern_export(self):
        scene = (SOURCE / "HprGameplaySuiteSceneBuilder.cs").read_text()
        for snippet in ("#if UNITY_6000_6_OR_NEWER",
                        "UnityEditor.AssetPackage.Package.Export",
                        "ExportPackageParameters",
                        "SaveCurrentModifiedScenesIfUserWantsTo",
                        "Existing demo assets found. No files modified"):
            self.assertIn(snippet, scene)
        validation = (SOURCE / "qa/HprGameplaySuiteCleanroomValidator.cs").read_text()
        self.assertIn("sceneBefore.SequenceEqual", validation)
        self.assertIn("medkitBefore.SequenceEqual", validation)

    def test_editor_ui_has_scoped_styles_read_only_first_use_and_dependencies(self):
        builder = (SOURCE / "build_gameplay_suite.py").read_text()
        validator = (SOURCE / "validate_release.py").read_text()
        for name in ("HprSuiteIntegrationGuide.cs", "HprSuiteIntegrationGuide.uss"):
            self.assertIn(name, builder)
            self.assertIn(name, validator)
        window = (SOURCE / "HprSuiteIntegrationGuide.cs").read_text()
        for snippet in ("CreateGUI()", "ScrollView", "RefreshStatus", "EditorApplication.projectChanged",
                        "EditorUtility.DisplayDialog", "EditorGUIUtility.PingObject",
                        "HprGameplaySuiteSceneBuilder.OpenShowcase"):
            self.assertIn(snippet, window)
        self.assertNotIn("UnityEditorInternal", window)
        self.assertNotIn("AssetDatabase.ImportPackage", window)
        style = (SOURCE / "HprSuiteIntegrationGuide.uss").read_text()
        self.assertIn(".hpr-suite-root", style)
        self.assertIn(".hpr-suite-button", style)

    def test_optional_input_backends_with_external_injection(self):
        engine = (SOURCE / "HprSuiteInput.cs").read_text()
        for symbol in ("ENABLE_INPUT_SYSTEM", "ENABLE_LEGACY_INPUT_MANAGER",
                       "IHprSuiteInputSource", "Keyboard.current", "Input.GetKey",
                       "Mouse.current", "TryGetPointer"):
            self.assertIn(symbol, engine)
        gameplay = (SOURCE / "HprGameplaySuitePlayground.cs").read_text()
        self.assertIn("BindInputSource(", gameplay)
        self.assertIn("interactionRangeMeters", gameplay)
        self.assertIn("moveForwardKey", gameplay)
        self.assertNotIn("Input.GetKey(", gameplay)
        self.assertNotIn("Input.GetKeyDown(", gameplay)
        self.assertNotIn("Input.mousePosition", gameplay)
        builder = (SOURCE / "build_gameplay_suite.py").read_text()
        self.assertIn("HprSuiteInput.cs", builder)
        archive = (SOURCE / "validate_release.py").read_text()
        self.assertIn("Integration/HprSuiteInput.cs", archive)
        for value in ("KeyCode.LeftControl", "Key.LeftCtrl", "KeyCode.Keypad1",
                      "Key.Numpad1", "KeyCode.RightControl", "Key.RightCtrl"):
            self.assertIn(value, engine)
        input_qa = (SOURCE / "qa/HprSuiteInputPlayModeFixtureTests.cs").read_text()
        for expected in ("InputTestFixture", "Press(keyboard.wKey)",
                         "source.WasPressed(KeyCode.W)", "Set(mouse.position",
                         "source.IsPressed(KeyCode.LeftControl)"):
            self.assertIn(expected, input_qa)
        live_qa = (SOURCE / "qa/HprSuiteInputGameplayProbe.cs").read_text()
        self.assertIn("source.WasPressed", live_qa)
        self.assertIn("InputSystem.QueueStateEvent", live_qa)
        self.assertIn("Application.Quit(0)", live_qa)


    def test_integrated_module_docs_drop_unavailable_standalone_workflows(self):
        builder = runpy.run_path(str(SOURCE / "build_gameplay_suite.py"))
        original = (ROOT / "unity/packages/com.hpr.inventory/README.md").read_text()
        converted = builder["integrated_module_readme"]("com.hpr.inventory", original)
        self.assertIn("INTEGRATED SUITE INSTALLATION", converted)
        self.assertIn("## API overview", converted)
        self.assertIn("## Limitations", converted)
        for old in ("## Installation", "## Demo", "## Samples", "## Validation"):
            self.assertNotIn(old, converted)
        self.assertIn("## Installation", original)

    def test_safe_export_reuse_does_not_trigger_demo_generation(self):
        builder = (SOURCE / "build_gameplay_suite.py").read_text()
        self.assertIn('"HPR.GameplaySuite.HprGameplaySuiteSceneBuilder.ExportExisting"', builder)
        self.assertIn("stage_authored_buyer_assets(reuse_project=args.reuse_project)", builder)
        source = (SOURCE / "HprGameplaySuiteSceneBuilder.cs").read_text()
        self.assertIn("public static void ExportExisting()", source)
        self.assertIn("public static void BuildAndExport()", source)
        self.assertIn("BuildShowcase(); // first-time build", source)

    def test_authored_unity_guids_and_sample_sources_are_stable_and_unique(self):
        import re
        source = SOURCE / "buyer_source_assets"
        metadata = sorted(source.rglob("*.meta"))
        assert source.is_dir()
        self.assertGreaterEqual(len(metadata), 52)
        parsed = {}
        for meta in metadata:
            matched = re.search(r"(?m)^guid:\s*([0-9a-f]{32})\s*$",
                                meta.read_text(encoding="utf-8"))
            self.assertIsNotNone(matched, str(meta))
            self.assertNotIn(matched.group(1), parsed.values(), str(meta))
            parsed[str(meta.relative_to(source))] = matched.group(1)
        self.assertIn("HPRGameplaySuite/Demo/GameplaySuiteShowcase.unity.meta", parsed)
        self.assertIn("HPRGameplaySuite/Integration/HprGameplaySuitePlayground.cs.meta", parsed)
        yaml = list(source.glob("HPRGameplaySuite/Samples/*.asset"))
        yaml += list(source.glob("HPRGameplaySuite/Samples/*.mat"))
        yaml += list(source.glob("HPRGameplaySuite/Demo/*.unity"))
        self.assertGreaterEqual(len(yaml), 22)
        for path in yaml:
            self.assertTrue(path.read_bytes().startswith(b"%YAML"), str(path))

    def test_staging_authored_assets_never_overwrites_edited_existing_files(self):
        import tempfile
        builder = runpy.run_path(str(SOURCE / "build_gameplay_suite.py"))
        stage = builder["stage_authored_buyer_assets"]
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "Project"
            (project / "Assets").mkdir(parents=True)
            stage.__globals__["PROJECT"] = project
            hashes = stage(reuse_project=False)
            self.assertGreaterEqual(len(hashes), 70)
            self.assertEqual(stage(reuse_project=True), hashes)
            example = project / "Assets/HPRGameplaySuite/Samples/FieldMedkit.asset"
            example.write_text(example.read_text() + "# local customer change\\n")
            with self.assertRaisesRegex(RuntimeError, "differs from source"):
                stage(reuse_project=True)

    def test_upgrade_guid_validator_catches_changed_and_removed_references(self):
        import io
        import sys
        import tarfile
        import tempfile
        sys.path.insert(0, str(SOURCE / "qa"))
        from validate_upgrade_guids import compare

        def archive(path, assets):
            with tarfile.open(path, "w:gz") as handle:
                for name, guid in assets.items():
                    data = name.encode("utf-8")
                    record = tarfile.TarInfo(guid + "/pathname")
                    record.size = len(data)
                    handle.addfile(record, io.BytesIO(data))

        paths = {
            "Assets/HPRGameplaySuite/QA/" + str(i) + ".asset": format(i + 1, "032x")
            for i in range(105)
        }
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            baseline = root / "baseline.unitypackage"
            unchanged = root / "unchanged.unitypackage"
            changed = root / "changed.unitypackage"
            removed = root / "removed.unitypackage"
            archive(baseline, paths)
            archive(unchanged, paths.copy())
            changed_paths = paths.copy()
            first = next(iter(changed_paths))
            changed_paths[first] = format(10000, "032x")
            archive(changed, changed_paths)
            removed_paths = paths.copy()
            removed_paths.pop(first)
            archive(removed, removed_paths)
            self.assertFalse(compare(baseline, unchanged)["changed_shared_guids"])
            self.assertFalse(compare(baseline, unchanged)["removed_reference_guids"])
            self.assertEqual(compare(baseline, changed)["changed_shared_guids"], [first])
            self.assertEqual(compare(baseline, removed)["removed_reference_guids"], [first])

    def test_snapshot_rotation_normalization_and_real_qa(self):
        source = (SOURCE / "HprGameplaySuitePlayground.cs").read_text()
        self.assertIn("!IsUnitQuaternion(s.Player.rotation)", source)
        self.assertIn("!IsUnitQuaternion(s.EnemyRotation)", source)
        self.assertIn("normSquared >= 0.99 && normSquared <= 1.01", source)
        qa = (SOURCE / "qa/HprGameplaySuiteRuntimeSmokeValidator.cs").read_text()
        self.assertIn("zero-length save quaternion must not be accepted", qa)

    def test_arena_boundaries_are_shared_by_player_and_enemy_restore(self):
        source = (SOURCE / "HprGameplaySuitePlayground.cs").read_text()
        self.assertIn("!IsWithinArena(s.Player.position)", source)
        self.assertIn("!IsWithinArena(s.EnemyPosition)", source)
        self.assertIn("IsWithin(position.x, -8f, 8f)", source)
        self.assertIn("IsWithin(position.z, -6f, 6f)", source)
        qa = (SOURCE / "qa/HprGameplaySuiteRuntimeSmokeValidator.cs").read_text()
        self.assertIn("valid player checkpoint beside the arena boundary must restore", qa)

    def test_rejection_corrected(self):
        strategy = (ROOT / 'doc/package-launch-strategy.md').read_text()
        steps = (ROOT / 'doc/human-only-final-steps.md').read_text()
        self.assertIn('October 8', strategy)
        self.assertIn('were **declined**', steps)
        self.assertIn('**not a live publisher listing', strategy)


if __name__ == '__main__':
    unittest.main()
