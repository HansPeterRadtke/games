"""Review-only integration of tested private Unity code into the owner's dirty tree.

Never apply a patch to the owner's worktree in this test. A fresh temporary
copy of the two source files is patched, byte-compared against the exact
already-verified 161-asset internal HPR buyer candidate, and discarded.
"""
import hashlib
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
OWNER=Path("/data/src/worktrees/unity-integrated-suite-20261030")
REVIEWED=Path("/data/var/marketplace-account-setup/hpr-unity-copy-race-guard-reviewed-20261102/source/unity/tools/release/gameplay_suite")
PACKAGE=Path("/data/var/marketplace-account-setup/hpr-unity-copy-race-reviewed-private-archive-20261102/internal-not-tested-in-unity.unitypackage")
PATCH=ROOT/"doc/unity-product-research-2026-10-31/patches/hpr-owner-uncommitted-two-file-safe-copy-2026-11-03.patch"
FILES=("HprSuiteIntegrationGuide.cs","HprGameplaySuiteSceneBuilder.cs")
REL=Path("unity/tools/release/gameplay_suite")


class OwnerDevelopmentFileIntegration(unittest.TestCase):
    def setUp(self):
        self.base=OWNER/REL
        if not PATCH.is_file() or not all((self.base/x).is_file() and (REVIEWED/x).is_file() for x in FILES):
            self.skipTest("Owner source snapshot/approved candidate not mounted")
        self.tmp=tempfile.TemporaryDirectory(prefix="hpr_owner_integration_patch_")
        self.addCleanup(self.tmp.cleanup)
        self.copy=Path(self.tmp.name)
        for name in FILES:
            dest=self.copy/REL/name
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(self.base/name,dest)
        self.before={n:hashlib.sha256((self.base/n).read_bytes()).hexdigest() for n in FILES}

    def test_only_two_existing_hpr_code_paths_are_in_patch(self):
        data=PATCH.read_text()
        old=[line[len("--- a/"):] for line in data.splitlines() if line.startswith("--- a/")]
        new=[line[len("+++ b/"):] for line in data.splitlines() if line.startswith("+++ b/")]
        expected={str(REL/name) for name in FILES}
        self.assertEqual(expected,set(old))
        self.assertEqual(expected,set(new))
        self.assertNotIn(".meta",data[:100])

    def test_patch_current_owner_snapshot_only_checks_never_modifies_it(self):
        r=subprocess.run(["git","-C",str(OWNER),"apply","--check",str(PATCH)],
                         capture_output=True,text=True,timeout=15)
        self.assertEqual(0,r.returncode,r.stderr)
        for name in FILES:
            self.assertEqual(self.before[name],
                             hashlib.sha256((self.base/name).read_bytes()).hexdigest())

    def test_apply_to_private_copy_matches_compiled_archive_source_exactly(self):
        r=subprocess.run(["git","apply","--check",str(PATCH)],
                         cwd=self.copy,capture_output=True,text=True,timeout=10)
        self.assertEqual(0,r.returncode,r.stderr)
        r=subprocess.run(["git","apply",str(PATCH)],
                         cwd=self.copy,capture_output=True,text=True,timeout=10)
        self.assertEqual(0,r.returncode,r.stderr)
        for name in FILES:
            self.assertEqual((REVIEWED/name).read_bytes(),
                             (self.copy/REL/name).read_bytes())
            self.assertEqual(self.before[name],
                             hashlib.sha256((self.base/name).read_bytes()).hexdigest())

    def test_exact_reviewed_archive_has_these_same_two_compiled_source_bytes(self):
        if not PACKAGE.is_file():
            self.skipTest("Actual source-verified Unity private archive unavailable")
        by_guid={}
        with tarfile.open(PACKAGE,"r:gz") as archive:
            for item in archive:
                if item.isfile():
                    by_guid[item.name]=archive.extractfile(item).read()
        for name in FILES:
            target="Assets/HPRGameplaySuite/Editor/"+name
            folders=[path.split("/")[0] for path,raw in by_guid.items()
                     if path.endswith("/pathname") and raw.decode().strip()==target]
            self.assertEqual(1,len(folders))
            self.assertEqual((REVIEWED/name).read_bytes(),by_guid[folders[0]+"/asset"])

    def test_reviewed_owner_targets_match_three_prior_real_offline_api_compilers(self):
        previous=Path("/data/tmp")
        for mode in ("6000-4","6000-6","6000-6-newinput"):
            folder=previous/("hpr-exact-reviewed-package-api-"+mode+"-20261102")
            if not (folder/"SOURCE_MANIFEST.json").is_file():
                self.skipTest("Previous source-controlled offline C# evidence not mounted")
            import json
            manifest=json.loads((folder/"SOURCE_MANIFEST.json").read_text())
            log=(folder/"build.log").read_text()
            self.assertEqual(55,manifest["source_file_count"])
            self.assertIn("Build succeeded.",log)
            self.assertIn("0 Error(s)",log)
            for name in FILES:
                archive_rel="Assets/HPRGameplaySuite/Editor/"+name
                self.assertEqual(hashlib.sha256((REVIEWED/name).read_bytes()).hexdigest(),
                                 manifest["source_file_sha256"][archive_rel])

    def test_recovered_owner_copy_has_no_global_save_or_deletion(self):
        subprocess.run(["git","apply",str(PATCH)],cwd=self.copy,
                       check=True,capture_output=True,text=True,timeout=10)
        guide=(self.copy/REL/FILES[0]).read_text()
        builder=(self.copy/REL/FILES[1]).read_text()
        self.assertNotIn("AssetDatabase.SaveAssets();",guide)
        self.assertNotIn("AssetDatabase.DeleteAsset(",guide)
        self.assertNotIn("AssetDatabase.SaveAssets();",builder)
        self.assertIn("AssetDatabase.SaveAssetIfDirty(copy);",guide)
        self.assertIn("AssetDatabase.SaveAssetIfDirty(material);",builder)
        self.assertIn("The last attempted output may also exist:",guide)


if __name__=="__main__":unittest.main()
