"""Test-first defects in buyer-package uninstall dependency auditing.

Unity's first-party Assembly Definition File Format documents .asmref JSON
as {"reference":"AssemblyName"} or {"reference":"GUID:32hex"}, not the
.asmdef "references":[...] array. Missing or malformed references must be
reported for review rather than treated as evidence of safe removal.
"""
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"unity/tools/release/gameplay_suite/qa/unity_uninstall_preflight.py"
SPEC=importlib.util.spec_from_file_location("uninstall_preflight_asmref",SOURCE)
preflight=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preflight)

GUID_ASMDEF="c42c4a8abb827303ed702e33a9ca1641"
GUID_SCRIPT="b264fbccf54cda999a913fe5c4089240"
NAME="HPR.Abilities.Runtime"

class UnityAssemblyReferenceSafety(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="hpr_asmref_owner_safety_")
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.project=self.root/"project"
        (self.project/"Assets/MyGame").mkdir(parents=True)
        self.asset=self.project/"Assets/MyGame/CustomerGameplay.asmref"
        self.archive=self.root/"seller.unitypackage"
        with tarfile.open(self.archive,"w:gz") as package:
            for guid,path in (
                (GUID_ASMDEF,"Assets/HPRGameplaySuite/Modules/com.hpr.abilities/Runtime/HPR.Abilities.Runtime.asmdef"),
                (GUID_SCRIPT,"Assets/HPRGameplaySuite/Modules/com.hpr.abilities/Runtime/AbilityRunnerComponent.cs")):
                binary=path.encode()
                member=tarfile.TarInfo(guid+"/pathname")
                member.size=len(binary)
                package.addfile(member,io.BytesIO(binary))

    def check(self,object):
        self.asset.write_text(json.dumps(object))
        return preflight.inspect(self.project,self.archive)

    def test_asmref_using_assembly_name_blocks_uninstall(self):
        report=self.check({"reference": NAME})
        self.assertEqual("customer_dependencies_found",report["classification"])
        self.assertTrue(any(x["kind"]=="asmref_reference" and
                            x["path"]=="Assets/MyGame/CustomerGameplay.asmref"
                            for x in report["dependencies"]))
        self.assertFalse(report["deletion_permitted"])

    def test_asmref_using_vendor_guid_blocks_uninstall(self):
        report=self.check({"reference":"GUID:"+GUID_ASMDEF})
        self.assertEqual("customer_dependencies_found",report["classification"])
        self.assertTrue(any(x["kind"]=="asmref_reference" for x in report["dependencies"]))

    def test_asmref_reference_to_other_assembly_not_false_positive(self):
        report=self.check({"reference":"OtherCompany.Physics.Runtime"})
        self.assertEqual("no_direct_reference_detected",report["classification"])
        self.assertEqual([],report["dependencies"])

    def test_malformed_asmref_fails_closed(self):
        for content in ({}, {"reference":None}, {"reference":""},
                        {"reference":[]}, {"reference":"GUID:not-a-guid"}):
            with self.subTest(content=content):
                report=self.check(content)
                self.assertEqual("unknown_project_content_requires_review",
                                 report["classification"])
                self.assertTrue(any("asmref" in u["reason"] for u in report["unknowns"]))
                self.assertFalse(report["deletion_permitted"])

    def test_asmdef_bad_reference_array_item_is_unknown(self):
        asset=self.project/"Assets/MyGame/Customer.asmdef"
        asset.write_text(json.dumps({
            "name":"Customer.Gameplay",
            "references":[None,17,{"source":"HPR.Abilities.Runtime"}],
        }))
        report=preflight.inspect(self.project,self.archive)
        self.assertEqual("unknown_project_content_requires_review",report["classification"])
        self.assertTrue(any("asmdef" in u["reason"] for u in report["unknowns"]))

    def test_original_asmdef_guid_reference_remains_detected(self):
        asset=self.project/"Assets/MyGame/Customer.asmdef"
        asset.write_text(json.dumps({
            "name":"Customer.Gameplay","references":["GUID:"+GUID_ASMDEF],
        }))
        report=preflight.inspect(self.project,self.archive)
        self.assertEqual("customer_dependencies_found",report["classification"])
        self.assertTrue(any(x["kind"]=="asmdef_reference" for x in report["dependencies"]))


if __name__=="__main__":unittest.main()
