"""Fresh private negative .unitypackage fixtures created from real old archive.

No user customer source or existing archive is edited. GZIP/TAR structures
are newly created to exercise the production C# reader's fail-closed checks.
"""
from pathlib import Path
import hashlib
import io
import tarfile

ROOT=Path('/data/var/marketplace-account-setup/unity-20261121-wave50')
ORIGINAL=Path('/data/var/marketplace-account-setup/unity-20261121-afternoon/native-2022-3-22f1-cleanmeta1/hpr-package-boundary-candidate.unitypackage')
OLD_GUID='557232cca8304776933adae163dca28b'
NEW_GUID='ffffffffffffffffffffffffffffffff'

def create(folder:Path):
    if folder.exists():raise RuntimeError('Refusing to replace any existing private negative fixtures')
    folder.mkdir(parents=True)
    raw=ORIGINAL.read_bytes()
    original_sha=hashlib.sha256(raw).hexdigest()
    with tarfile.open(ORIGINAL,'r:gz') as file:
        items=[]
        for member in file:
            if member.isfile():
                stream=file.extractfile(member)
                if stream is None:raise RuntimeError('Unreadable original member')
                items.append((member,stream.read()))
            else:items.append((member,None))
    for purpose in ('bad_meta','guid_changed','path_traversal','symlink'):
        path=folder/f'{purpose}.unitypackage'
        with tarfile.open(path,'w:gz') as out:
            for member,data in items:
                # Copy the TAR entry description but never reuse an object
                # that another negative fixture already modified.
                new=tarfile.TarInfo(member.name)
                new.type=member.type;new.mode=member.mode;new.uid=member.uid;new.gid=member.gid
                new.mtime=0;new.uname=member.uname;new.gname=member.gname
                if purpose=='guid_changed' and OLD_GUID in new.name:
                    new.name=new.name.replace(OLD_GUID,NEW_GUID)
                    if new.name.endswith('/asset.meta'):
                        data=data.replace(OLD_GUID.encode(),NEW_GUID.encode())
                elif purpose=='bad_meta' and member.name.endswith(OLD_GUID+'/asset.meta'):
                    data=data.replace(OLD_GUID.encode(),NEW_GUID.encode())
                elif purpose=='path_traversal' and member.name.endswith(OLD_GUID+'/pathname'):
                    data=b'Assets/../ExampleAsset/README.md'
                if data is None:new.size=0;out.addfile(new)
                else:new.size=len(data);out.addfile(new,io.BytesIO(data))
            if purpose=='symlink':
                fake=tarfile.TarInfo('./bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb/asset')
                fake.type=tarfile.SYMTYPE;fake.linkname='../../unsafe';fake.mode=0o777
                out.addfile(fake)
        if path.stat().st_size<100:raise RuntimeError('Could not write negative archive')
    truncated=folder/'truncated.unitypackage'
    truncated.write_bytes(raw[:-30])
    assert hashlib.sha256(ORIGINAL.read_bytes()).hexdigest()==original_sha
    print('NEGATIVE_ARCHIVES_CREATED',len(list(folder.glob('*.unitypackage'))),
          'ORIGINAL_UNTOUCHED_SHA256',original_sha)

if __name__=='__main__':
    create(ROOT/'negative-archive-fixtures')
