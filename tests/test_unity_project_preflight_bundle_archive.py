"""Archive boundary regression: path normalization must not relax security.

Synthetic fixture is not a released package and is never sent to buyers.
"""
from pathlib import Path
import importlib.util
import io
import tarfile
from tempfile import TemporaryDirectory

BASE = Path(__file__).resolve().parents[1]
MOD = BASE/'unity/tools/release/preflight_bundle/qa/check_bundle_identity.py'
spec=importlib.util.spec_from_file_location('bundle_guard', MOD)
guard=importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def _fixture(tmp, prefix='./', invalid=False):
    tmp=Path(tmp)
    project=tmp/'project';project.mkdir()
    package=tmp/'vendor.unitypackage'
    with tarfile.open(package,'w:gz') as archive:
        for i, path in enumerate(sorted(guard.ALLOWED),1):
            guid=f'{i:032x}'
            file=project/path
            folder=path.endswith('/Editor') or path in {
                'Assets/HPRInputReadiness','Assets/HPRAnimatorContract','Assets/HPRProjectPreflight'}
            if folder: file.mkdir(parents=True,exist_ok=True);payload=None
            else:
                file.parent.mkdir(parents=True,exist_ok=True)
                payload=('original vendor asset: '+path).encode();file.write_bytes(payload)
            meta=f'fileFormatVersion: 2\nguid: {guid}\n'.encode()
            Path(str(file)+'.meta').write_bytes(meta)
            for part, data in [('pathname',path.encode()),('asset.meta',meta),('asset',payload)]:
                if data is None:continue
                entry=tarfile.TarInfo(prefix+guid+'/'+part)
                entry.size=len(data)
                archive.addfile(entry,io.BytesIO(data))
        if invalid:
            guid='f'*32
            data=b'../../../../outside/hidden.txt'
            entry=tarfile.TarInfo(prefix+guid+'/pathname')
            entry.size=len(data)
            archive.addfile(entry,io.BytesIO(data))
    return package,project


def test_unity6_older_plain_guid_package_format():
    with TemporaryDirectory() as temp:
        package,project=_fixture(temp,prefix='')
        result=guard.verify(package,project)
        assert result['status']=='PASS',result
        assert result['paths_verified']==12 and result['source_scripts_verified']==3


def test_unity2022_dot_prefixed_package_format():
    with TemporaryDirectory() as temp:
        package,project=_fixture(temp)
        result=guard.verify(package,project)
        assert result['status']=='PASS',result


def test_reject_archive_member_outside_vendor_roots():
    with TemporaryDirectory() as temp:
        package,project=_fixture(temp,invalid=True)
        result=guard.verify(package,project)
        assert result['status']=='FAIL'
        assert any('Unexpected asset pathname' in x for x in result['issues'])


def test_reject_tampered_buyer_file():
    with TemporaryDirectory() as temp:
        package,project=_fixture(temp)
        file=project/'Assets/HPRProjectPreflight/README.md'
        file.write_text('tampered')
        result=guard.verify(package,project)
        assert result['status']=='FAIL'
        assert any('Asset bytes differ' in x for x in result['issues'])


def test_reject_tampered_guid_metadata():
    with TemporaryDirectory() as temp:
        package,project=_fixture(temp)
        file=project/'Assets/HPRAnimatorContract/README.md.meta'
        file.write_text('guid: 00000000000000000000000000000000\n')
        result=guard.verify(package,project)
        assert result['status']=='FAIL'
        assert any('Meta bytes differ' in x for x in result['issues'])
