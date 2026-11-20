#!/usr/bin/env python3
"""Read-only exact Unity package vs fresh imported project verification.

Narrow policy is deliberate: rejects unexpected package roots and unsafe paths.
Does not import, extract, overwrite, delete, or repair customer files.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import tarfile

GUID = re.compile(r"^[0-9a-f]{32}$")
ROOT = PurePosixPath("Assets/HPRAnimatorContract")
MEMBER = re.compile(r"^([0-9a-f]{32})/(pathname|asset|asset.meta)$")


def check(archive: Path, project: Path) -> dict:
    errors = []
    blobs: dict[str, bytes] = {}
    with tarfile.open(archive, "r:gz") as src:
        for member in src:
            if not member.isfile() or not MEMBER.fullmatch(member.name):
                errors.append(f"Unexpected Unity package member: {member.name}")
                continue
            if member.name in blobs:
                errors.append(f"Duplicate archive member: {member.name}")
                continue
            if member.size > 8 * 1024 * 1024:
                errors.append("Unexpected huge package member: " + member.name)
                continue
            stream = src.extractfile(member)
            if stream is None:
                errors.append("Unreadable archive member: " + member.name)
                continue
            blobs[member.name] = stream.read()
    paths = {}
    for name, raw in blobs.items():
        match = MEMBER.fullmatch(name)
        if not match or match[2] != "pathname":
            continue
        guid = match[1]
        try:
            decoded = raw.decode("utf-8").strip()
        except UnicodeDecodeError:
            errors.append("Invalid UTF-8 asset pathname: " + name)
            continue
        rel = PurePosixPath(decoded)
        if (rel != ROOT and ROOT not in rel.parents) or ".." in rel.parts or "\\" in decoded or rel.is_absolute():
            errors.append("Asset outside dedicated product root: " + decoded)
            continue
        if decoded in paths:
            errors.append("Duplicate asset pathname: " + decoded)
        paths[decoded] = guid
        folder = f"{guid}/"
        meta = blobs.get(folder + "asset.meta")
        if meta is None:
            errors.append("No metadata: " + decoded)
            continue
        meta_guid = re.search(rb"(?m)^guid:\s*([0-9a-f]{32})\s*$", meta)
        if meta_guid is None or meta_guid.group(1).decode() != guid:
            errors.append("Package asset GUID mismatch: " + decoded)
        path = project / decoded
        if path.is_symlink() or path.with_name(path.name + ".meta").is_symlink():
            errors.append("Buyer project symlink: " + decoded)
            continue
        if not path.exists():
            errors.append("Missing imported asset: " + decoded)
            continue
        payload = blobs.get(folder + "asset")
        if payload is None:
            if not path.is_dir():
                errors.append("Expected folder not created: " + decoded)
        elif not path.is_file() or path.read_bytes() != payload:
            errors.append("Imported asset payload differs: " + decoded)
        on_disk_meta = path.with_name(path.name + ".meta")
        if not on_disk_meta.is_file() or on_disk_meta.read_bytes() != meta:
            errors.append("Imported metadata differs: " + decoded)
    expected = {"Assets/HPRAnimatorContract", "Assets/HPRAnimatorContract/Editor",
                "Assets/HPRAnimatorContract/README.md",
                "Assets/HPRAnimatorContract/Editor/HprAnimatorContractAudit.cs"}
    if set(paths) != expected:
        errors.append("Unexpected complete product asset-path set")
    return {"status": "PASS" if not errors else "FAIL", "issues": errors,
            "paths_verified": len(paths), "scripts_verified": sum(x.endswith(".cs") for x in paths),
            "package_sha256": hashlib.sha256(archive.read_bytes()).hexdigest()}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive", type=Path, required=True)
    ap.add_argument("--project", type=Path, required=True)
    ap.add_argument("--receipt", type=Path)
    args = ap.parse_args()
    receipt = check(args.archive, args.project)
    if args.receipt:
        with args.receipt.open("x") as f:
            json.dump(receipt, f, indent=2)
    print(json.dumps(receipt, indent=2))
    return 0 if receipt["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
