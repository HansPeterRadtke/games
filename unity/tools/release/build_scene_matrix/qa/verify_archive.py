"""Validate exact first-party native export and prevent QA leakage."""
from pathlib import Path
import hashlib,json,re,sys,tarfile
def inspect(archive,source):
    base=Path(source)
    expected={"Assets/"+f.relative_to(base).as_posix():f for f in base.rglob("*") if not f.name.endswith(".meta")}
    assert len(expected)==5,expected
    blobs={}
    with tarfile.open(archive,"r:gz") as t:
        for m in t.getmembers():
            name=m.name.removeprefix("./")
            if m.isdir():
                assert re.fullmatch(r"[0-9a-f]{32}/?",name) or name in ("",".")
                continue
            assert m.isfile() and m.size<3_000_000 and re.fullmatch(r"[0-9a-f]{32}/(pathname|asset|asset.meta)",name)
            assert name not in blobs
            blobs[name]=t.extractfile(m).read()
    observed={}
    for k,v in blobs.items():
        if not k.endswith("/pathname"):continue
        guid=k.split("/")[0]
        path=v.decode().strip()
        assert path in expected and path not in observed,path
        f=expected[path]
        meta=Path(str(f)+".meta").read_bytes()
        assert re.search(rb"(?m)^guid:\s*"+guid.encode()+rb"\s*$",meta)
        # Unity can canonicalize trailing whitespace in importer metadata.
        actual=blobs[guid+"/asset.meta"]
        assert re.search(rb"(?m)^guid:\s*"+guid.encode()+rb"\s*$",actual)
        if f.is_file():assert blobs[guid+"/asset"]==f.read_bytes(),path
        else:assert blobs.get(guid+"/asset") in (None,b"")
        observed[path]=guid
    assert set(observed)==set(expected) and len(set(observed.values()))==len(expected)
    assert all(k.split("/")[0] in observed.values() for k in blobs)
    return {"result":"PASS","sha256":hashlib.sha256(Path(archive).read_bytes()).hexdigest(),
            "paths":observed,"exact_authored_payloads":True,"guid_identity":True,"no_qa_assets":True}
if __name__=="__main__":print(json.dumps(inspect(*sys.argv[1:]),indent=2))
