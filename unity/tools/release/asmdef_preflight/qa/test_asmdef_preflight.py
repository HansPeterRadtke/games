"""Private source-only tests; no Unity Editor, network, or real-project mutation."""
from __future__ import annotations
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("hpr_asmdef_preflight", ROOT / "hpr_asmdef_preflight.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class AssemblyPreflightTest(unittest.TestCase):
    def setUp(self):
        self.ctx = tempfile.TemporaryDirectory(prefix="hpr-asmdef-preflight-", dir="/data/tmp")
        self.addCleanup(self.ctx.cleanup)
        self.base = Path(self.ctx.name)
        self.project = self.base / "project"
        (self.project / "Assets").mkdir(parents=True)
        (self.project / "ProjectSettings").mkdir()
        (self.project / "ProjectSettings/ProjectVersion.txt").write_text("m_EditorVersion: 6000.6.8f1\n")
        (self.project / "Packages").mkdir()
        self.source = self.project / "Assets" / "Components"
        self.source.mkdir()

    def asset(self, name, data, guid=None, parent=None):
        if parent is None: parent = self.source
        parent.mkdir(parents=True, exist_ok=True)
        p = parent / name
        p.write_text(json.dumps(data), encoding="utf-8")
        if guid is not None:
            Path(str(p) + ".meta").write_text("fileFormatVersion: 2\nguid: " + guid + "\n")
        return p

    def basics(self):
        self.asset("Core.asmdef", {"name": "HPR.Core", "references": []}, "a" * 32)
        self.asset("Consumer.asmdef", {"name": "HPR.Consumer", "references": ["HPR.Core", "GUID:" + "a" * 32]}, "b" * 32)
        self.asset("Bridge.asmref", {"reference": "GUID:" + "a" * 32}, "c" * 32)

    def test_real_local_reference_graph_is_clean_with_limits(self):
        self.basics()
        d = mod.inspect(self.project)
        self.assertEqual(d["status"], "CLEAR_WITH_LIMITS")
        self.assertEqual(d["asmdef_count"], 2)
        self.assertEqual(d["asmref_count"], 1)
        self.assertEqual(d["findings"], [])

    def test_duplicate_name_is_definite_local_failure(self):
        self.asset("A.asmdef", {"name": "HPR.Shared"}, "a" * 32)
        self.asset("B.asmdef", {"name": "HPR.Shared"}, "b" * 32)
        d = mod.inspect(self.project)
        self.assertEqual(d["status"], "FAIL")
        self.assertEqual(len([x for x in d["findings"] if x["code"] == "DUPLICATE_ASSEMBLY_NAME"]), 2)

    def test_unresolved_external_is_review_not_proven_breakage(self):
        self.asset("Local.asmdef", {"name": "HPR.Local", "references": ["Unity.InputSystem", "GUID:" + "a" * 32]}, "b" * 32)
        d = mod.inspect(self.project)
        self.assertEqual(d["status"], "REVIEW")
        self.assertEqual({x["code"] for x in d["findings"]},
                         {"UNRESOLVED_NAME_REFERENCE", "UNRESOLVED_GUID_REFERENCE"})
        self.assertIn("Registry", d["limitations"][0])

    def test_duplicate_guid_is_failed_identity(self):
        self.asset("A.asmdef", {"name": "A"}, "d" * 32)
        self.asset("B.asmdef", {"name": "B"}, "d" * 32)
        d = mod.inspect(self.project)
        self.assertEqual(len([x for x in d["findings"] if x["code"] == "DUPLICATE_ASMDEF_GUID"]), 2)

    def test_repeated_reference_and_test_only_constraint_are_review(self):
        self.asset("Core.asmdef", {"name": "Core", "references": ["Other", "Other"],
                                   "defineConstraints": ["UNITY_INCLUDE_TESTS"]}, "a" * 32)
        d = mod.inspect(self.project)
        codes = {f["code"] for f in d["findings"]}
        self.assertIn("REPEATED_ASSEMBLY_REFERENCE", codes)
        self.assertIn("TEST_ONLY_CONSTRAINT", codes)

    def test_conflicting_platform_filters_are_review(self):
        self.asset("Core.asmdef", {"name": "Core", "includePlatforms": ["Editor"],
                                   "excludePlatforms": ["Android"]}, "a" * 32)
        d = mod.inspect(self.project)
        self.assertEqual(d["status"], "REVIEW")
        self.assertEqual(d["findings"][0]["code"], "CONFLICTING_PLATFORM_FILTERS")

    def test_missing_meta_cannot_be_called_clean(self):
        self.asset("Core.asmdef", {"name": "Core"})
        with self.assertRaises(mod.Incomplete): mod.inspect(self.project)

    def test_embedded_package_without_meta_is_review_not_false_fail(self):
        embedded = self.project / "Packages" / "com.hpr.example"
        embedded.mkdir()
        (embedded / "package.json").write_text('{"name":"com.hpr.example"}')
        self.asset("Runtime.asmdef", {"name": "HPR.Runtime"}, parent=embedded)
        d = mod.inspect(self.project)
        self.assertEqual(d["status"], "REVIEW")
        self.assertIn("EMBEDDED_GUID_UNKNOWN", {x["code"] for x in d["findings"]})
        self.assertEqual(d["embedded_roots_scanned"], 1)

    def test_json_duplicate_keys_and_wrong_reference_field_fail_closed(self):
        a = self.asset("A.asmdef", {"name": "A"}, "a" * 32)
        a.write_text('{"name":"A","name":"B"}')
        with self.assertRaises(mod.Incomplete):mod.inspect(self.project)
        a.write_text('{"name":"A","references":"B"}')
        with self.assertRaises(mod.Incomplete):mod.inspect(self.project)

    def test_unhandled_symlinked_source_path_is_rejected(self):
        self.asset("Core.asmdef", {"name": "Core"}, "a" * 32)
        (self.project / "Assets" / "Shortcut").symlink_to(self.source, target_is_directory=True)
        with self.assertRaises(mod.Incomplete):mod.inspect(self.project)

    def test_special_input_and_oversized_asset_refused(self):
        a = self.asset("Core.asmdef", {"name": "Core"}, "a" * 32)
        a.write_bytes(b"x" * (mod.MAX_BYTES_PER_FILE + 1))
        with self.assertRaises(mod.Incomplete):mod.inspect(self.project)
        a.unlink()
        os.mkfifo(a)
        with self.assertRaises(mod.Incomplete):mod.inspect(self.project)

    def test_report_create_only_and_not_written_inside_project(self):
        self.basics()
        report = json.dumps(mod.inspect(self.project), indent=2) + "\n"
        outfile = self.base / "report.json"
        mod._write_new(outfile, report, self.project)
        self.assertEqual(outfile.read_text(), report)
        with self.assertRaises(mod.Incomplete): mod._write_new(outfile, report, self.project)
        with self.assertRaises(mod.Incomplete): mod._write_new(self.project / "Assets" / "report.json", report, self.project)
        self.assertFalse((self.project / "Assets" / "report.json").exists())

    def test_html_escapes_untrusted_project_and_strings(self):
        self.asset("Html.asmdef", {"name": '<script>alert("x")</script>',
                                    "references": ["<img src=x onerror=1>"]}, "a" * 32)
        result = mod.inspect(self.project)
        text = mod.render_html(result)
        self.assertIn("&lt;img src=x onerror=1&gt;", text)
        self.assertNotIn("<img src=x", text)
        self.assertIn("script-src", text) if "script-src" in text else self.assertIn("default-src 'none'", text)
        self.assertIn("No real Unity compilation", text)

    def test_output_parent_symlink_refused(self):
        self.basics()
        target = self.base / "outside"
        target.mkdir()
        (self.base / "alias").symlink_to(target, target_is_directory=True)
        with self.assertRaises(mod.Incomplete):
            mod._write_new(self.base / "alias" / "report.json", "{}", self.project)
        self.assertFalse((target / "report.json").exists())

    def test_missing_project_and_linked_embedded_manifest_refused(self):
        self.basics()
        project_version = self.project / "ProjectSettings" / "ProjectVersion.txt"
        project_version.unlink()
        with self.assertRaises(mod.Incomplete): mod.inspect(self.project)
        project_version.write_text("m_EditorVersion: 6000.6.8f1\n")
        pkg = self.project / "Packages/com.fake.test"
        pkg.mkdir()
        (pkg / "package.json").symlink_to(project_version)
        with self.assertRaises(mod.Incomplete): mod.inspect(self.project)

    def test_cli_output_exit_semantics_and_no_duplicate_output(self):
        self.basics()
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            status = mod.main([str(self.project)])
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(out.getvalue())["status"], "CLEAR_WITH_LIMITS")
        self.asset("Again.asmdef", {"name": "HPR.Core"}, "d" * 32)
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            status = mod.main([str(self.project)])
        self.assertEqual(status, 1)

    def test_no_asmdefs_is_review_not_assumed_valid(self):
        d = mod.inspect(self.project)
        self.assertEqual(d["status"], "REVIEW")
        self.assertIn("NO_LOCAL_ASMDEF", [x["code"] for x in d["findings"]])


if __name__ == "__main__": unittest.main()
