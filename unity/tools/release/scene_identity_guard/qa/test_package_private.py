"""Exact package/rights boundary tests independent of the command-line product."""
from __future__ import annotations

from pathlib import Path
import importlib.util
import json
import tempfile
import unittest
import zipfile

QA = Path(__file__).resolve().parent
ROOT = QA.parent
spec = importlib.util.spec_from_file_location("hpr_packaging_guard", QA / "package_private.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class ExactPrivatePackageTest(unittest.TestCase):
    def test_original_package_inventory_is_only_buyer_source(self):
        with tempfile.TemporaryDirectory(prefix="scene-identity-zip-") as tmp:
            target=Path(tmp)/"PRIVATE_ONLY.zip"
            result=mod.package(target)
            self.assertEqual(result["status"],"PRIVATE_SOURCE_CLI_CANDIDATE_NOT_PUBLISHED")
            self.assertFalse(result["native_unity_editor_tested"])
            self.assertEqual(result["payloads"],4)
            with zipfile.ZipFile(target) as z:
                self.assertEqual(sorted(z.namelist()),sorted([
                    "HPRSceneIdentityGuard/"+n for n in
                    ("hpr_scene_identity.py","hpr_scene_identity_report.py","README.md","LICENSE.md","PRIVATE_MANIFEST.json")
                ]))
                manifest=json.loads(z.read("HPRSceneIdentityGuard/PRIVATE_MANIFEST.json"))
                self.assertEqual(manifest["tool_version"],"0.2.0")
                self.assertIn("PRIVATE",manifest["status"])
                self.assertIn("internal prerelease evaluation",manifest["rights"])
                for n in mod.PAYLOADS:
                    self.assertEqual(z.read("HPRSceneIdentityGuard/"+n),(ROOT/n).read_bytes())
            self.assertEqual(mod.verify(target)["archive_sha256"],result["archive_sha256"])
            with self.assertRaises(FileExistsError):
                mod.package(target)

    def test_payload_modification_without_manifest_update_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="scene-identity-zip-") as tmp:
            src=Path(tmp)/"PRIVATE_ONLY.zip"
            mod.package(src)
            tampered=Path(tmp)/"tampered.zip"
            with zipfile.ZipFile(src) as a,zipfile.ZipFile(tampered,"x") as b:
                for name in a.namelist():
                    contents=a.read(name)
                    if name.endswith("hpr_scene_identity_report.py"):
                        contents+=b"\n# unexpected modification\n"
                    b.writestr(name,contents)
            with self.assertRaisesRegex(ValueError,"Payload differs"):
                mod.verify(tampered)

    def test_unsafe_inventory_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="scene-identity-zip-") as tmp:
            src=Path(tmp)/"PRIVATE_ONLY.zip"
            mod.package(src)
            extra=Path(tmp)/"extra.zip"
            with zipfile.ZipFile(src) as a,zipfile.ZipFile(extra,"x") as b:
                for name in a.namelist():
                    b.writestr(name,a.read(name))
                b.writestr("../unwanted.txt","bad")
            with self.assertRaisesRegex(ValueError,"inventory"):
                mod.verify(extra)


if __name__=="__main__":
    unittest.main()
