#!/usr/bin/env python3
"""Create-only, reproducible private Unity archive for QA, NOT a Unity export.

Repackages exact existing Unity .unitypackage GUID entries while replacing
ONLY independently reviewed HPR source/doc files. Metadata and all other
asset bytes are unchanged. The resulting archive MUST undergo genuine
Unity Editor import, runtime, pipeline and customer-integrity tests before
being described as saleable. No publisher/account/network action occurs.
"""
from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile

from unity_archive_policy import inspect_archive
from verify_detach_overlay import _files

ROOT = "Assets/HPRGameplaySuite"
SOURCE_PREFIX = "unity/tools/release/gameplay_suite/"
REPLACEMENTS = {
    SOURCE_PREFIX + "HprSuiteIntegration.cs":
        ROOT + "/Integration/HprSuiteIntegration.cs",
    SOURCE_PREFIX + "HprSelectedAbilityInstaller.cs":
        ROOT + "/Editor/HprSelectedAbilityInstaller.cs",
    SOURCE_PREFIX + "HprSuiteIntegrationGuide.cs":
        ROOT + "/Editor/HprSuiteIntegrationGuide.cs",
    SOURCE_PREFIX + "HprGameplaySuiteSceneBuilder.cs":
        ROOT + "/Editor/HprGameplaySuiteSceneBuilder.cs",
    SOURCE_PREFIX + "README.md": ROOT + "/README.md",
    SOURCE_PREFIX + "QUICKSTART.md": ROOT + "/QUICKSTART.md",
    SOURCE_PREFIX + "ARCHITECTURE.md": ROOT + "/ARCHITECTURE.md",
}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def build(original_archive: Path, original_source: Path,
          proposed_source: Path, destination: Path,
          *, replacements: dict[str, str] | None = None) -> dict:
    """Create exactly one new private tar-format QA candidate.

    This function does not modify either source, an existing archive or
    another user's Unity project. Failed/uncertain outputs are left in place
    for inspection, rather than automatically retried or erased.
    """
    allowed = dict(REPLACEMENTS if replacements is None else replacements)
    if not allowed or len(set(allowed.values())) != len(allowed):
        raise ValueError("A nonempty one-to-one asset/source replacement map is required")
    archive = Path(original_archive)
    out = Path(destination)
    if out.suffix != ".unitypackage" or out.exists() or out.is_symlink():
        raise FileExistsError("A unique new private Unity QA archive path is required")
    resolved_output = out.resolve(strict=False)
    if archive.resolve(strict=False) == resolved_output:
        raise ValueError("Cannot replace the original archive")
    for source_tree in (Path(original_source), Path(proposed_source)):
        if resolved_output.is_relative_to(source_tree.resolve(strict=False)):
            raise ValueError("QA output must never be created inside an original source tree")
    before, old_external = _files(Path(original_source))
    after, new_external = _files(Path(proposed_source))
    if old_external != new_external:
        raise ValueError("Historical external source aliases changed")
    if set(before) != set(after):
        raise ValueError("Source file/path identity set changed unexpectedly")
    changed = {name for name in before if before[name] != after[name]}
    if changed != set(allowed):
        raise ValueError("Unexpected source changes outside exact HPR QA allowlist: " +
                         str(sorted(changed ^ set(allowed))[:12]))
    if any(before[p] != after[p] for p in before if p.endswith(".meta")):
        raise ValueError("An original Unity .meta GUID identity changed")
    original_archive_status = inspect_archive(archive)
    if original_archive_status["status"] != "PASS":
        raise ValueError("Original immutable Unity archive failed independent structural QA")

    # Read archive without extraction or running untrusted asset content.
    with tarfile.open(archive, "r:gz") as source:
        members = [copy.copy(member) for member in source.getmembers()]
        if not all(member.isfile() for member in members):
            raise ValueError("An unexpected non-file tar member cannot be repacked")
        data = {}
        for member in members:
            stream = source.extractfile(member)
            if stream is None:
                raise ValueError("Tar member lacks its expected content")
            data[member.name] = stream.read(member.size + 1)
            if len(data[member.name]) != member.size:
                raise ValueError("Archive member payload length changed during read")
    paths: dict[str, str] = {}
    for filename, raw in data.items():
        if filename.endswith("/pathname"):
            paths[raw.decode("utf-8").strip()] = filename.split("/",1)[0]
    changed_entries: dict[str, bytes] = {}
    for source_rel, archive_path in allowed.items():
        if not archive_path.startswith(ROOT + "/"):
            raise ValueError("Refusing to patch any non-suite asset")
        oldfile = Path(original_source) / source_rel
        candidate = Path(proposed_source) / source_rel
        if (not oldfile.is_file() or oldfile.is_symlink() or
                not candidate.is_file() or candidate.is_symlink()):
            raise ValueError("Missing or symlinked replacement source: " + source_rel)
        guid = paths.get(archive_path)
        if guid is None:
            raise ValueError("Authorized replacement not found in prior Unity archive: " + archive_path)
        tar_key = guid + "/asset"
        old_payload = oldfile.read_bytes()
        if tar_key not in data or data[tar_key] != old_payload:
            raise ValueError("Prior archive payload differs from archived frozen source: " + archive_path)
        if sha(old_payload) != before[source_rel]:
            raise ValueError("Frozen source changed after the initial file inventory: " + source_rel)
        payload = candidate.read_bytes()
        if sha(payload) != after[source_rel]:
            raise ValueError("Candidate source changed after the initial file inventory: " + source_rel)
        if payload == data[tar_key]:
            raise ValueError("An authorized change is unexpectedly byte-identical: " + archive_path)
        changed_entries[tar_key] = payload
    expected_count = len(data)
    if len(changed_entries) != len(allowed):
        raise ValueError("Duplicate or missing prior Unity source identities")

    # The gzip+tar header is deterministic. Contents of every GUID asset.meta
    # and pathname are copied unmodified from the original Unity export.
    out.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with out.open("xb") as rawout:
        with gzip.GzipFile(filename="", mode="wb", fileobj=rawout, mtime=0) as gz:
            with tarfile.open(fileobj=gz, mode="w", format=tarfile.USTAR_FORMAT) as tar:
                for member in members:
                    content = changed_entries.get(member.name, data[member.name])
                    member.size = len(content)
                    member.mtime = 0
                    member.uid = 0
                    member.gid = 0
                    member.uname = ""
                    member.gname = ""
                    tar.addfile(member, io.BytesIO(content))
    out.chmod(0o600)

    qa = inspect_archive(out)
    if qa["status"] != "PASS":
        raise ValueError("New private QA tar failed post-build policy audit; do not import")
    with tarfile.open(out, "r:gz") as check:
        verified = {member.name:check.extractfile(member).read()
                    for member in check if member.isfile()}
    if len(verified) != expected_count or set(verified) != set(data):
        raise ValueError("Repacked candidate unexpectedly added/removed archive members")
    if any(verified[name] != payload for name, payload in changed_entries.items()):
        raise ValueError("Repacked HPR source patch was not preserved exactly")
    if any(verified[name] != original for name, original in data.items()
           if name not in changed_entries):
        raise ValueError("Non-target asset, GUID metadata or pathname bytes changed")

    meta_count = sum(1 for name in data if name.endswith("/asset.meta"))
    return {
        "status": "PASS",
        "archive_sha256": sha(out.read_bytes()),
        "original_archive_sha256": original_archive_status["archive_sha256"],
        "archive_format": "Unity-compatible tar format assembled for private QA; not exported by Unity Editor",
        "not_a_unity_editor_import": True,
        "not_published_or_approved": True,
        "asset_count": qa["asset_count"],
        "assembly_definitions": qa["assembly_definitions"],
        "changed_asset_paths": sorted(allowed.values()),
        "changed_payload_count": len(changed_entries),
        "unchanged_archive_member_count": expected_count-len(changed_entries),
        "unchanged_asset_meta_count": meta_count,
        "unchanged_source_meta_count": sum(1 for name in before if name.endswith(".meta")),
        "original_source_files_read_only": True,
        "new_archive_create_only": True,
    }


def validate_receipt_path(receipt: Path, original_archive: Path,
                          original_source: Path, proposed_source: Path,
                          output_archive: Path) -> None:
    """Keep all build/QA report writes outside preserved source trees.

    A report must not replace either archive, nor be redirected through a
    symlink into an original source tree. This is a pre-effect check.
    """
    dest = Path(receipt).resolve(strict=False)
    if dest in (Path(original_archive).resolve(strict=False),
                Path(output_archive).resolve(strict=False)):
        raise ValueError("The build receipt cannot replace a package archive")
    for source in (Path(original_source), Path(proposed_source)):
        if dest.is_relative_to(source.resolve(strict=False)):
            raise ValueError("Build receipt must never be created in a source tree")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-archive", type=Path, required=True)
    parser.add_argument("--original-source", type=Path, required=True)
    parser.add_argument("--proposed-source", type=Path, required=True)
    parser.add_argument("--output-archive", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    try:
        validate_receipt_path(args.receipt, args.original_archive,
                              args.original_source, args.proposed_source,
                              args.output_archive)
        if args.receipt.exists() or args.receipt.is_symlink():
            raise FileExistsError("Private build receipt already exists")
        report = build(args.original_archive, args.original_source,
                       args.proposed_source, args.output_archive)
        with args.receipt.open("x",encoding="utf-8") as fp:
            json.dump(report,fp,indent=2,sort_keys=True)
            fp.write("\n")
        args.receipt.chmod(0o600)
        print(json.dumps(report,sort_keys=True,indent=2))
        return 0
    except (OSError, ValueError, tarfile.TarError) as err:
        print(json.dumps({"status":"FAIL","error_type":type(err).__name__,
                          "error":str(err)[:220],"no_external_effects":True,
                          "do_not_blindly_retry_uncertain_archive":True}))
        return 2


if __name__=="__main__":
    raise SystemExit(main())
