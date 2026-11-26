#!/usr/bin/env python3
"""Build and independently inspect a create-only PRIVATE Scene Identity Guard ZIP.

No Unity Editor process, marketplace upload, license acceptance, or external effect.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import stat
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TOP = "HPRSceneIdentityGuard"
PAYLOADS = ("hpr_scene_identity.py", "README.md", "LICENSE.md")
MANIFEST = TOP + "/PRIVATE_MANIFEST.json"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def package(new_zip: Path) -> dict:
    if new_zip.exists() or new_zip.is_symlink():
        raise FileExistsError("Create-only private archive already exists")
    entries: dict[str, bytes] = {}
    for name in PAYLOADS:
        path = ROOT / name
        if not stat.S_ISREG(path.lstat().st_mode):
            raise ValueError("Missing regular first-party payload: " + name)
        entries[TOP + "/" + name] = path.read_bytes()
    manifest = {
        "schema":"hpr.private-scene-identity-cli-archive.v1",
        "tool_version":"0.1.1",
        "rights":"internal prerelease evaluation only; not a marketplace licence",
        "status":"PRIVATE_SOURCE_CLI_CANDIDATE_NOT_PUBLISHED",
        "native_unity_editor_tested":False,
        "coverage":"direct-serialized-gameobject-documents-only",
        "payload_sha256":{n:sha(d) for n,d in sorted(entries.items())},
        "payload_bytes":{n:len(d) for n,d in sorted(entries.items())},
    }
    entries[MANIFEST]=(json.dumps(manifest,sort_keys=True,indent=2)+"\n").encode("utf-8")
    new_zip.parent.mkdir(parents=True,exist_ok=True)
    # Exclusive create prevents accidental reusing or overwriting an old evaluated archive.
    with new_zip.open("xb") as handle:
        with zipfile.ZipFile(handle,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
            for name,payload in sorted(entries.items()):
                info=zipfile.ZipInfo(name,(2026,11,26,0,0,0))
                info.compress_type=zipfile.ZIP_DEFLATED
                info.external_attr=0o100644 << 16
                archive.writestr(info,payload,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    result=verify(new_zip)
    result["status"]="PRIVATE_SOURCE_CLI_CANDIDATE_NOT_PUBLISHED"
    result["created_utc"]=datetime.now(timezone.utc).isoformat()
    return result


def verify(archive_file: Path) -> dict:
    with zipfile.ZipFile(archive_file) as archive:
        names=archive.namelist()
        expected=sorted([TOP+"/"+x for x in PAYLOADS]+[MANIFEST])
        if names != expected:
            raise ValueError("Archive has missing, unsafe, extra or reordered members: "+str(names))
        if archive.testzip():
            raise ValueError("Archive internal checksum failure")
        manifest=json.loads(archive.read(MANIFEST))
        if manifest.get("schema")!="hpr.private-scene-identity-cli-archive.v1" or manifest.get("native_unity_editor_tested") is not False:
            raise ValueError("Invalid private licence and native acceptance status")
        assert set(manifest["payload_sha256"])=={TOP+"/"+x for x in PAYLOADS}
        for name in manifest["payload_sha256"]:
            actual=archive.read(name)
            if sha(actual)!=manifest["payload_sha256"][name] or len(actual)!=manifest["payload_bytes"][name]:
                raise ValueError("Payload differs from manifest: "+name)
            if name.endswith(".py") and actual!= (ROOT/"hpr_scene_identity.py").read_bytes():
                raise ValueError("Archived Python source differs from source control")
        return {
            "verification":"EXACT_PRIVATE_ARCHIVE_INVENTORY_HASH_AND_SOURCE_MATCH",
            "archive":str(archive_file),
            "archive_bytes":archive_file.stat().st_size,
            "archive_sha256":sha(archive_file.read_bytes()),
            "payloads":len(manifest["payload_sha256"]),
            "members":len(names),
            "native_unity_editor_tested":False,
            "rights":manifest["rights"],
        }


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("new_zip",type=Path)
    args=parser.parse_args()
    print(json.dumps(package(args.new_zip),indent=2))


if __name__=="__main__":
    main()
