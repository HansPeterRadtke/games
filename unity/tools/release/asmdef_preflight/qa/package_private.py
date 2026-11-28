#!/usr/bin/env python3
"""Package only exact first-party reviewed CLI files into a PRIVATE ZIP."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
SHIP = ("hpr_asmdef_preflight.py", "README.md", "LICENSE.md", "ThirdPartyNotices.md")
PREFIX = "HPRAssemblyPreflight/"


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def package(destination: Path) -> dict:
    if not str(destination).startswith("/data/var/marketplace-account-setup/"):
        raise ValueError("Buyer prerelease ZIP must stay in private marketplace evidence storage")
    if destination.suffix.lower() != ".zip" or destination.exists() or destination.is_symlink():
        raise ValueError("Create-only new private .zip output required")
    if not destination.parent.is_dir() or destination.parent.is_symlink():
        raise ValueError("Existing real private output directory required")
    sources = {}
    for relative in SHIP:
        file = ROOT/relative
        if not file.is_file() or file.is_symlink() or file.stat().st_size > 400_000:
            raise ValueError("Source missing or unsafe: " + relative)
        blob = file.read_bytes()
        if b"\x00" in blob:
            raise ValueError("Unexpected binary source: " + relative)
        sources[relative] = blob
    if b"private" not in sources["LICENSE.md"].lower():
        raise ValueError("Prerelease license lacks private-only disclosure")
    with ZipFile(destination, mode="x", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for name in SHIP:
            info = ZipInfo(PREFIX+name, date_time=(2026, 11, 28, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            archive.writestr(info, sources[name], compress_type=ZIP_DEFLATED, compresslevel=9)
    with ZipFile(destination) as archive:
        actual = archive.namelist()
        if actual != [PREFIX+name for name in SHIP]:
            raise ValueError("Packaged unrelated files")
        for name, blob in sources.items():
            if archive.read(PREFIX+name) != blob:
                raise ValueError("Packaged file content changed")
    return {"status":"PASS_PRIVATE_CLI_ZIP_NOT_PUBLISHED","version":"0.1.0-private",
            "zip_path":str(destination),"zip_sha256":digest(destination.read_bytes()),
            "sources_sha256":{name:digest(b) for name,b in sources.items()},
            "files":[PREFIX+name for name in SHIP],"contains_private_qa":False,
            "source_only":True,"unity_editor_native_acceptance":False,
            "marketplace_publication":False}


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('new_private_zip',type=Path)
    args=parser.parse_args()
    result=package(args.new_private_zip)
    print(json.dumps(result,indent=2))
