"""Fail-closed Unity Asset Store archive validator against real export metadata.

These unit tests use disposable synthetic archives. Real frozen-candidate
inspection runs separately, with a read-only SHA-pinned input.
"""
import io
import json
import os
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/"unity/tools/release/gameplay_suite/qa"
sys.path.insert(0,str(QA))
import unity_archive_policy as checker

def unitypackage(dest,files):
    """Each tuple = GUID, Unity asset path, payload or None (folder)."""
    with tarfile.open(dest,"w:gz") as tf:
        for guid,path,payload in files:
            streams=[("pathname",path.encode()),
                     ("asset.meta",("fileFormatVersion: 2\nguid: "+guid+"\n").encode())]
            if payload is not None:
                streams.append(("asset",payload if isinstance(payload,bytes) else payload.encode()))
            for suffix,data in streams:
                member=tarfile.TarInfo(guid+"/"+suffix)
                member.size=len(data)
                tf.addfile(member,io.BytesIO(data))

def definition(name,refs=()):
    return json.dumps({"name":name,"references":list(refs)}).encode()

ROOT_FOLDER=("f"*32,"Assets/HPRGameplaySuite",None)
ASM_1=("a"*32,
       "Assets/HPRGameplaySuite/Modules/com.hpr.abilities/Runtime/HPR.Abilities.Runtime.asmdef",
       definition("HPR.Abilities.Runtime",["HPR.Stats.Runtime"]))
ASM_2=("b"*32,
       "Assets/HPRGameplaySuite/Modules/com.hpr.stats/Runtime/HPR.Stats.Runtime.asmdef",
       definition("HPR.Stats.Runtime"))
SCRIPT=("c"*32,"Assets/HPRGameplaySuite/Editor/HprSampleInstaller.cs","namespace HPR {}")

class ValidatedArchive(unittest.TestCase):
    def setUp(self):
        self.working=tempfile.TemporaryDirectory(prefix="hpr_archive_policy_")
        self.addCleanup(self.working.cleanup)
        self.out=Path(self.working.name)/"test.unitypackage"

    def check(self,*items):
        unitypackage(self.out,items or (ROOT_FOLDER,ASM_1,ASM_2,SCRIPT))
        return checker.inspect_archive(self.out)

    def test_valid_unity_package_has_unique_asset_guid_and_assembly_refs(self):
        r=self.check()
        self.assertEqual("PASS",r["status"])
        self.assertEqual(4,r["asset_count"])
        self.assertEqual(2,r["assembly_definitions"])
        self.assertEqual([],r["issues"])
        self.assertTrue(r["read_only"])

    def test_legacy_directory_preview_and_modern_members_identify_the_same_assets(self):
        self.check()
        legacy = self.out.with_name("legacy.unitypackage")
        with tarfile.open(self.out, "r:gz") as source, tarfile.open(legacy, "w:gz") as output:
            for name in (".", "./" + SCRIPT[0]):
                directory = tarfile.TarInfo(name)
                directory.type = tarfile.DIRTYPE
                output.addfile(directory)
            for member in source:
                data = source.extractfile(member).read()
                member.name = "./" + member.name
                output.addfile(member, io.BytesIO(data))
            png = b"\x89PNG\r\n\x1a\nsynthetic thumbnail record"
            thumb = tarfile.TarInfo("./" + SCRIPT[0] + "/preview.png")
            thumb.size = len(png)
            output.addfile(thumb, io.BytesIO(png))
        report = checker.inspect_archive(legacy)
        self.assertEqual(report["status"], "PASS", report)
        records = checker.read_package_members(legacy)
        self.assertEqual(records.pop(SCRIPT[0] + "/preview.png"), png)
        self.assertEqual(records, checker.read_package_members(self.out))

    def test_legacy_syntax_preserves_collision_and_path_checks(self):
        self.check()
        for kind, name, data in (
            (tarfile.REGTYPE, "./" + SCRIPT[0] + "/pathname", b"duplicate"),
            (tarfile.REGTYPE, "./../" + SCRIPT[0] + "/asset", b"escape"),
            (tarfile.DIRTYPE, "./" + "1" * 32, b""),
            (tarfile.SYMTYPE, "./" + SCRIPT[0] + "/preview.png", b""),
            (tarfile.REGTYPE, "./" + SCRIPT[0] + "/preview.png", b"unexpected"),
        ):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                invalid = Path(temporary) / "invalid.unitypackage"
                with tarfile.open(self.out, "r:gz") as source, tarfile.open(invalid, "w:gz") as output:
                    for member in source:
                        output.addfile(member, source.extractfile(member))
                    extra = tarfile.TarInfo(name)
                    extra.type = kind
                    extra.size = len(data)
                    output.addfile(extra, io.BytesIO(data))
                with self.assertRaisesRegex(ValueError, "Invalid Unity archive"):
                    checker.read_package_members(invalid)

    def test_broken_asmdef_reference_rejected(self):
        bad=("a"*32,ASM_1[1],definition("HPR.Abilities.Runtime",["HPR.Unshipped.Runtime"]))
        r=self.check(ROOT_FOLDER,bad,ASM_2,SCRIPT)
        self.assertEqual("FAIL",r["status"])
        self.assertTrue(any("missing assembly" in issue for issue in r["issues"]))

    def test_duplicate_assembly_name_rejected(self):
        bad=("b"*32,ASM_2[1],definition("HPR.Abilities.Runtime"))
        self.assertEqual("FAIL",self.check(ROOT_FOLDER,ASM_1,bad,SCRIPT)["status"])

    def test_duplicate_guid_or_asset_path_rejected(self):
        same_guid=("c"*32,"Assets/HPRGameplaySuite/Demo/Other.asset","good")
        self.assertEqual("FAIL",self.check(ROOT_FOLDER,ASM_1,ASM_2,SCRIPT,same_guid)["status"])
        dup_name=("d"*32,SCRIPT[1],"other")
        self.assertEqual("FAIL",self.check(ROOT_FOLDER,ASM_1,ASM_2,SCRIPT,dup_name)["status"])

    def test_windows_case_insensitive_path_collision_rejected(self):
        second=("d"*32,"Assets/HPRGameplaySuite/Editor/hprsampleinstaller.cs","different content")
        result=self.check(ROOT_FOLDER,ASM_1,ASM_2,SCRIPT,second)
        self.assertEqual("FAIL",result["status"])
        self.assertTrue(any("case-insensitive" in issue for issue in result["issues"]))

    def test_macos_unicode_normalization_equivalent_paths_rejected(self):
        composed=("d"*32,"Assets/HPRGameplaySuite/Editor/Caf\u00e9.cs","one")
        decomposed=("e"*32,"Assets/HPRGameplaySuite/Editor/Cafe\u0301.cs","two")
        result=self.check(ROOT_FOLDER,ASM_1,ASM_2,SCRIPT,composed,decomposed)
        self.assertEqual("FAIL",result["status"])
        self.assertTrue(any("unicode" in issue.lower() or "normalization" in issue.lower()
                            for issue in result["issues"]))

    def test_windows_reserved_device_filenames_refused(self):
        for filename in ("CON.cs", "NUL.asset", "aux.cs", "COM1.txt"):
            with self.subTest(filename=filename):
                item=("d"*32,"Assets/HPRGameplaySuite/Editor/"+filename,"data")
                result=self.check(ROOT_FOLDER,ASM_1,ASM_2,SCRIPT,item)
                self.assertEqual("FAIL",result["status"])
                self.assertTrue(any("unsafe" in issue for issue in result["issues"]))

    def test_windows_trailing_space_or_dot_segment_rejected(self):
        for name in ("Assets/HPRGameplaySuite/Editor/Tool. ",
                     "Assets/HPRGameplaySuite/Editor/Module. /Source.cs",
                     "Assets/HPRGameplaySuite/Editor/TrailingDot."):
            with self.subTest(name=name):
                result=self.check(ROOT_FOLDER,ASM_1,ASM_2,SCRIPT,("d"*32,name,"data"))
                self.assertEqual("FAIL",result["status"])
                self.assertTrue(any("unsafe" in issue for issue in result["issues"]))

    def test_unapproved_test_runner_and_nonroot_asset_rejected(self):
        bad=("d"*32,"Assets/HPRGameplaySuite/Tests/HPR.TestRunner.cs","namespace HPR {}")
        self.assertEqual("FAIL",self.check(ROOT_FOLDER,ASM_1,ASM_2,SCRIPT,bad)["status"])
        bad2=("d"*32,"Assets/OtherTool/Surprise.cs","namespace OtherTool {}")
        self.assertEqual("FAIL",self.check(ROOT_FOLDER,ASM_1,ASM_2,SCRIPT,bad2)["status"])

    def test_long_path_and_traversal_refused(self):
        long=("d"*32,"Assets/HPRGameplaySuite/"+"a"*160+".cs","namespace HPR {}")
        self.assertEqual("FAIL",self.check(ROOT_FOLDER,ASM_1,ASM_2,SCRIPT,long)["status"])
        traversal=("d"*32,"Assets/HPRGameplaySuite/../Out.cs","namespace HPR {}")
        self.assertEqual("FAIL",self.check(ROOT_FOLDER,ASM_1,ASM_2,SCRIPT,traversal)["status"])

    def test_missing_file_asset_body_is_not_silently_treated_as_folder(self):
        missing=("d"*32,"Assets/HPRGameplaySuite/Editor/Missing.cs",None)
        self.assertEqual("FAIL",self.check(ROOT_FOLDER,ASM_1,ASM_2,SCRIPT,missing)["status"])

    def test_missing_root_folder_and_guid_meta_mismatch_rejected(self):
        self.assertEqual("FAIL",self.check(ASM_1,ASM_2,SCRIPT)["status"])
        unitypackage(self.out,(ROOT_FOLDER,ASM_1,ASM_2,SCRIPT))
        with tarfile.open(self.out,"r:gz") as tf:
            old=[(x,tf.extractfile(x).read() if x.isfile() else b"") for x in tf]
        with tarfile.open(self.out,"w:gz") as tf:
            for oldmeta,data in old:
                if oldmeta.name=="c"*32+"/asset.meta":
                    data=data.replace(b"guid: "+b"c"*32,b"guid: "+b"d"*32)
                m=tarfile.TarInfo(oldmeta.name);m.size=len(data)
                tf.addfile(m,io.BytesIO(data))
        self.assertEqual("FAIL",checker.inspect_archive(self.out)["status"])

    def test_absolute_archive_entry_rejected(self):
        unitypackage(self.out,(ROOT_FOLDER,ASM_1,ASM_2,SCRIPT))
        with tarfile.open(self.out,"a") if False else tarfile.open(self.out,"w:gz") as tf:
            p=b"Assets/HPRGameplaySuite"
            m=tarfile.TarInfo("/evil/pathname");m.size=len(p);tf.addfile(m,io.BytesIO(p))
        self.assertEqual("FAIL",checker.inspect_archive(self.out)["status"])

    def test_frozen_archive_is_readonly_no_repack_or_rewrite(self):
        r=self.check()
        before=self.out.read_bytes()
        after=checker.inspect_archive(self.out)
        self.assertEqual("PASS",after["status"])
        self.assertEqual(before,self.out.read_bytes())


if __name__=="__main__":
    unittest.main()
