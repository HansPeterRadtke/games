#!/usr/bin/env python3
"""Exact read-only .unitypackage vs actual imported Unity project integrity.

Checks EVERY archived asset payload, full metadata and GUID against project files.
A successful result is not proof the Unity Editor compiled or played:
an independent genuine Editor run, log and exit code must be supplied.
Never reads symlink targets or repairs customer project data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import tarfile

from unity_archive_policy import inspect_archive

ROOT = "Assets/HPRGameplaySuite"
GUID = re.compile(rb"(?m)^guid:\s*([0-9a-fA-F]{32})\s*$")


def _digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as handle:
        for part in iter(lambda: handle.read(1_048_576), b""):
            sha.update(part)
    return sha.hexdigest()


def _safe_path(project: Path, relative: str) -> Path:
    current = project
    for segment in Path(relative).parts:
        current /= segment
        if current.is_symlink():
            raise ValueError("symlinked customer/imported asset path: " + relative)
    return current


def verify_import(archive: Path, project: Path, expected_sha: str) -> dict:
    """Read the original exact archive and compare the actual imported tree.

    SHA-256 is a required explicit 64-hex pin. No writing or repair of Unity
    projects, metadata, input settings, or asset content is performed.
    """
    archive = Path(archive)
    project = Path(project)
    if project.is_symlink() or not project.is_dir() or not (project / "Assets").is_dir():
        raise ValueError("A real Unity project containing Assets is required")
    if not isinstance(expected_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_sha):
        raise ValueError("Expected archive SHA-256 must be explicit and lowercase")
    if not archive.is_file() or archive.is_symlink():
        raise ValueError("Exact source archive missing or symlinked")
    observed = _digest(archive)
    if observed != expected_sha:
        raise ValueError("Archive has changed or caller supplied a different expected version")
    check = inspect_archive(archive)
    if check["status"] != "PASS":
        raise ValueError("Source archive failed the independent Unity archive policy gate")

    # Independent tar data read: no extraction and no execution.
    members: dict[str, bytes] = {}
    with tarfile.open(archive, "r:gz") as package:
        for member in package:
            if not member.isfile():
                raise ValueError("Unexpected archive entry type")
            stream = package.extractfile(member)
            if stream is None:
                raise ValueError("Missing Unity archive member data")
            body = stream.read(member.size + 1)
            if len(body) != member.size:
                raise ValueError("Archive payload size mismatch")
            members[member.name] = body

    names: dict[str, str] = {}
    for member, body in members.items():
        if member.endswith("/pathname"):
            asset_name = body.decode("utf-8").strip()
            guid = member.split("/", 1)[0]
            if asset_name in names:
                raise ValueError("Duplicate Unity asset path inside the candidate")
            names[asset_name] = guid

    expected_physical: set[str] = set()
    issues: list[str] = []
    checked_guids = 0
    checked_bodies = 0
    checked_metadata = 0
    fully_verified_paths = 0
    for name, guid in sorted(names.items()):
        asset = _safe_path(project, name)
        metadata = _safe_path(project, name + ".meta")
        expected_physical.add(name)
        expected_physical.add(name + ".meta")
        body_key = guid + "/asset"
        is_folder = body_key not in members
        payload_matches = False
        guid_matches = False
        metadata_matches = False
        if is_folder:
            if not asset.is_dir():
                issues.append("missing imported Unity folder: " + name)
            else:
                payload_matches = True
        elif not asset.is_file():
            issues.append("missing imported Unity asset: " + name)
        else:
            actual = _digest(asset)
            expected_body = hashlib.sha256(members[body_key]).hexdigest()
            if actual != expected_body:
                issues.append("asset payload differs from exact archive: " + name)
            else:
                checked_bodies += 1
                payload_matches = True
        if not metadata.is_file():
            issues.append("missing imported Unity .meta GUID file: " + name)
        else:
            text = metadata.read_bytes()
            match = GUID.search(text)
            if match is None or match.group(1).decode("ascii").lower() != guid:
                issues.append("imported Unity GUID identity mismatch: " + name)
            else:
                checked_guids += 1
                guid_matches = True
            expected_metadata = members.get(guid + "/asset.meta")
            if expected_metadata is None:
                raise ValueError("Missing exact archive metadata: " + name)
            if text != expected_metadata:
                issues.append("imported Unity metadata payload differs from exact archive: " + name)
            else:
                checked_metadata += 1
                metadata_matches = True
        if payload_matches and guid_matches and metadata_matches:
            fully_verified_paths += 1

    # A fresh cleanroom may not contain stale vendor files or injected code.
    suite = _safe_path(project, ROOT)
    if suite.is_dir():
        for path in suite.rglob("*"):
            relative = path.relative_to(project).as_posix()
            if path.is_symlink():
                issues.append("symlinked imported HPR vendor asset: " + relative)
            elif path.is_file() and relative not in expected_physical:
                issues.append("unexpected imported HPR vendor asset: " + relative)

    return {
        "status": "PASS" if not issues else "FAIL",
        "read_only": True,
        "unity_editor_was_executed_by_this_check": False,
        "real_unity_editor_exit_or_compile_proved": False,
        "archive_sha256": observed,
        "asset_paths_expected": len(names),
        "asset_paths_verified": fully_verified_paths,
        "asset_payloads_verified": checked_bodies,
        "metadata_payloads_verified": checked_metadata,
        "guid_identities_verified": checked_guids,
        "issues": sorted(set(issues)),
        "remediation": "Do not report Unity package acceptance until an actual Editor process/log also passes.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--expected-sha256", type=str, required=True)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    try:
        result = verify_import(args.archive, args.project, args.expected_sha256)
        payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.receipt is not None:
            dest = args.receipt.resolve(strict=False)
            if dest.is_relative_to(args.project.resolve()) or dest == args.archive.resolve():
                raise ValueError("QA receipt must be outside the customer Unity project/archive")
            dest.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with dest.open("x", encoding="utf-8") as writer:
                writer.write(payload)
            dest.chmod(0o600)
        print(payload, end="")
        return 0 if result["status"] == "PASS" else 2
    except (OSError, ValueError, tarfile.TarError) as exc:
        print(json.dumps({"status":"ERROR", "error_type":type(exc).__name__,
                          "error":str(exc)[:200], "project_modified":False}))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
