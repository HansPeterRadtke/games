"""Cold private ZIP inspection and actual example-command acceptance."""
from pathlib import Path
import hashlib
import json
import stat
import subprocess
import sys
import zipfile

EXPECTED={
    "HprSceneGate.dll","HprSceneGate.deps.json","HprSceneGate.runtimeconfig.json",
    "README.md","LICENSE.md","examples/approved.hpr-scenes",
    "examples/same.hpr-scenes","examples/renamed.hpr-scenes","PRIVATE_MANIFEST.json",
}

def verify(archive, destination):
    archive,destination=Path(archive).resolve(),Path(destination).resolve()
    if destination.exists():raise FileExistsError(destination)
    def require(ok,message):
        if not ok:raise ValueError(message)
    digest=lambda b:hashlib.sha256(b).hexdigest()
    original_hash=digest(archive.read_bytes())
    with zipfile.ZipFile(archive) as z:
        infos=z.infolist()
        require(len(infos)==len(EXPECTED) and {i.filename for i in infos}==EXPECTED,
                "Unexpected ZIP inventory")
        require(sum(i.file_size for i in infos)<1_000_000,"Unexpected expanded package size")
        require(all(stat.S_ISREG(i.external_attr>>16) for i in infos),"Non-file ZIP member")
        manifest=json.loads(z.read("PRIVATE_MANIFEST.json"))
        require(manifest["status"]=="PRIVATE_COMPANION_CANDIDATE_NOT_PUBLISHED" and
                not manifest["runtime_included"] and not manifest["native_unity_editor_invoked"],
                "Incorrect private delivery boundary")
        require(set(manifest["files"])==EXPECTED-{"PRIVATE_MANIFEST.json"},
                "Manifest is not an exact payload inventory")
        for name,meta in manifest["files"].items():
            blob=z.read(name)
            require(len(blob)==meta["bytes"] and digest(blob)==meta["sha256"],"Payload identity mismatch")
        destination.mkdir()
        # Only a fixed, known, regular-file allowlist can be extracted.
        for i in infos:
            target=destination/i.filename
            target.parent.mkdir(parents=True,exist_ok=True)
            with target.open("xb") as out:out.write(z.read(i))
    dll=destination/"HprSceneGate.dll"
    def cmd(*args):
        return subprocess.run(["dotnet",str(dll),*map(str,args)],capture_output=True,text=True,
                              timeout=20,cwd=destination)
    version=cmd("--version")
    require(version.returncode==0 and version.stdout.strip()==manifest["version"] and not version.stderr,
            "Cold package version does not match")
    same=cmd("compare","examples/approved.hpr-scenes","examples/same.hpr-scenes")
    changed=cmd("compare","examples/approved.hpr-scenes","examples/renamed.hpr-scenes")
    a,b=json.loads(same.stdout),json.loads(changed.stdout)
    require(same.returncode==0 and a["status"]=="MATCH_WITHOUT_WARNINGS" and not same.stderr,
            "Cold matching example did not pass")
    require(changed.returncode==1 and b["changed_scene_identities"]==1 and not changed.stderr,
            "Cold changed example did not request review")
    require(digest(archive.read_bytes())==original_hash,"Original ZIP changed")
    require(all(digest((destination/name).read_bytes())==meta["sha256"]
                for name,meta in manifest["files"].items()),"Extracted package mutated during run")
    result={"status":"COLD_EXTRACTED_COMPANION_PASS","archive_sha256":original_hash,
            "source_revision":manifest["source_revision"],"manifest_payloads_verified":len(manifest["files"]),
            "version":version.stdout.strip(),"same_example_exit":same.returncode,"renamed_example_exit":changed.returncode,
            "match":a,"changed":b,"native_unity_editor_invoked":False}
    print(json.dumps(result,indent=2))

if __name__=="__main__":verify(*sys.argv[1:])
