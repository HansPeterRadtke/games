"""Independent minimal deterministic checks; no Unity process or SDK required."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

SRC = Path(__file__).resolve().parents[1] / "hpr_scene_identity.py"
spec = importlib.util.spec_from_file_location("hpr_identity", SRC)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
GUID_A = "0123456789abcdef0123456789abcdef"
GUID_B = "fedcba9876543210fedcba9876543210"


def scene(*objects):
    parts = ["%YAML 1.1","%TAG !u! tag:unity3d.com,2011:"]
    for fileid,name in objects:
        parts += ["--- !u!1 &"+str(fileid),"GameObject:","  m_Name: "+name]
    return ("\n".join(parts)+"\n").encode()


def meta(guid):
    return ("fileFormatVersion: 2\nguid: "+guid+"\n").encode()


class SceneIdentityTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory(prefix="hpr-identity-light-")
        self.addCleanup(self.dir.cleanup)
        self.project = Path(self.dir.name) / "Project"
        (self.project / "ProjectSettings").mkdir(parents=True)
        (self.project / "ProjectSettings/ProjectVersion.txt").write_text("m_EditorVersion: 2022.3.22f1\n")
        (self.project / "Assets/Scenes").mkdir(parents=True)
        self.source = self.project / "Assets/Scenes/Intro.unity"
        self.source.write_bytes(scene((11,"Player"),(22,"Door")))
        self.source.with_suffix(".unity.meta").write_bytes(meta(GUID_A))
        self.prev = Path(self.dir.name) / "approved.json"
        self.current = Path(self.dir.name) / "review.json"

    def test_snapshot_stable_rename_and_reorder(self):
        expected = guard.scan(self.project)
        self.assertEqual(expected["direct_object_count"],2)
        self.assertTrue(expected["complete"])
        self.assertEqual(expected["coverage"],guard.COVERAGE)
        self.assertEqual(guard.main(["capture",str(self.project),"--out",str(self.prev)]),0)
        first_snapshot = json.loads(self.prev.read_text())
        self.source.write_bytes(scene((22,"Door"),(11,"Renamed player")))
        other = self.project / "Assets/Scenes/Landing.unity"
        self.source.rename(other)
        self.source.with_suffix(".unity.meta").rename(other.with_suffix(".unity.meta"))
        self.assertEqual(guard.compare(first_snapshot,guard.scan(self.project))["status"],"IDENTITY_STABLE")
        changes = guard.compare(first_snapshot,guard.scan(self.project))["renamed_or_moved_without_identity_loss"]
        self.assertEqual(len(changes),2)
        self.assertFalse(changes[0]["was_path"] == changes[0]["now_path"])
        self.assertFalse(self.current.exists())

    def test_missing_id_requires_review_and_never_edits_originals(self):
        guard.main(["capture",str(self.project),"--out",str(self.prev)])
        original_before = hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.source.write_bytes(scene((11,"Player")))
        edited_bytes = self.source.read_bytes()
        rc = guard.main(["check",str(self.project),"--baseline",str(self.prev),"--out",str(self.current)])
        self.assertEqual(rc,1)
        result = json.loads(self.current.read_text())
        self.assertEqual(result["status"],"REVIEW_REQUIRED")
        self.assertEqual([v["local_file_id"] for v in result["lost"]],["22"])
        self.assertEqual(self.source.read_bytes(),edited_bytes)
        self.assertNotEqual(hashlib.sha256(edited_bytes).hexdigest(),original_before)

    def test_guid_change_or_new_gameobject(self):
        approved = guard.scan(self.project)
        self.source.with_suffix(".unity.meta").write_bytes(meta(GUID_B))
        diff = guard.compare(approved,guard.scan(self.project))
        self.assertEqual(diff["status"],"REVIEW_REQUIRED")
        self.assertEqual(len(diff["changed_asset_guids"]),1)
        self.source.with_suffix(".unity.meta").write_bytes(meta(GUID_A))
        self.source.write_bytes(scene((11,"Player"),(22,"Door"),(33,"New")))
        self.assertEqual(guard.compare(approved,guard.scan(self.project))["status"],"ADDITIONS_ONLY")

    def test_duplicate_fileid_and_duplicate_asset_guid_are_incomplete(self):
        self.source.write_bytes(scene((11,"A"),(11,"B")))
        with self.assertRaisesRegex(guard.IncompleteScan,"Duplicate GameObject"):
            guard.scan(self.project)
        self.source.write_bytes(scene((11,"A")))
        another = self.project / "Assets/Scenes/Again.unity"
        another.write_bytes(scene((55,"C")))
        another.with_suffix(".unity.meta").write_bytes(meta(GUID_A))
        with self.assertRaisesRegex(guard.IncompleteScan,"Duplicate asset GUID"):
            guard.scan(self.project)

    def test_no_false_clean_for_binary_missing_meta_or_variant(self):
        self.source.write_bytes(b"binary file")
        with self.assertRaisesRegex(guard.IncompleteScan,"Force Text"):
            guard.scan(self.project)
        self.source.write_bytes(scene((11,"Player")))
        self.source.with_suffix(".unity.meta").unlink()
        with self.assertRaisesRegex(guard.IncompleteScan,"Cannot read file"):
            guard.scan(self.project)
        self.source.with_suffix(".unity.meta").write_bytes(meta(GUID_A))
        self.source.write_text("%YAML 1.1\n--- !u!1001 &17\nPrefabInstance:\n",encoding="utf-8")
        with self.assertRaisesRegex(guard.IncompleteScan,"No directly"):
            guard.scan(self.project)

    def test_skip_stripped_docs_and_never_claim_complete_prefab_coverage(self):
        self.source.write_bytes(scene((11,"Direct"))+b"--- !u!1 &99 stripped\nGameObject:\n  m_Name: Inherited\n")
        snapshot=guard.scan(self.project)
        self.assertEqual(len(snapshot["objects"]),1)
        self.assertEqual(snapshot["stripped_prefab_documents_not_resolved"],1)
        self.assertIn("direct",snapshot["coverage"])

    def test_empty_project_and_directory_symlink_fail_closed(self):
        self.source.unlink()
        self.source.with_suffix(".unity.meta").unlink()
        with self.assertRaisesRegex(guard.IncompleteScan,"No .unity"):
            guard.scan(self.project)
        self.source.write_bytes(scene((11,"Recovered")))
        self.source.with_suffix(".unity.meta").write_bytes(meta(GUID_A))
        (self.project/"Assets/Linked").symlink_to(self.project/"Assets/Scenes")
        with self.assertRaisesRegex(guard.IncompleteScan,"Linked asset folder"):
            guard.scan(self.project)

    def test_asset_symlink_rejected(self):
        other = Path(self.dir.name)/"external"
        other.write_bytes(scene((17,"Other")))
        self.source.unlink()
        self.source.symlink_to(other)
        with self.assertRaisesRegex(guard.IncompleteScan,"Not a regular file"):
            guard.scan(self.project)

    def test_baseline_duplicate_or_path_escape_rejected(self):
        guard.main(["capture",str(self.project),"--out",str(self.prev)])
        data=json.loads(self.prev.read_text())
        data["objects"].append(dict(data["objects"][0]))
        data["direct_object_count"]+=1
        self.prev.write_text(json.dumps(data))
        with self.assertRaisesRegex(guard.IncompleteScan,"Repeated baseline identity"):
            guard._validated_snapshot(self.prev)
        data["objects"].pop()
        data["direct_object_count"]-=1
        data["objects"][0]["path"]="Assets/../../tmp/secret.unity"
        self.prev.write_text(json.dumps(data))
        with self.assertRaisesRegex(guard.IncompleteScan,"Unsafe"):
            guard._validated_snapshot(self.prev)

    def test_create_only_outputs(self):
        self.prev.write_text("KEEP")
        err=io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(guard.main(["capture",str(self.project),"--out",str(self.prev)]),3)
        self.assertEqual(self.prev.read_text(),"KEEP")
        self.assertIn("INCOMPLETE",err.getvalue())

    def test_missing_baseline_no_report(self):
        err=io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(guard.main(["check",str(self.project),"--baseline",str(self.prev),"--out",str(self.current)]),3)
        self.assertFalse(self.current.exists())

    def test_wrong_yaml_document_type_fails_closed(self):
        self.source.write_text("%YAML 1.1\n--- !u!1 &88\nSomethingElse:\n  m_Name: phantom\n")
        with self.assertRaisesRegex(guard.IncompleteScan,"type marker"):
            guard.scan(self.project)

    def test_signed_negative_local_file_id_is_not_silently_dropped(self):
        self.source.write_bytes(scene((-922,"Hidden"),(22,"Door")))
        before=guard.scan(self.project)
        self.assertEqual(len(before["objects"]),2)
        self.assertEqual(sorted(x["local_file_id"] for x in before["objects"]),["-922","22"])
        self.source.write_bytes(scene((22,"Door")))
        after=guard.compare(before,guard.scan(self.project))
        self.assertEqual(after["status"],"REVIEW_REQUIRED")
        self.assertEqual(after["lost"][0]["local_file_id"],"-922")

    def test_cross_asset_baseline_rewrite_cannot_hide_churn(self):
        guard.main(["capture",str(self.project),"--out",str(self.prev)])
        baseline=json.loads(self.prev.read_text())
        baseline["objects"][0]["path"]="Assets/Scenes/SomethingElse.unity"
        self.prev.write_text(json.dumps(baseline))
        with self.assertRaisesRegex(guard.IncompleteScan,"disagree"):
            guard._validated_snapshot(self.prev)

    def test_size_limit_refuses(self):
        with mock.patch.object(guard,"MAX_BYTES_EACH",20):
            with self.assertRaisesRegex(guard.IncompleteScan,"size limit"):
                guard.scan(self.project)

    def test_fifo_scan_boundary_fails_without_blocking(self):
        self.source.unlink()
        os.mkfifo(self.source)
        with self.assertRaisesRegex(guard.IncompleteScan,"regular file"):
            guard.scan(self.project)

    def test_unsupported_class_one_yaml_header_is_incomplete(self):
        self.source.write_bytes(scene((11,"Player"))+b"--- !u!1 &id-string\nGameObject:\n  m_Name: Unexpected\n")
        with self.assertRaisesRegex(guard.IncompleteScan,"Unsupported GameObject"):
            guard.scan(self.project)

    def test_unreadable_asset_directory_fails_closed(self):
        def denied(*args, **kwargs):
            kwargs["onerror"](PermissionError("mocked directory read failure"))
            return iter(())
        with mock.patch.object(guard.os, "walk", side_effect=denied):
            with self.assertRaisesRegex(guard.IncompleteScan,"Cannot enumerate Unity Assets"):
                guard.scan(self.project)

    def test_fifo_baseline_boundary_fails_without_blocking(self):
        os.mkfifo(self.prev)
        with self.assertRaisesRegex(guard.IncompleteScan,"regular file"):
            guard._validated_snapshot(self.prev)

    def test_original_saved_unity_files_are_read_without_mutation(self):
        project=Path(__file__).resolve().parents[4]/"projects/fps_demo"
        if not project.exists():
            self.skipTest("Original first-party saved Unity sample not in this checkout")
        manifests={}
        for asset in project.glob("Assets/**/*.unity"):
            manifests[str(asset)]=hashlib.sha256(asset.read_bytes()).hexdigest()
        read=guard.scan(project)
        self.assertGreater(read["direct_object_count"],10)
        self.assertEqual(read["asset_count"],3)
        for name,digest in manifests.items():
            self.assertEqual(hashlib.sha256(Path(name).read_bytes()).hexdigest(),digest)
        (Path(self.dir.name)/"real-summary.json").write_text(json.dumps({"status":"PASSED_SAVED_FILE_ONLY","assets":read["asset_count"],"direct_objects":read["direct_object_count"]}))


if __name__ == "__main__":
    unittest.main()
