"""Private CLI archive boundaries; no Unity application or downloads."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

from test_asmdef_preflight import mod, ROOT

class PackagingContract(unittest.TestCase):
    def test_source_tree_has_no_third_party_runtime(self):
        source=(ROOT/'hpr_asmdef_preflight.py').read_text()
        self.assertNotIn('import requests',source)
        self.assertNotIn('import urllib',source)
        self.assertNotIn('subprocess.run',source)
        self.assertNotIn('shutil.rmtree',source)
        self.assertFalse((ROOT/'Assets').exists(), 'CLI must not pose as a Unity Editor package')
        for name in ('LICENSE.md','ThirdPartyNotices.md','README.md'):
            self.assertTrue((ROOT/name).is_file())

    def test_exact_ship_set_excludes_original_private_test_data(self):
        import importlib.util
        spec=importlib.util.spec_from_file_location('hpr_zip',ROOT/'qa/package_private.py')
        p=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(p)
        self.assertEqual(p.SHIP,('hpr_asmdef_preflight.py','README.md','LICENSE.md','ThirdPartyNotices.md'))
        self.assertNotIn('qa/',str(p.SHIP))

if __name__=='__main__':unittest.main()
