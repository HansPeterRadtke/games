"""Exercise the source builder with a controlled Editor export and real release validation."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / "unity/tools/release/gameplay_suite"
ARCHIVE = "hpr-gameplay-systems-suite-candidate.unitypackage"
STATS = "HPRGameplaySuite/Modules/com.hpr.stats/Runtime/ActorStatsComponent.cs"


def version_probe(root, version):
    binary = root / "Unity"
    binary.write_text(f'#!/bin/sh\ntest "$1" = -version || exit 2\necho {version}\n')
    binary.chmod(0o700)
    return binary


def emit_package(assets, output, *, legacy=False, change=None):
    with tarfile.open(output, "w:gz") as archive:
        def record(name, body=None):
            member = tarfile.TarInfo(name)
            if body is None:
                member.type = tarfile.DIRTYPE
                archive.addfile(member)
            else:
                member.size = len(body)
                archive.addfile(member, io.BytesIO(body))

        if legacy:
            record(".")
        for meta in sorted(assets.rglob("*.meta")):
            file = meta.with_suffix("")
            guid = next(line.removeprefix("guid: ") for line in meta.read_text().splitlines()
                        if line.startswith("guid: "))
            rel = file.relative_to(assets).as_posix()
            folder = ("./" if legacy else "") + guid
            if legacy:
                record(folder)
            record(folder + "/pathname", ("Assets/" + rel).encode())
            record(folder + "/asset.meta", meta.read_bytes())
            if file.is_file():
                body = file.read_bytes()
                record(folder + "/asset", change(rel, body) if change else body)


class ReleaseExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        root = Path(cls.temp.name)
        cls.project = root / "project"
        cls.release = root / "release"
        cls.module = runpy.run_path(str(SOURCE / "build_gameplay_suite.py"))
        main = cls.module["main"]
        cls.settings = main.__globals__
        cls.settings.update(PROJECT=cls.project, RELEASE=cls.release,
                            UNITY=version_probe(root, "6000.6.8f1"))
        path = patch.object(sys, "path", [str(SOURCE), *sys.path])
        path.start()
        cls.addClassCleanup(path.stop)

        def initial_editor(args, label, env=None):
            if label == "create":
                cls.project.mkdir()
            else:
                emit_package(cls.project / "Assets", env["HPR_GAMEPLAY_SUITE_OUTPUT"])

        with (
            patch.dict(os.environ, HPR_UNPATCHED_EDITOR_INTERNAL_QA=""),
            patch.dict(cls.settings, run_editor=initial_editor),
            patch.object(sys, "argv", ["build"]),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            main()

    def read_outputs(self):
        return {name: (self.release / name).read_bytes()
                for name in (ARCHIVE, "source-manifest.json", "release-receipt.json")}

    def test_new_receipt_pins_validated_archive_and_source_manifest(self):
        outputs = self.read_outputs()
        receipt = json.loads(outputs["release-receipt.json"])
        self.assertEqual(json.loads(outputs["source-manifest.json"])["verified_patched_editor"], "6000.6.8f1")
        self.assertEqual(receipt["sha256"], hashlib.sha256(outputs[ARCHIVE]).hexdigest())
        self.assertEqual(receipt["source_manifest_sha256"], hashlib.sha256(outputs["source-manifest.json"]).hexdigest())
        self.assertEqual(receipt["validation"]["runtime_sources_checked"], 62)
        self.assertEqual(receipt["validation"]["editor_scripts_checked"], 3)
        self.assertEqual(receipt["validation"]["source_controlled_guids_verified"], 161)

    def test_cli_rejects_old_editor_before_writing_staging_or_release(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            binary = version_probe(root, "6000.6.7f1")
            project, release = root / "project", root / "release"
            env = dict(os.environ, UNITY_BIN=str(binary), HPR_UNPATCHED_EDITOR_INTERNAL_QA="",
                       HPR_SUITE_PROJECT_ROOT=str(project), HPR_SUITE_RELEASE_ROOT=str(release))
            result = subprocess.run([sys.executable, str(SOURCE / "build_gameplay_suite.py")],
                                    cwd=root, env=env, text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not verified as security-patched: 6000.6.7f1", result.stderr)
            self.assertFalse(project.exists())
            self.assertFalse(release.exists())

    def test_legacy_override_does_not_attest_a_patched_editor(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            release = root / "release"
            def fixture_export(args, label, env):
                emit_package(self.project / "Assets", env["HPR_GAMEPLAY_SUITE_OUTPUT"])

            with (
                patch.dict(os.environ, HPR_UNPATCHED_EDITOR_INTERNAL_QA="1"),
                patch.dict(self.settings, UNITY=version_probe(root, "6000.6.7f1"),
                           RELEASE=release, run_editor=fixture_export),
                patch.object(sys, "argv", ["build", "--reuse-project"]),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                self.settings["main"]()
            manifest = json.loads((release / "source-manifest.json").read_text())
            self.assertIsNone(manifest["verified_patched_editor"])

    def test_editor_success_without_new_archive_preserves_previous_release(self):
        before = self.read_outputs()
        with patch.dict(self.settings, run_editor=lambda *args: None):
            with self.assertRaisesRegex(ValueError, "Missing or trivial"):
                self.settings["export_candidate"]({"must": "never replace the old manifest"})
        self.assertEqual(self.read_outputs(), before)

    def test_changed_runtime_source_preserves_previous_release(self):
        before = self.read_outputs()
        def faulty_editor(args, label, env):
            emit_package(self.project / "Assets", env["HPR_GAMEPLAY_SUITE_OUTPUT"],
                         change=lambda name, data: b"broken code" if name == STATS else data)
        with patch.dict(self.settings, run_editor=faulty_editor):
            with self.assertRaisesRegex(ValueError, "runtime source differs.*ActorStatsComponent"):
                self.settings["export_candidate"]({"must": "be rejected"})
        self.assertEqual(self.read_outputs(), before)

    def test_legacy_directories_and_dot_prefix_preserve_all_runtime_identities(self):
        from validate_release import inspect
        with tempfile.TemporaryDirectory() as temporary:
            legacy = Path(temporary) / "legacy.unitypackage"
            emit_package(self.project / "Assets", legacy, legacy=True)
            self.assertEqual(inspect(legacy), inspect(self.release / ARCHIVE))

    def test_foreign_file_and_changed_module_guid_are_rejected(self):
        from validate_release import inspect
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            assets = root / "Assets"
            shutil.copytree(self.project / "Assets", assets)
            meta = assets / (STATS + ".meta")
            meta.write_text("guid: " + "a" * 32 + "\n")
            altered = root / "altered.unitypackage"
            emit_package(assets, altered)
            with self.assertRaisesRegex(ValueError, "Unstable buyer asset GUID.*ActorStatsComponent"):
                inspect(altered)
            foreign = assets / "HPRGameplaySuite/Samples/CustomerNotes.txt"
            foreign.write_text("Customer project notes")
            foreign.with_suffix(".txt.meta").write_text("guid: " + "b" * 32 + "\n")
            extra = root / "extra.unitypackage"
            emit_package(assets, extra)
            with self.assertRaisesRegex(ValueError, "Unexpected or missing buyer asset paths.*CustomerNotes"):
                inspect(extra)
