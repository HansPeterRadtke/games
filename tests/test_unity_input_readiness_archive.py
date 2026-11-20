"""Independent byte-level package guard fixtures for a newly created Unity product."""
import importlib.util
import io
from pathlib import Path
import tarfile
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'unity/tools/release/input_readiness_audit/qa/check_package_identity.py'
spec = importlib.util.spec_from_file_location('hpr_input_archive_guard', SOURCE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class InputAuditPackageIdentityTests(unittest.TestCase):
    def fixture(self, base, *, alter=None):
        project = base / 'project'
        project.mkdir()
        package = base / 'product.unitypackage'
        paths = {
            'Assets/HPRInputReadiness': None,
            'Assets/HPRInputReadiness/Editor': None,
            'Assets/HPRInputReadiness/README.md': b'Buyer instructions',
            'Assets/HPRInputReadiness/Editor/HprInputReadinessAudit.cs': b'// trusted test source',
        }
        with tarfile.open(package, 'w:gz') as out:
            for i, (name, data) in enumerate(paths.items(), 1):
                guid = f'{i:032x}'
                p = project / name
                if data is None: p.mkdir(parents=True, exist_ok=True)
                else:
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_bytes(data)
                meta = f'fileFormatVersion: 2\nguid: {guid}\n'.encode()
                Path(str(p) + '.meta').write_bytes(meta)
                for part, content in [('pathname', name.encode()), ('asset.meta', meta)]:
                    m = tarfile.TarInfo(guid + '/' + part)
                    m.size = len(content)
                    out.addfile(m, io.BytesIO(content))
                if data is not None:
                    m = tarfile.TarInfo(guid + '/asset');m.size = len(data)
                    out.addfile(m, io.BytesIO(data))
        if alter == 'file': (project / 'Assets/HPRInputReadiness/README.md').write_text('modified')
        if alter == 'guid': Path(str(project / 'Assets/HPRInputReadiness/README.md') + '.meta').write_text('guid: abcd\n')
        return package, project

    def test_exact_archive_and_import(self):
        with TemporaryDirectory() as tmp:
            a, p = self.fixture(Path(tmp))
            self.assertEqual(mod.check(a, p)['status'], 'PASS')

    def test_changed_customer_asset_fails(self):
        with TemporaryDirectory() as tmp:
            a, p = self.fixture(Path(tmp), alter='file')
            self.assertEqual(mod.check(a, p)['status'], 'FAIL')

    def test_changed_imported_meta_fails(self):
        with TemporaryDirectory() as tmp:
            a, p = self.fixture(Path(tmp), alter='guid')
            self.assertEqual(mod.check(a, p)['status'], 'FAIL')

    def test_unknown_archive_root_fails(self):
        with TemporaryDirectory() as tmp:
            a, p = self.fixture(Path(tmp))
            bad = Path(tmp) / 'unexpected.unitypackage'
            with tarfile.open(a, 'r:gz') as src, tarfile.open(bad, 'w:gz') as out:
                for m in src:
                    out.addfile(m, src.extractfile(m) if m.isfile() else None)
                payload = b'Assets/OtherVendor/Unwanted.cs'
                m = tarfile.TarInfo('f' * 32 + '/pathname')
                m.size = len(payload)
                out.addfile(m, io.BytesIO(payload))
            result = mod.check(bad, p)
            self.assertEqual(result['status'], 'FAIL')
            self.assertTrue(any('outside' in err for err in result['issues']), result)


if __name__ == '__main__':
    unittest.main()
