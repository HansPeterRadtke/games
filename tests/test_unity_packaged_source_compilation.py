"""Stage exact archive C# for offline, distinct-from-Editor API compilation.

All tests use synthetic local packages and fake API DLL placeholders;
these tests do not start a Unity Editor, C# compiler or actual import.
"""
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from xml.etree import ElementTree as ET

QA=Path(__file__).resolve().parents[1]/"unity/tools/release/gameplay_suite/qa"
sys.path.insert(0,str(QA))
import unity_packaged_source_compile as tool


class ExactUnitySourceCompilerStaging(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="hpr_csharp_archive_staging_")
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.archive=self.root/"frozen.unitypackage"
        self.out=self.root/"new-staged-output"
        self.editor=self.root/"Editors/6000.6.7f1/Editor"
        managed=self.editor/"Data/Managed/UnityEngine"
        managed.mkdir(parents=True)
        (managed/"UnityEngine.CoreModule.dll").write_bytes(b"fake managed DLL")
        (managed/"UnityEditor.CoreModule.dll").write_bytes(b"fake managed DLL")
        self.cs="Assets/HPRGameplaySuite/Editor/HprBuyerEditor.cs"
        with tarfile.open(self.archive,"w:gz") as tar:
            for guid,name,body in (("f"*32,"Assets/HPRGameplaySuite",None),
                                   ("a"*32,self.cs,b"namespace HPR { public class Check { } }")):
                parts=[("pathname",name.encode()),("asset.meta",("guid: "+guid+"\n").encode())]
                if body is not None:parts.append(("asset",body))
                for suffix,data in parts:
                    m=tarfile.TarInfo(guid+"/"+suffix);m.size=len(data)
                    tar.addfile(m,io.BytesIO(data))
        self.sha=hashlib.sha256(self.archive.read_bytes()).hexdigest()

    def stage(self,**kwargs):
        return tool.stage(self.archive,self.sha,self.editor,self.out,**kwargs)

    def test_preserves_real_archive_source_bytes_and_writes_exact_manifest(self):
        result=self.stage()
        self.assertEqual("PASS",result["status"])
        self.assertEqual(1,result["source_file_count"])
        self.assertEqual("private_offline_api_only_not_unity_editor",result["verification_level"])
        self.assertEqual(b"namespace HPR { public class Check { } }",
                         (self.out/"sources"/self.cs).read_bytes())
        project=ET.parse(self.out/"hpr-package-compile.csproj")
        self.assertIn("UNITY_6000_6_OR_NEWER",
                      project.find("./PropertyGroup/DefineConstants").text)
        self.assertEqual(1,len(project.findall("./ItemGroup/Compile")))
        self.assertEqual(self.sha,json.loads((self.out/"SOURCE_MANIFEST.json").read_text())["archive_sha256"])
        self.assertFalse(result["actual_unity_editor_executed"])

    def test_wrong_digest_refused_without_output(self):
        with self.assertRaises(ValueError):
            tool.stage(self.archive,"0"*64,self.editor,self.out)
        self.assertFalse(self.out.exists())

    def test_existing_output_refused_even_when_archive_matches(self):
        self.stage()
        with self.assertRaises(FileExistsError):self.stage()

    def test_input_branch_requires_explicit_existing_dll(self):
        with self.assertRaises(ValueError):
            self.stage(new_input=True)
        self.assertFalse(self.out.exists())
        inp=self.root/"Unity.InputSystem.dll"
        inp.write_bytes(b"local fake input dll")
        result=self.stage(new_input=True,inputsystem_dll=inp)
        self.assertTrue(result["new_input_system_branch"])
        props=ET.parse(self.out/"hpr-package-compile.csproj").find('./PropertyGroup')
        self.assertIn("ENABLE_INPUT_SYSTEM",props.find('DefineConstants').text)

    def test_existing_original_archive_and_source_remain_unchanged(self):
        before=self.archive.read_bytes()
        self.stage()
        self.assertEqual(before,self.archive.read_bytes())
        self.assertNotIn("Assets/HPRGameplaySuite/Tests",str(self.out))

    def test_stage_refuses_output_inside_installed_editor_folder(self):
        with self.assertRaises(ValueError):
            tool.stage(self.archive,self.sha,self.editor,self.editor/"new-qa-output")


if __name__=='__main__':unittest.main()
