"""Read-only HPR removal preflight must include embedded CUSTOMER UPM packages.

Unity treats project/Packages/com.mycompany.game as editable project source,
not only as a manifest/lock entry. Those customer scripts may use HPR APIs.
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
SPEC=importlib.util.spec_from_file_location("uninstall_embedded_package_test",SOURCE)
preflight=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preflight)

GUID_HPR_ASM="c42c4a8abb827303ed702e33a9ca1641"
GUID_HPR_CODE="b264fbccf54cda999a913fe5c4089240"

class EmbeddedLocalCustomerPackages(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="hpr_embedded_customer_")
        self.addCleanup(self.temp.cleanup)
        root=Path(self.temp.name)
        self.project=root/"buyer"
        (self.project/"Assets/MyGame").mkdir(parents=True)
        (self.project/"Assets/MyGame/Controller.cs").write_text("class ExistingController {}")
        (self.project/"Packages").mkdir()
        (self.project/"Packages/manifest.json").write_text('{"dependencies":{}}')
        (self.project/"Packages/packages-lock.json").write_text('{"dependencies":{}}')
        self.embedded=self.project/"Packages/com.customer.game/Runtime"
        self.embedded.mkdir(parents=True)
        self.archive=root/"hpr.unitypackage"
        with tarfile.open(self.archive,"w:gz") as tar:
            for guid,path in ((GUID_HPR_ASM,"Assets/HPRGameplaySuite/Modules/com.hpr.abilities/Runtime/HPR.Abilities.Runtime.asmdef"),
                              (GUID_HPR_CODE,"Assets/HPRGameplaySuite/Modules/com.hpr.abilities/Runtime/AbilityRunnerComponent.cs")):
                body=path.encode()
                member=tarfile.TarInfo(guid+"/pathname")
                member.size=len(body)
                tar.addfile(member,io.BytesIO(body))

    def test_embedded_customer_package_csharp_hpr_reference_detected(self):
        source=self.embedded/"AbilityClient.cs"
        source.write_text("using HPR;\npublic class AbilityClient { HPR.AbilityRunnerComponent runner; }\n")
        result=preflight.inspect(self.project,self.archive)
        self.assertEqual("customer_dependencies_found",result["classification"])
        self.assertTrue(any(x["kind"]=="csharp_hpr_reference" and
                            x["path"]=="Packages/com.customer.game/Runtime/AbilityClient.cs"
                            for x in result["dependencies"]))
        self.assertFalse(result["deletion_permitted"])

    def test_embedded_customer_package_asmref_by_guid_detected(self):
        (self.embedded/"CustomerAbility.asmref").write_text(json.dumps({
            "reference":"GUID:"+GUID_HPR_ASM,
        }))
        result=preflight.inspect(self.project,self.archive)
        self.assertEqual("customer_dependencies_found",result["classification"])
        self.assertTrue(any(x["kind"]=="asmref_reference" and
                            x["path"].startswith("Packages/com.customer.game/")
                            for x in result["dependencies"]))

    def test_embedded_customer_package_asmdef_by_name_detected(self):
        (self.embedded/"CustomerGame.asmdef").write_text(json.dumps({
            "name":"Customer.Gameplay","references":["HPR.Abilities.Runtime"]
        }))
        result=preflight.inspect(self.project,self.archive)
        self.assertTrue(any(x["kind"]=="asmdef_reference" for x in result["dependencies"]))

    def test_embedded_vendor_package_itself_is_not_a_self_blocker(self):
        own=self.project/"Packages/com.hpr.abilities/Runtime"
        own.mkdir(parents=True)
        (own/"MyOwnSource.cs").write_text("using HPR;\n")
        result=preflight.inspect(self.project,self.archive)
        self.assertEqual("no_direct_reference_detected",result["classification"])
        self.assertEqual([],result["dependencies"])

    def test_embedded_customer_package_json_transitive_hpr_dependency_detected(self):
        file=self.embedded.parent/"package.json"
        file.write_text(json.dumps({"name":"com.customer.game", "version":"1.0.0",
            "dependencies":{"com.hpr.abilities":"1.2.0"}}))
        report=preflight.inspect(self.project,self.archive)
        self.assertEqual("customer_dependencies_found",report["classification"])
        self.assertTrue(any(x["kind"]=="embedded_package_manifest_reference" and
                            x["path"]=="Packages/com.customer.game/package.json"
                            for x in report["dependencies"]))
        self.assertFalse(report["deletion_permitted"])

    def test_unrelated_embedded_package_json_has_no_false_hpr_dependency(self):
        file=self.embedded.parent/"package.json"
        file.write_text(json.dumps({"name":"com.customer.game", "version":"1.0.0",
            "dependencies":{"com.unity.inputsystem":"1.20.1"}}))
        report=preflight.inspect(self.project,self.archive)
        self.assertEqual("no_direct_reference_detected",report["classification"])

    def test_broken_embedded_package_json_is_unknown_not_safe(self):
        file=self.embedded.parent/"package.json"
        for content in ('{ bad json', '{"dependencies":[]}', '{"dependencies":null}'):
            file.write_text(content)
            with self.subTest(content=content):
                report=preflight.inspect(self.project,self.archive)
                self.assertEqual("unknown_project_content_requires_review",report["classification"])
                self.assertTrue(any("package manifest" in x["reason"] for x in report["unknowns"]))

    def test_embedded_package_symlink_escape_rejected(self):
        external=Path(self.temp.name)/"outside-secret.txt"
        external.write_text("do not read")
        (self.embedded/"Alias.cs").symlink_to(external)
        with self.assertRaises(ValueError):
            preflight.inspect(self.project,self.archive)
        self.assertEqual("do not read",external.read_text())

    def test_embedded_binary_file_fails_closed_unknown_not_safe(self):
        (self.embedded/"OnlyBinary.asset").write_bytes(b"\x00\x11binary")
        result=preflight.inspect(self.project,self.archive)
        self.assertEqual("unknown_project_content_requires_review",result["classification"])
        self.assertTrue(any(x["path"].startswith("Packages/com.customer.game/") for x in result["unknowns"]))

    def test_packages_entries_count_towards_total_traversal_budget(self):
        for i in range(7):
            (self.embedded/f"Module{i}.cs").write_text("class Noop {}")
        result=preflight.inspect(self.project,self.archive,max_scanned_paths=4)
        self.assertEqual("unknown_project_content_requires_review",result["classification"])
        self.assertTrue(any("traversal limit" in x["reason"] for x in result["unknowns"]))


if __name__=="__main__":unittest.main()
