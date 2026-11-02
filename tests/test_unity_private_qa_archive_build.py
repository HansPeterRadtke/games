"""Build a private, identity-preserving Unity tar-format QA archive.

No Unity process, publisher submission, network or original source writes.
An actual Unity Editor import remains a separately required release gate.
"""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/"unity/tools/release/gameplay_suite/qa"
sys.path.insert(0,str(QA))
import unity_private_qa_archive_build as builder
import unity_archive_policy as policy

RELPATH="unity/tools/release/gameplay_suite/README.md"
PACKAGEPATH="Assets/HPRGameplaySuite/README.md"
GUID_ROOT="f"*32
GUID_CONTENT="a"*32


def make_archive(path, payload: bytes):
    rows=((GUID_ROOT, "Assets/HPRGameplaySuite", None),
          (GUID_CONTENT, PACKAGEPATH, payload))
    with tarfile.open(path,"w:gz") as tf:
        for guid,name,blob in rows:
            streams=[("pathname",name.encode()),
                     ("asset.meta",("fileFormatVersion: 2\nguid: "+guid+"\n").encode())]
            if blob is not None:
                streams.append(("asset",blob))
            for suffix,data in streams:
                member=tarfile.TarInfo(guid+"/"+suffix)
                member.size=len(data)
                tf.addfile(member,io.BytesIO(data))


class PrivateRepack(unittest.TestCase):
    def setUp(self):
        self.td=tempfile.TemporaryDirectory(prefix="hpr_private_repack_")
        self.addCleanup(self.td.cleanup)
        self.root=Path(self.td.name)
        self.original=self.root/"original.unitypackage"
        self.frozen=self.root/"frozen"
        self.proposed=self.root/"proposal"
        self.output=self.root/"modified.unitypackage"
        for folder in (self.frozen,self.proposed):
            file=folder/RELPATH
            file.parent.mkdir(parents=True)
            file.write_text("version zero\n")
        (self.proposed/RELPATH).write_text("new version only in QA\n")
        make_archive(self.original,(self.frozen/RELPATH).read_bytes())
        self.mapping={RELPATH:PACKAGEPATH}

    def run_builder(self):
        return builder.build(self.original,self.frozen,self.proposed,self.output,
                             replacements=self.mapping)

    def test_changed_source_preserves_export_guid_and_all_untouched_bytes(self):
        prior=self.original.read_bytes()
        receipt=self.run_builder()
        self.assertEqual("PASS",receipt["status"])
        self.assertEqual(2,receipt["asset_count"])
        self.assertEqual([PACKAGEPATH],receipt["changed_asset_paths"])
        self.assertTrue(self.output.is_file())
        self.assertEqual(prior,self.original.read_bytes())
        self.assertEqual("PASS",policy.inspect_archive(self.output)["status"])
        with tarfile.open(self.output,"r:gz") as archive:
            parts={i.name:archive.extractfile(i).read() for i in archive}
        self.assertEqual((self.proposed/RELPATH).read_bytes(),
                         parts[GUID_CONTENT+"/asset"])
        self.assertIn(GUID_CONTENT.encode(),parts[GUID_CONTENT+"/asset.meta"])

    def test_identity_stable_output_reproducible_in_different_file(self):
        self.run_builder()
        digest=hashlib.sha256(self.output.read_bytes()).hexdigest()
        second=self.root/"another.unitypackage"
        builder.build(self.original,self.frozen,self.proposed,second,
                      replacements=self.mapping)
        self.assertEqual(digest,hashlib.sha256(second.read_bytes()).hexdigest())

    def test_repeating_existing_output_is_refused_and_does_not_rewrite(self):
        self.run_builder()
        before=self.output.read_bytes()
        with self.assertRaises(FileExistsError):
            self.run_builder()
        self.assertEqual(before,self.output.read_bytes())

    def test_changed_original_not_matching_archive_is_refused(self):
        (self.frozen/RELPATH).write_text("wrong prior content")
        with self.assertRaises(ValueError):
            self.run_builder()
        self.assertFalse(self.output.exists())

    def test_proposed_asset_changing_after_hash_inventory_is_refused(self):
        # Emulate a concurrent editor touching our OWN synthetic proposal
        # between the source-inventory hash and the archive byte read.
        # The build must stop before creating a misleading verified package.
        real_files = builder._files
        def source_changes_after_snapshot(root):
            report = real_files(root)
            if Path(root) == self.proposed:
                (self.proposed/RELPATH).write_text("changed after the audit hash")
            return report
        with mock.patch.object(builder,"_files",side_effect=source_changes_after_snapshot):
            with self.assertRaises(ValueError):
                self.run_builder()
        self.assertFalse(self.output.exists())

    def test_unapproved_additional_source_edit_refused(self):
        for root in (self.frozen,self.proposed):
            (root/"README-OTHER.md").write_text("unchanged")
        (self.proposed/"README-OTHER.md").write_text("hidden extra effect")
        with self.assertRaises(ValueError):
            self.run_builder()
        self.assertFalse(self.output.exists())

    def test_missing_proposed_asset_and_unexpected_symlink_refused(self):
        (self.proposed/RELPATH).unlink()
        with self.assertRaises(ValueError):
            self.run_builder()
        (self.proposed/RELPATH).symlink_to(self.root/"elsewhere")
        with self.assertRaises(ValueError):
            self.run_builder()

    def test_wrong_incoming_guid_or_malformed_archive_rejected(self):
        with tarfile.open(self.original,"w:gz") as archive:
            content=b"not a valid Unity package"
            item=tarfile.TarInfo("garbage")
            item.size=len(content)
            archive.addfile(item,io.BytesIO(content))
        with self.assertRaises(ValueError):
            self.run_builder()

    def test_output_inside_frozen_or_proposed_source_is_refused(self):
        for target in (self.frozen/"exports/new.unitypackage",
                       self.proposed/"builds/new.unitypackage"):
            with self.subTest(target=target),self.assertRaises(ValueError):
                builder.build(self.original,self.frozen,self.proposed,target,
                              replacements=self.mapping)
            self.assertFalse(target.exists())

    def test_receipt_path_must_not_overlap_any_original_or_output(self):
        for dest in (self.frozen/"private.json",self.proposed/"private.json",
                     self.original,self.output):
            with self.subTest(dest=dest),self.assertRaises(ValueError):
                builder.validate_receipt_path(dest,self.original,self.frozen,
                                              self.proposed,self.output)
        builder.validate_receipt_path(self.root/"safe_receipt.json",
                                      self.original,self.frozen,self.proposed,self.output)

    def test_missing_or_ambiguous_source_mapping_rejected(self):
        with self.assertRaises(ValueError):
            builder.build(self.original,self.frozen,self.proposed,self.output,
                          replacements={"unrelated":PACKAGEPATH})
        with self.assertRaises(ValueError):
            builder.build(self.original,self.frozen,self.proposed,self.output,
                          replacements={RELPATH:"Assets/Other/Outside.md"})
        self.assertFalse(self.output.exists())


if __name__=="__main__":
    unittest.main()
