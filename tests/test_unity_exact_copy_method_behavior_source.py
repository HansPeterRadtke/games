"""Pure Python provenance and guard tests for the standalone C# fake Editor.

No real Unity Editor, external API, active importer or fake subprocess is
executed by this pytest module. Explicit actual .NET run has its own logs.
"""
from pathlib import Path
import hashlib
import importlib.util
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/"unity/tools/release/gameplay_suite/qa/CopyRaceBehavior"
MODULE=FOLDER/"extract_exact_method.py"
SPEC=importlib.util.spec_from_file_location("hpr_exact_copy_source",MODULE)
extractor=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(extractor)
SOURCE=ROOT/"unity/tools/release/gameplay_suite/qa/HprSuiteIntegrationGuideRaceGuard.cs"


class ExactSourceToFakeUnity(unittest.TestCase):
    def test_actual_reviewed_source_extracts_byte_exact_method_once(self):
        with tempfile.TemporaryDirectory() as td:
            output=Path(td)/"CopyMethod.cs"
            r=extractor.extract(SOURCE,output)
            assert output.is_file()
            source=SOURCE.read_text()
            start=source.index("internal static UnityEngine.Object CopySampleToCustomerPath(")
            raw=output.read_text()
            fragment=raw[raw.index("internal static UnityEngine.Object CopySampleToCustomerPath("):raw.rindex("\n  }\n}")].strip()
            self.assertTrue(fragment.startswith(source[start:start+90]))
            self.assertEqual(r["original_source_sha256"],hashlib.sha256(SOURCE.read_bytes()).hexdigest())
            self.assertIn("lastAttemptedTarget = target;",fragment)
            self.assertIn("AssetDatabase.CopyAsset(source, target)",fragment)
            self.assertFalse(r["source_only_no_editor_launched"] is False)

    def test_output_creation_is_exclusive(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"source-exact.cs"
            extractor.extract(SOURCE,p)
            prior=p.read_bytes()
            with self.assertRaises(FileExistsError):extractor.extract(SOURCE,p)
            self.assertEqual(prior,p.read_bytes())

    def test_synthetic_missing_source_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                extractor.extract(Path(td)/"absent.cs",Path(td)/"new.cs")

    def test_simulated_six_failure_modes_are_explicitly_marked_not_real_editor(self):
        text=(FOLDER/"Program.cs").read_text()
        for key in ("normal","partial-false-file","partial-no-file",
                    "first-false-no-file","race-after-preflight","initial-collision"):
            with self.subTest(key=key):self.assertIn('"'+key+'"',text)
        self.assertIn("actual_unity_editor_process_executed=false",text)
        self.assertIn("no_asset_database_delete_method_available_in_stub=true",text)
        self.assertNotIn("UnityEditor.AssetDatabase.DeleteAsset(",text)

    def test_fake_asset_database_does_not_implement_deletion(self):
        src=(FOLDER/"FakeUnity.cs").read_text()
        self.assertIn("public static bool CopyAsset(",src)
        self.assertIn("public static void SaveAssetIfDirty(",src)
        self.assertNotIn("public static bool DeleteAsset(",src)
        self.assertNotIn("public static void DeleteAsset(",src)


if __name__=="__main__":unittest.main()
