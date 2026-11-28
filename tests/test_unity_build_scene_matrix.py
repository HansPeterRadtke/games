"""Offline archive-boundary regression tests, not Unity import acceptance."""
import hashlib
import importlib.util
import io
from pathlib import Path
import re
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "unity/tools/release/build_scene_matrix"
SRC = MATRIX / "Assets"
SPEC = importlib.util.spec_from_file_location("matrix_archive", MATRIX / "qa/verify_archive.py")
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class SceneMatrixArchiveContract(unittest.TestCase):
    def records(self):
        items = []
        for p in sorted(SRC.rglob("*")):
            if p.name.endswith(".meta"):
                continue
            meta = Path(str(p) + ".meta").read_bytes()
            guid = re.search(rb"(?m)^guid: ([0-9a-f]{32})$", meta).group(1).decode()
            items.append((guid + "/pathname", ("Assets/" + p.relative_to(SRC).as_posix()).encode()))
            items.append((guid + "/asset.meta", meta))
            if p.is_file():
                items.append((guid + "/asset", p.read_bytes()))
        return items

    def archive(self, tmp, items):
        p = Path(tmp) / "synthetic-boundary-fixture.unitypackage"
        with tarfile.open(p, "w:gz") as t:
            for name, blob in items:
                entry = tarfile.TarInfo(name)
                entry.size = len(blob)
                t.addfile(entry, io.BytesIO(blob))
        return p

    def test_current_source_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = self.archive(tmp, self.records())
            result = MOD.inspect(p, SRC)
            self.assertEqual(len(result["paths"]), 7)
            self.assertEqual(result["sha256"], hashlib.sha256(p.read_bytes()).hexdigest())
            self.assertEqual(result["paths"]["Assets/HPRBuildSceneMatrix/Editor/HprBuildSceneMatrix.cs"],
                             "16c37836d9d94dc39063b7c6053b5eb5")
            self.assertTrue(result["no_qa_assets"])
            self.assertTrue(result["exact_authored_payloads"])

    def check_rejected(self, items):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises((AssertionError, KeyError, ValueError, UnicodeError)):
                MOD.inspect(self.archive(tmp, items), SRC)

    def test_reject_missing_new_core(self):
        items = self.records()
        guid = next(n.split("/")[0] for n, b in items
                    if n.endswith("/pathname") and b.endswith(b"/HprSceneMatrixCore.cs"))
        self.check_rejected([(n,b) for n,b in items if not n.startswith(guid + "/")])

    def test_reject_modified_source_payload(self):
        items = self.records()
        index = next(i for i,(n,b) in enumerate(items)
                     if n.endswith("/asset") and b"public sealed class HprSceneBaseline" in b)
        n,b = items[index]
        items[index] = (n,b+b"\n// unexpected edit")
        self.check_rejected(items)

    def test_reject_extra_or_traversal_member(self):
        self.check_rejected(self.records() + [("../unexpected",b"x")])

    def test_reject_duplicate_record(self):
        items = self.records()
        self.check_rejected(items+[items[0]])

    def test_reject_wrong_guid_metadata(self):
        items = self.records()
        i = next(i for i,(n,b) in enumerate(items) if n.endswith("/asset.meta"))
        n,b = items[i]
        items[i] = (n, re.sub(rb"(?m)^guid: [0-9a-f]{32}$", b"guid: " + b"0"*32, b))
        self.check_rejected(items)

    def test_reject_qa_path(self):
        items = self.records()
        i = next(i for i,(n,b) in enumerate(items)
                 if n.endswith("/pathname") and b.endswith(b"/README.md"))
        items[i] = (items[i][0], b"Assets/HPRBuildSceneMatrix/qa/Program.cs")
        self.check_rejected(items)

    def test_reject_link_member(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = self.archive(tmp,self.records())
            q = Path(tmp) / "link-fixture.unitypackage"
            with tarfile.open(p) as a, tarfile.open(q,"w:gz") as b:
                for m in a:
                    b.addfile(m,a.extractfile(m))
                m = tarfile.TarInfo("f"*32+"/asset")
                m.type = tarfile.SYMTYPE
                m.linkname = "/etc/passwd"
                b.addfile(m)
            with self.assertRaises(AssertionError):
                MOD.inspect(q,SRC)


class SceneMatrixCompanionContract(unittest.TestCase):
    def test_companion_links_exact_editor_independent_core_and_is_outside_assets(self):
        companion = MATRIX / "companion"
        project = (companion / "HprSceneGate.csproj").read_text()
        for filename in ("HprSceneMatrixCore.cs", "HprSceneBaseline.cs"):
            self.assertIn("$(HprSourceRoot)/" + filename, project)
        self.assertIn("<TargetFramework>net10.0</TargetFramework>", project)
        self.assertIn("<RuntimeFrameworkVersion>10.0.15</RuntimeFrameworkVersion>", project)
        self.assertIn("<RollForward>LatestPatch</RollForward>", project)
        for source in (companion / "Program.cs", companion / "SavedUnitySceneLists.cs"):
            text = source.read_text()
            self.assertNotIn("using UnityEditor;", text)
            self.assertNotIn("using UnityEngine;", text)
            self.assertNotIn("Process.Start", text)
        self.assertFalse(list(SRC.rglob("HprSceneGate.dll")))
        self.assertFalse(list(SRC.rglob("SavedUnitySceneLists.cs")))

    def test_disabled_scene_position_is_visible_and_csv_never_loses_it(self):
        editor = (SRC / "HPRBuildSceneMatrix/Editor/HprBuildSceneMatrix.cs").read_text()
        core = (SRC / "HPRBuildSceneMatrix/Editor/HprSceneMatrixCore.cs").read_text()
        native = (MATRIX / "qa/offline/tests/Program.cs").read_text()
        for statement in ("declaredDelta.Positions.Count", "position.Reference",
                          "position.Compared", "declared-position changes",
                          "Export full comparison CSV"):
            self.assertIn(statement, editor)
        for statement in ("Declared position ", "Declared entry sequence",
                          "CompareDeclaredLists(a, b)", "Different scene asset at this list position"):
            self.assertIn(statement, core + editor)
        self.assertIn("this does not prove regeneration", editor)
        self.assertIn("live-disabled-reorder.csv", native)
        self.assertIn("live to live CSV reports a structural change", native)
        self.assertIn("shared core identifies both disabled-scene move positions", native)
        native_fixture = (MATRIX / "qa/HprBuildSceneMatrixQa.cs").read_text()
        for marker in ("ACTUAL_DISABLED_ENTRY_REORDER_PASS", "NATIVE_LIVE_CSV_DECLARED_POSITIONS_PASS",
                       "NATIVE_EDITOR_WINDOW_CHANGED_POSITIONS_PASS", "disabled-entry-move-native-live-comparison.csv",
                       "EditorWindow.GetWindow<HprBuildSceneMatrixWindow>", "DisabledShift"):
            self.assertIn(marker, native_fixture)

    def test_ui_and_companion_share_declared_list_delta(self):
        core = (SRC / "HPRBuildSceneMatrix/Editor/HprSceneMatrixCore.cs").read_text()
        editor = (SRC / "HPRBuildSceneMatrix/Editor/HprBuildSceneMatrix.cs").read_text()
        companion = (MATRIX / "companion/Program.cs").read_text()
        self.assertIn("CompareDeclaredLists", core)
        self.assertIn("HprSceneMatrix.CompareDeclaredLists", editor)
        self.assertIn("HprSceneMatrix.CompareDeclaredLists", companion)
        self.assertIn("FirstDifferingEntryIndex", editor)
        self.assertIn("FirstDifferingEntryIndex", companion)

    def test_companion_packaging_requires_both_exact_process_receipts(self):
        packaging = (MATRIX / "companion/qa/package_private.py").read_text()
        self.assertIn('companion-process-receipt.json', packaging)
        self.assertIn('saved-project-process-receipt.json', packaging)
        self.assertIn('Packaged executable differs from actually tested output', packaging)
        self.assertIn('PRIVATE_COMPANION_CANDIDATE_NOT_PUBLISHED', packaging)
        self.assertIn('"runtime_included":False', packaging)


if __name__ == "__main__":
    unittest.main()
