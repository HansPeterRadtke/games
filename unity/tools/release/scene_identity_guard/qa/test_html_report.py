"""Behavior, output-safety and injection tests for the genuine static HTML report."""
from __future__ import annotations

from contextlib import redirect_stderr
from html import unescape
from pathlib import Path
import hashlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))  # Mimic the actual self-contained CLI script directory.
SOURCE = ROOT / "hpr_scene_identity.py"
HTML = ROOT / "hpr_scene_identity_report.py"

def load(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

guard=load("hpr_scene_guard_html_tests",SOURCE)
renderer=load("hpr_scene_report_html_tests",HTML)
GUID_A="12345678901234567890123456789012"
GUID_B="abcdefabcdefabcdefabcdefabcdefab"


def serialized(*rows):
    lines=["%YAML 1.1","%TAG !u! tag:unity3d.com,2011:"]
    for id_, name in rows:
        lines += [f"--- !u!1 &{id_}","GameObject:","  m_Name: "+name]
    return ("\n".join(lines)+"\n").encode()


class HtmlReportTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="hpr-private-html-")
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.project=self.root/"UnityProject"
        (self.project/"ProjectSettings").mkdir(parents=True)
        (self.project/"ProjectSettings/ProjectVersion.txt").write_text("m_EditorVersion: 2022.3.22f1\n")
        (self.project/"Assets/Scenes").mkdir(parents=True)
        self.file=self.project/"Assets/Scenes/Example.unity"
        self.file.write_bytes(serialized((11,"Player"),(22,"Gate")))
        self.file.with_suffix(".unity.meta").write_text(f"fileFormatVersion: 2\nguid: {GUID_A}\n")
        self.baseline=self.root/"approved.json"
        self.html=self.root/"preview.html"
        self.old=guard.scan(self.project)

    def test_actual_project_change_produces_static_html_and_review_exit(self):
        self.file.write_bytes(serialized((11,"Player")))
        start=hashlib.sha256(self.file.read_bytes()).hexdigest()
        guard._write_new(self.baseline,(json.dumps(self.old)+"\n").encode())
        stdout=io.StringIO()
        with mock.patch("sys.stdout",stdout):
            rc=guard.main(["check",str(self.project),"--baseline",str(self.baseline),"--html-out",str(self.html)])
        self.assertEqual(rc,1)
        self.assertEqual(json.loads(stdout.getvalue())["status"],"REVIEW_REQUIRED")
        html=self.html.read_text()
        self.assertIn("<!doctype html>",html)
        self.assertIn("script-src 'none'",html)
        self.assertNotIn("<script",html.lower())
        self.assertIn("Review required",html)
        self.assertIn("Gate",html)
        self.assertIn("No longer present",html)
        self.assertEqual(hashlib.sha256(self.file.read_bytes()).hexdigest(),start)

    def test_matching_snapshot_is_readable_without_false_alarm(self):
        guard._write_new(self.baseline,(json.dumps(self.old)+"\n").encode())
        self.assertEqual(guard.main(["check",str(self.project),"--baseline",str(self.baseline),"--html-out",str(self.html)]),0)
        html=self.html.read_text()
        self.assertIn("Direct identities stable",html)
        self.assertIn("No baseline direct GameObject identities were lost",html)

    def test_additions_only_and_renamed_preserving_identity(self):
        self.file.write_bytes(serialized((11,"Renamed Player"),(22,"Gate"),(33,"New")))
        result=guard.compare(self.old,guard.scan(self.project))
        self.assertEqual(result["status"],"ADDITIONS_ONLY")
        doc=renderer.render_report(result).decode()
        self.assertIn("New objects only",doc)
        self.assertIn("Identity retained",doc)
        self.assertIn("Renamed Player",doc)

    def test_html_escapes_all_user_supplied_strings_and_no_external_assets(self):
        result=guard.compare(self.old,self.old)
        attack='<script src="https://attacker.invalid/x"></script> & <img src=x onerror=alert(9)>'
        result["lost"].append(dict(kind="scene",asset_guid=GUID_A,local_file_id="11",
                                   path="Assets/Scenes/"+attack+".unity",name=attack))
        result["status"]="REVIEW_REQUIRED"
        html=renderer.render_report(result).decode()
        self.assertIn("&lt;script",html)
        self.assertIn("&lt;img",html)
        self.assertNotIn("<script",html.lower())
        self.assertNotIn("<img",html.lower())
        self.assertNotIn('href="https://',html)
        self.assertIn("base-uri 'none'",html)
        self.assertIn("script-src 'none'",html)
        self.assertIn("img-src 'none'",html)

    def test_bad_comparison_refused_without_creating_report(self):
        result=guard.compare(self.old,self.old)
        result["scope"]="claims all Player save compatibility"
        with self.assertRaises(ValueError):
            renderer.render_report(result)
        self.assertFalse(self.html.exists())

    def test_html_render_limit_makes_omission_obvious(self):
        result=guard.compare(self.old,self.old)
        count=renderer.MAX_VISIBLE_ROWS+7
        result["status"]="REVIEW_REQUIRED"
        result["lost"]=[{"name":str(i),"path":"Assets/Scenes/Test.unity",
                         "asset_guid":GUID_A,"local_file_id":str(i+1)}
                        for i in range(count)]
        doc=renderer.render_report(result).decode()
        self.assertIn("complete machine-readable JSON",doc)
        self.assertIn("of "+str(count),doc)
        self.assertLess(len(doc),500000)

    def test_no_creating_json_or_html_inside_readonly_project(self):
        guard._write_new(self.baseline,(json.dumps(self.old)+"\n").encode())
        for ext in ("--out","--html-out"):
            inside=self.project/"Assets"/("bad."+("html" if ext=="--html-out" else "json"))
            stderr=io.StringIO()
            with redirect_stderr(stderr):
                rc=guard.main(["check",str(self.project),"--baseline",str(self.baseline),ext,str(inside)])
            self.assertEqual(rc,3)
            self.assertIn("outside the Unity project",stderr.getvalue())
            self.assertFalse(inside.exists())

    def test_symlinked_output_parent_is_refused(self):
        guard._write_new(self.baseline,(json.dumps(self.old)+"\n").encode())
        (self.root/"link").symlink_to(self.project/"Assets",target_is_directory=True)
        stderr=io.StringIO()
        with redirect_stderr(stderr):
            rc=guard.main(["check",str(self.project),"--baseline",str(self.baseline),
                           "--html-out",str(self.root/"link"/"bad.html")])
        self.assertEqual(rc,3)
        self.assertIn("Linked output parent",stderr.getvalue())
        self.assertFalse((self.project/"Assets"/"bad.html").exists())

    def test_html_output_is_create_only_and_preserves_existing_data(self):
        guard._write_new(self.baseline,(json.dumps(self.old)+"\n").encode())
        self.html.write_text("CUSTOMER DATA")
        stderr=io.StringIO()
        with redirect_stderr(stderr):
            self.assertEqual(guard.main(["check",str(self.project),"--baseline",str(self.baseline),
                                          "--html-out",str(self.html)]),3)
        self.assertEqual(self.html.read_text(),"CUSTOMER DATA")

    def test_capture_rejects_html_request(self):
        stderr=io.StringIO()
        with redirect_stderr(stderr):
            with self.assertRaises(SystemExit):
                guard.main(["capture",str(self.project),"--html-out",str(self.html)])
        self.assertFalse(self.html.exists())


if __name__ == "__main__":
    unittest.main()
