import contextlib
import hashlib
import io
import json
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from unittest import mock

from test_unity_release_export import emit_package

PATH = Path(__file__).resolve().parents[1] / "unity/tools/release/gameplay_suite/qa/NativeEditMode/run_native_editmode.py"
spec = importlib.util.spec_from_file_location("native_editmode", PATH)
qa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa)


def receipt():
    total = sum(qa.EXPECTED_ASSEMBLIES.values())
    root = ET.Element("test-run", result="Passed", total=str(total), passed=str(total), failed="0", skipped="0", inconclusive="0")
    for name, count in qa.EXPECTED_ASSEMBLIES.items():
        assembly = ET.SubElement(root, "test-suite", type="Assembly", name=name + ".dll", result="Passed")
        for index in range(count):
            ET.SubElement(assembly, "test-case", fullname=name + ".Case" + str(index), result="Passed")
    return root


class NativeReceiptTests(unittest.TestCase):
    def classify(self, root, code=0):
        return qa.classify_xml(code, ET.tostring(root, encoding="unicode"))["passed"]

    def test_complete_native_contract(self):
        self.assertTrue(self.classify(receipt()))

    def test_missing_or_invalid_xml(self):
        for raw in ("", "<test-run", "<test-run/>", "<test-case result='Passed'/>"):
            with self.subTest(raw=raw): self.assertFalse(qa.classify_xml(0, raw)["passed"])

    def test_every_missing_case_rejected(self):
        for index in range(sum(qa.EXPECTED_ASSEMBLIES.values())):
            root = receipt()
            cases = list(root.iter("test-case"))
            for parent in root.iter():
                if cases[index] in list(parent): parent.remove(cases[index]); break
            self.assertFalse(self.classify(root))

    def test_case_failure_even_with_passed_root(self):
        for value in ("Failed", "Skipped", "Inconclusive", ""):
            root = receipt()
            next(root.iter("test-case")).set("result", value)
            self.assertFalse(self.classify(root))

    def test_duplicated_identity_rejected(self):
        root = receipt()
        cases = list(root.iter("test-case"))
        cases[1].set("fullname", cases[0].get("fullname"))
        self.assertFalse(self.classify(root))

    def test_zero_or_inconsistent_count_rejected(self):
        for key in ("total", "passed", "failed", "skipped", "inconclusive"):
            root = receipt()
            root.set(key, "0" if key in ("total", "passed") else "1")
            self.assertFalse(self.classify(root))

    def test_wrong_or_missing_module_rejected(self):
        root = receipt()
        next(root.iter("test-suite")).set("name", "Unrelated.dll")
        self.assertFalse(self.classify(root))
        root = receipt()
        root.remove(next(root.iter("test-suite")))
        self.assertFalse(self.classify(root))

    def test_native_exit_required(self):
        for code in (1, 2, -999): self.assertFalse(self.classify(receipt(), code))

    def test_failed_assembly_or_root_rejected(self):
        root = receipt()
        next(root.iter("test-suite")).set("result", "Failed")
        self.assertFalse(self.classify(root))
        root = receipt()
        root.set("result", "Failed")
        self.assertFalse(self.classify(root))


class ExactNUnitPackageTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.assets = self.root / "project/Assets"
        self.vendor = self.assets / "HPRGameplaySuite"
        self.vendor.mkdir(parents=True)
        self.guide = self.vendor / "QUICKSTART.md"
        self.guide.write_text("Current guide")
        for index in range(55):
            (self.vendor / f"Module{index}.cs").write_text(f"class Module{index} {{}}")
        for index, path in enumerate(sorted(self.assets.rglob("*")), start=1):
            Path(str(path) + ".meta").write_text(f"fileFormatVersion: 2\nguid: {index:032x}\n")
        self.archive = self.root / "suite.unitypackage"
        emit_package(self.assets, self.archive)
        self.sha = hashlib.sha256(self.archive.read_bytes()).hexdigest()

    def check(self):
        return qa.require_exact_package(self.assets.parent, self.archive, self.sha)

    def test_exact_non_script_assets_and_metadata(self):
        report = self.check()
        self.assertEqual(57, report["guid_identities_verified"])
        self.assertEqual(56, report["asset_payloads_verified"])
        self.assertEqual(55, report["script_payloads_verified"])
        self.assertEqual([], report["script_payload_mismatches"])

    def test_identical_scripts_with_wrong_guide_are_rejected(self):
        self.guide.write_text("Previous guide")
        with self.assertRaisesRegex(ValueError, "asset payload differs.*QUICKSTART"):
            self.check()

    def test_changed_import_settings_with_stable_guid_are_rejected(self):
        metadata = self.guide.with_suffix(".md.meta")
        metadata.write_text(metadata.read_text() + "userData: changed\n")
        with self.assertRaisesRegex(ValueError, "metadata payload differs"):
            self.check()

    def test_green_nunit_results_do_not_hide_an_asset_added_during_playback(self):
        template = self.assets.parent
        for folder in ("Packages", "ProjectSettings", "Library"):
            (template / folder).mkdir()
        for name in ("manifest", "packages-lock"):
            (template / "Packages" / (name + ".json")).write_text('{"dependencies": {}}')
        editor = self.root / "Unity"
        editor.touch()
        built_in = self.root / "Data/Resources/PackageManager/BuiltInPackages"
        for name in ("com.unity.test-framework", "com.unity.ext.nunit"):
            (built_in / name).mkdir(parents=True)
            (built_in / name / "package.json").write_text(json.dumps({
                "name": name, "version": "1.0", "dependencies": {}}))
        prior = self.root / "import.json"
        prior.write_text(json.dumps({"actual_unity_editor_executed": True, "exit_code": 0,
                                     "archive_sha256": self.sha}))
        task = self.root / "task"
        task.mkdir()
        output = task / "run"
        command = [str(PATH), "--template", str(template), "--archive", str(self.archive),
                   "--archive-sha256", self.sha, "--editor", str(editor),
                   "--import-receipt", str(prior), "--output", str(output)]
        real_run = qa.subprocess.run

        def run(arguments, **kwargs):
            if arguments[0] != str(editor):
                return real_run(arguments, **kwargs)
            project = output / "project"
            (project / "Assets/HPRGameplaySuite/unexpected.asset").write_text("extra")
            lock = {"dependencies": {
                name: {"version": "1.0", "depth": depth, "source": "builtin", "dependencies": {}}
                for name, depth in (("com.unity.test-framework", 0), ("com.unity.ext.nunit", 1))}}
            (project / "Packages/packages-lock.json").write_text(json.dumps(lock))
            ET.ElementTree(receipt()).write(output / "test-results.xml")
            return qa.subprocess.CompletedProcess(arguments, 0)

        with (mock.patch.object(qa, "PRIVATE_QA_ROOT", self.root),
              mock.patch.object(sys, "argv", command),
              mock.patch.object(qa.subprocess, "run", side_effect=run),
              contextlib.redirect_stdout(io.StringIO())):
            self.assertEqual(qa.main(), 1)
        result = json.loads((output / "RESULT.json").read_text())
        self.assertTrue(result["nunit"]["passed"])
        self.assertTrue(result["package_lock_matches_planned_bundled_resolution"])
        self.assertEqual(result["modified_original_files"], [])
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("unexpected.asset", result["package_identity"]["issues"][0])
        self.assertFalse((self.vendor / "unexpected.asset").exists())

    def test_unexpected_vendor_asset_is_rejected(self):
        (self.vendor / "leftover.asset").write_text("Retained from an older package")
        with self.assertRaisesRegex(ValueError, "unexpected imported.*leftover"):
            self.check()


class PackageResolutionPreservationTests(unittest.TestCase):
    def test_only_exact_planned_resolution_is_allowed(self):
        expected = {"dependencies": {"com.unity.test-framework": {"version": "1.8.0", "source": "builtin"}, "customer.package": {"version": "1.0"}}}
        before = {"Packages/packages-lock.json": "old", "Assets/player.asset": "stable"}
        after = {"Packages/packages-lock.json": "new", "Assets/player.asset": "stable"}
        self.assertEqual([], qa.preserved_file_changes(before, after, expected, expected))
        import copy
        bad = copy.deepcopy(expected)
        bad["dependencies"]["customer.package"]["version"] = "2.0"
        self.assertIn("Packages/packages-lock.json", qa.preserved_file_changes(before, after, bad, expected))

    def test_unchanged_but_unexpected_resolution_is_rejected(self):
        files = {"Packages/packages-lock.json": "same"}
        self.assertIn("Packages/packages-lock.json", qa.preserved_file_changes(files, files, {"dependencies": {}}, {"dependencies": {"required": {}}}))

    def test_deleted_lock_or_unrelated_asset_is_not_exempted(self):
        expected = {"dependencies": {}}
        before = {"Packages/packages-lock.json": "old", "Assets/player.asset": "stable"}
        self.assertIn("Packages/packages-lock.json", qa.preserved_file_changes(before, {"Assets/player.asset": "stable"}, None, expected))
        self.assertIn("Assets/player.asset", qa.preserved_file_changes(before, {"Packages/packages-lock.json": "new", "Assets/player.asset": "changed"}, expected, expected))


class BundledResolutionTests(unittest.TestCase):
    def test_uses_installed_versions_and_preserves_customer_dependencies(self):
        old = {"dependencies": {"customer.package": {"version": "1.0", "depth": 0}}}
        framework = {"name": "com.unity.test-framework", "version": "1.6.0", "dependencies": {"com.unity.ext.nunit": "2.0.3"}}
        nunit = {"name": "com.unity.ext.nunit", "version": "2.0.5"}
        expected = qa.expected_bundled_lock(old, framework, nunit, {})
        self.assertEqual(expected["dependencies"]["customer.package"], old["dependencies"]["customer.package"])
        self.assertEqual(expected["dependencies"]["com.unity.ext.nunit"]["version"], "2.0.5")
        self.assertEqual(expected["dependencies"]["com.unity.ext.nunit"]["depth"], 1)
        self.assertEqual(expected["dependencies"]["com.unity.test-framework"]["dependencies"], framework["dependencies"])
        self.assertNotIn("com.unity.test-framework", old["dependencies"])
        direct = qa.expected_bundled_lock(old, framework, nunit, {"com.unity.ext.nunit": "2.0.5"})
        self.assertEqual(direct["dependencies"]["com.unity.ext.nunit"]["depth"], 0)
