import importlib.util
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

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
        for index in range(55):
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
