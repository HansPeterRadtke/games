"""Build Unity's actual assembly-definition boundaries from the QA package.

The previous offline C# check compiled 55 scripts into ONE assembly and
could miss internal/public and missing assembly-reference errors.
This module only tests staging and explicit compile graph; native Unity
Editor compilation remains a separate release gate.
"""
import hashlib
import io
import json
import shutil
import tarfile
import sys
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
QA=ROOT/"unity/tools/release/gameplay_suite/qa"
sys.path.insert(0,str(QA))
import unity_exact_asmdef_compiler as split

ARCHIVE=Path("/data/var/marketplace-account-setup/hpr-unity-copy-race-reviewed-private-archive-20261102/internal-not-tested-in-unity.unitypackage")
STAGED=Path("/data/tmp/hpr-exact-reviewed-package-api-6000-6-20261102")
EDITOR=Path("/data/apps/Unity/Hub/Editor/6000.6.7f1/Editor")
PIN="1140e9bf5c7a9848003ce0ccd8168c298ced2bf957194364f9f08b3f52974f5e"


class ModuleBoundaries(unittest.TestCase):
    def test_dag_toposort_rejects_unknown_and_cycle(self):
        order=split.topological_assembly_order({"HPR.A":["HPR.B"],"HPR.B":[]})
        self.assertEqual(["HPR.B","HPR.A"],order)
        with self.assertRaisesRegex(ValueError,"missing"):
            split.topological_assembly_order({"HPR.A":["HPR.Missing"]})
        with self.assertRaisesRegex(ValueError,"cyclic"):
            split.topological_assembly_order({"HPR.A":["HPR.B"],"HPR.B":["HPR.A"]})

    def test_real_vendor_source_partition_is_explicit(self):
        if not ARCHIVE.exists() or not STAGED.is_dir():self.skipTest("private source absent")
        plan=split.plan(ARCHIVE,PIN,STAGED)
        self.assertEqual(10,len(plan["runtime"]))
        self.assertEqual(47,sum(len(v["sources"]) for v in plan["runtime"].values()))
        self.assertEqual(5,len(plan["integration_sources"]))
        self.assertEqual(3,len(plan["editor_sources"]))
        self.assertEqual(55,plan["source_count"])
        self.assertEqual(55,len(set(
            src for info in plan["runtime"].values() for src in info["sources"]
        ) | set(plan["integration_sources"]) | set(plan["editor_sources"])))
        self.assertEqual(["HPR.Eventbus.Runtime","HPR.Stats.Runtime"],
                         plan["runtime"]["HPR.Abilities.Runtime"]["references"])

    def test_runtime_module_projects_reference_only_declared_asmdef_modules(self):
        if not ARCHIVE.exists() or not STAGED.is_dir():self.skipTest("private source absent")
        with tempfile.TemporaryDirectory(prefix="hpr_asmdef_project_") as td:
            dest=Path(td)/"project"
            record=split.stage(ARCHIVE,PIN,STAGED,EDITOR,dest)
            self.assertEqual("PASS",record["status"])
            self.assertEqual(12,record["projects_created"])
            self.assertEqual(55,record["scripts_included_once"])
            for name,declared in record["runtime_asmdefs"].items():
                csproj=ET.parse(dest/"projects"/(name+".csproj"))
                refs=sorted(x.get("Include") for x in csproj.findall("./ItemGroup/ProjectReference"))
                self.assertEqual(sorted(str((dest/"projects"/(dep+".csproj"))) for dep in declared["references"]),refs)
                libs=[r.get("Include") for r in csproj.findall("./ItemGroup/Reference")]
                self.assertTrue(any(x.startswith("UnityEngine.") for x in libs))
                self.assertFalse(any(x.startswith("UnityEditor.") for x in libs))
            code=ET.parse(dest/"projects/Assembly-CSharp.csproj")
            scripts=code.findall("./ItemGroup/Compile")
            self.assertEqual(5,len(scripts))
            editor=ET.parse(dest/"projects/Assembly-CSharp-Editor.csproj")
            self.assertEqual(3,len(editor.findall("./ItemGroup/Compile")))
            self.assertTrue(any(x.get("Include")=="UnityEditor.CoreModule" for x in editor.findall("./ItemGroup/Reference")))
            self.assertFalse(record["actual_unity_editor_compilation_completed"])

    def test_create_only_and_source_hash_immutable(self):
        if not ARCHIVE.exists() or not STAGED.is_dir():self.skipTest("private source absent")
        with tempfile.TemporaryDirectory(prefix="hpr_asmdef_immutable_") as td:
            archive_hash=hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
            dest=Path(td)/"project"
            split.stage(ARCHIVE,PIN,STAGED,EDITOR,dest)
            with self.assertRaises(FileExistsError):
                split.stage(ARCHIVE,PIN,STAGED,EDITOR,dest)
            self.assertEqual(archive_hash,hashlib.sha256(ARCHIVE.read_bytes()).hexdigest())

    def test_manifest_does_not_accept_customer_modified_staged_csharp(self):
        if not ARCHIVE.exists() or not STAGED.is_dir():self.skipTest("source absent")
        with tempfile.TemporaryDirectory(prefix="hpr_exact_csharp_mutation_") as td:
            root=Path(td)
            stage=root/"copied-input"
            stage.mkdir()
            shutil.copytree(STAGED/"sources",stage/"sources")
            shutil.copy2(STAGED/"SOURCE_MANIFEST.json",stage/"SOURCE_MANIFEST.json")
            source=stage/"sources/Assets/HPRGameplaySuite/Integration/HprSuiteIntegration.cs"
            source.write_bytes(source.read_bytes() + b"// foreign customer source edit\n")
            with self.assertRaisesRegex(ValueError,"changed after original package"):
                split.stage(ARCHIVE,PIN,stage,EDITOR,root/"refused-output")
            self.assertFalse((root/"refused-output").exists())
            self.assertEqual(PIN,hashlib.sha256(ARCHIVE.read_bytes()).hexdigest())

    def test_symlinked_staged_csharp_rejected_before_output(self):
        if not ARCHIVE.exists() or not STAGED.is_dir():self.skipTest("source absent")
        with tempfile.TemporaryDirectory(prefix="hpr_exact_csharp_symlink_") as td:
            root=Path(td)
            stage=root/"copied-input"
            stage.mkdir()
            shutil.copytree(STAGED/"sources",stage/"sources")
            shutil.copy2(STAGED/"SOURCE_MANIFEST.json",stage/"SOURCE_MANIFEST.json")
            source=stage/"sources/Assets/HPRGameplaySuite/Integration/HprSuiteIntegration.cs"
            original=source.read_bytes()
            source.unlink()
            target=root/"outside-customer-source.cs"
            target.write_bytes(original)
            source.symlink_to(target)
            with self.assertRaisesRegex(ValueError,"missing or symlinked"):
                split.stage(ARCHIVE,PIN,stage,EDITOR,root/"refused-output")
            self.assertEqual(original,target.read_bytes())
            self.assertFalse((root/"refused-output").exists())

    def test_player_boundary_excludes_editor_assembly_and_editor_only_symbols(self):
        if not ARCHIVE.exists() or not STAGED.is_dir():self.skipTest("private source absent")
        with tempfile.TemporaryDirectory(prefix="hpr_asmdef_player_") as td:
            destination=Path(td)/"player-only"
            result=split.stage(ARCHIVE,PIN,STAGED,EDITOR,destination,player=True)
            self.assertEqual(11,result["projects_created"])
            self.assertEqual(52,result["scripts_included_once"])
            self.assertEqual(3,result["editor_sources_excluded"])
            self.assertFalse((destination/"projects/Assembly-CSharp-Editor.csproj").exists())
            for path in (destination/"projects").glob("*.csproj"):
                doc=ET.parse(path)
                self.assertNotIn("UNITY_EDITOR",doc.find("./PropertyGroup/DefineConstants").text)
                references=[x.get("Include") for x in doc.findall("./ItemGroup/Reference")]
                self.assertFalse(any(x.startswith("UnityEditor.") for x in references))

    def test_legacy_input_compiles_the_real_input_manager_branch(self):
        if not ARCHIVE.exists() or not STAGED.is_dir():self.skipTest("private source absent")
        with tempfile.TemporaryDirectory(prefix="hpr_asmdef_legacy_real_branch_") as td:
            dest=Path(td)/"legacy-player"
            result=split.stage(ARCHIVE,PIN,STAGED,EDITOR,dest,
                               player=True,legacy_input=True)
            self.assertEqual("legacy",result["input_mode"])
            self.assertFalse(result["new_input"])
            symbols=ET.parse(dest/"projects/Assembly-CSharp.csproj").find(
                "./PropertyGroup/DefineConstants").text
            self.assertIn("ENABLE_LEGACY_INPUT_MANAGER",symbols)
            self.assertNotIn("ENABLE_INPUT_SYSTEM",symbols)
            self.assertFalse((dest/"projects/Assembly-CSharp-Editor.csproj").exists())

    def test_no_input_fallback_cannot_be_reported_as_old_input(self):
        if not ARCHIVE.exists() or not STAGED.is_dir():self.skipTest("private source absent")
        with tempfile.TemporaryDirectory(prefix="hpr_asmdef_noinput_truth_") as td:
            record=split.stage(ARCHIVE,PIN,STAGED,EDITOR,Path(td)/"no-input")
            self.assertEqual("disabled_fallback",record["input_mode"])
            self.assertFalse(record["legacy_input_branch_compiled"])

    def test_player_new_only_input_references_package_inputsystem(self):
        if not ARCHIVE.exists() or not STAGED.is_dir():self.skipTest("private source absent")
        with tempfile.TemporaryDirectory(prefix="hpr_asmdef_player_modern_") as td:
            root=Path(td)
            input_dll=root/"Unity.InputSystem.dll"
            input_dll.write_bytes(b"synthetic input library for staging test")
            dest=root/"player"
            report=split.stage(ARCHIVE,PIN,STAGED,EDITOR,dest,
                               player=True,new_input=True,input_dll=input_dll)
            self.assertTrue(report["player_build"])
            integration=ET.parse(dest/"projects/Assembly-CSharp.csproj")
            self.assertIn("ENABLE_INPUT_SYSTEM",integration.find("./PropertyGroup/DefineConstants").text)
            self.assertIn("Unity.InputSystem",[x.get("Include") for x in integration.findall("./ItemGroup/Reference")])
            for name in report["runtime_asmdefs"]:
                doc=ET.parse(dest/"projects"/(name+".csproj"))
                self.assertFalse(any(x.get("Include")=="Unity.InputSystem"
                                     for x in doc.findall("./ItemGroup/Reference")))

    def test_unsupported_asmdef_compiler_options_fail_closed(self):
        if not ARCHIVE.is_file() or not STAGED.is_dir():self.skipTest("private sources absent")
        with tempfile.TemporaryDirectory(prefix="hpr_asmdef_unsupported_flags_") as td:
            root=Path(td)
            stage=root/"copied-input"
            stage.mkdir()
            shutil.copytree(STAGED/"sources",stage/"sources")
            shutil.copy2(STAGED/"SOURCE_MANIFEST.json",stage/"SOURCE_MANIFEST.json")
            data=[]
            with tarfile.open(ARCHIVE,"r:gz") as previous:
                entries={m.name:previous.extractfile(m).read() for m in previous if m.isfile()}
            target_guid=None
            for member,body in entries.items():
                if member.endswith("/pathname") and body.decode().strip().endswith(
                        "HPR.Abilities.Runtime.asmdef"):
                    target_guid=member.split("/",1)[0]
            self.assertIsNotNone(target_guid)
            original=json.loads(entries[target_guid+"/asset"])
            for key,value in (("noEngineReferences",True),("overrideReferences",True),
                              ("allowUnsafeCode",True),("versionDefines",[{"name":"foo"}])):
                with self.subTest(asmdef_option=key):
                    altered=dict(original)
                    altered[key]=value
                    entries[target_guid+"/asset"]=json.dumps(altered).encode()
                    changed=root/(key+".unitypackage")
                    with tarfile.open(changed,"w:gz") as tf:
                        for name,body in entries.items():
                            entry=tarfile.TarInfo(name)
                            entry.size=len(body)
                            tf.addfile(entry,io.BytesIO(body))
                    actual=hashlib.sha256(changed.read_bytes()).hexdigest()
                    manifest=json.loads((stage/"SOURCE_MANIFEST.json").read_text())
                    manifest["archive_sha256"]=actual
                    (stage/"SOURCE_MANIFEST.json").write_text(json.dumps(manifest))
                    with self.assertRaisesRegex(ValueError,"unsupported.*asmdef"):
                        split.plan(changed,actual,stage)

    def test_new_input_branch_requires_explicit_dll_and_only_integration_refs_it(self):
        if not ARCHIVE.exists() or not STAGED.is_dir():self.skipTest("private source absent")
        with tempfile.TemporaryDirectory(prefix="hpr_asmdef_input_") as td:
            root=Path(td)
            with self.assertRaises(ValueError):
                split.stage(ARCHIVE,PIN,STAGED,EDITOR,root/"invalid",new_input=True)
            input_dll=root/"Unity.InputSystem.dll"
            input_dll.write_bytes(b"synthetic InputSystem.dll no actual Unity execution")
            record=split.stage(ARCHIVE,PIN,STAGED,EDITOR,root/"valid",
                               new_input=True,input_dll=input_dll)
            self.assertTrue(record["new_input"])
            integration=ET.parse(root/"valid/projects/Assembly-CSharp.csproj")
            defs=integration.find("./PropertyGroup/DefineConstants").text
            self.assertIn("ENABLE_INPUT_SYSTEM",defs)
            self.assertIn("Unity.InputSystem",[x.get("Include") for x in integration.findall("./ItemGroup/Reference")])


if __name__=="__main__":unittest.main()
