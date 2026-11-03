#!/usr/bin/env python3
"""Read-only HPR customer-game upgrade preflight, never an import approval.

Composes the existing exact-package GUID/source verifier, preserved buyer
file checksum inventory and the customer dependency/uninstall audit.
It never starts Unity Editor, deletes files, changes a project or grants
approval for an automatic package upgrade. The report is preconditions
only; real Unity Editor import, scene/Play-mode QA and owner authorization
remain independent requirements.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from customer_integrity import snapshot_customer_project, find_customer_guid_collisions
from unity_imported_archive_identity import verify_import
from validate_upgrade_guids import compare
from unity_uninstall_preflight import inspect as inspect_uninstall


def digest_file(source: Path) -> str:
    result = hashlib.sha256()
    with source.open("rb") as file:
        for part in iter(lambda: file.read(1_048_576), b""):
            result.update(part)
    return result.hexdigest()


def validate_archive(source: Path, expected: str) -> None:
    if (not isinstance(expected, str) or
            re.fullmatch(r"[0-9a-f]{64}", expected) is None):
        raise ValueError("An explicit lowercase SHA-256 archive pin is required")
    if source.is_symlink() or not source.is_file() or source.suffix != ".unitypackage":
        raise ValueError("A concrete, non-symlink Unity package archive is required")
    if digest_file(source) != expected:
        raise ValueError("The supplied archived package differs from its expected identity")


def validate_receipt_location(receipt: Path, project: Path,
                              old_archive: Path, new_archive: Path) -> None:
    """A newly created proof can never overwrite an input or a buyer file."""
    target = receipt.resolve(strict=False)
    if (target.is_relative_to(project.resolve(strict=False)) or
        target in (old_archive.resolve(strict=False), new_archive.resolve(strict=False))):
        raise ValueError("The QA report must be outside all original buyer/project inputs")
    if receipt.exists() or receipt.is_symlink():
        raise FileExistsError("The requested QA preflight report already exists")


def inspect(project: Path, old_archive: Path, old_sha256: str,
            new_archive: Path, new_sha256: str) -> dict:
    """Preview HPR upgrades only; no implicit Unity or file mutations."""
    project = Path(project)
    previous = Path(old_archive)
    candidate = Path(new_archive)
    if project.is_symlink() or not project.is_dir() or not (project/"Assets").is_dir():
        raise ValueError("An existing non-symlink Unity customer project is required")
    validate_archive(previous, old_sha256)
    validate_archive(candidate, new_sha256)

    customer_original = snapshot_customer_project(project)
    if not customer_original:
        raise ValueError("Expected a real nonempty customer file inventory")
    prior = verify_import(previous, project, old_sha256)
    upgraded_guid = compare(previous, candidate)
    # Unity GUID identities apply across Assets and customer-owned embedded
    # Packages. A foreign file with a vendor GUID must be reviewed before
    # any import, even when the previous vendor install itself is pristine.
    foreign_guid_collisions = find_customer_guid_collisions(project, candidate)
    consumers = inspect_uninstall(project, previous)
    after = snapshot_customer_project(project)
    # A separate customer importer may alter a VENDOR file while preflight
    # is reading customer code. Recheck exact installed payloads/GUIDs at
    # the end, not just the original nonvendor customer file inventory.
    post_vendor = verify_import(previous, project, old_sha256)
    changing_customer_files = sorted(
        path for path in set(customer_original) | set(after)
        if customer_original.get(path) != after.get(path)
    )
    # Recheck pinned archive bytes because an external writer could replace
    # the source during this read-only, multi-file examination.
    validate_archive(previous, old_sha256)
    validate_archive(candidate, new_sha256)

    vendor_issues = list(prior.get("issues") or [])
    post_vendor_issues = list(post_vendor.get("issues") or [])
    relocated_vendor_paths = list(upgraded_guid.get("removed_assets") or [])
    guid_issues = (
        list(upgraded_guid.get("changed_shared_guids") or []) +
        list(upgraded_guid.get("removed_reference_guids") or [])
    )
    deps = list(consumers.get("dependencies") or [])
    unknowns = list(consumers.get("unknowns") or [])

    # Fail closed, ordered by what would make any later import unsafe.
    if changing_customer_files:
        decision = "blocked_customer_files_changed_during_preflight"
        issues = ["Customer source changed during a read-only inspection"]
    elif prior.get("status") != "PASS":
        decision = "blocked_modified_or_missing_old_vendor_assets"
        issues = vendor_issues or ["The exact old archive is not fully installed"]
    elif post_vendor.get("status") != "PASS":
        decision = "blocked_old_vendor_changed_during_preflight"
        issues = post_vendor_issues or ["Existing vendor files changed during the source preflight"]
    elif guid_issues:
        decision = "blocked_asset_guid_breaking_update"
        issues = guid_issues
    elif foreign_guid_collisions:
        decision = "blocked_unrelated_customer_guid_collision"
        issues = foreign_guid_collisions
    elif relocated_vendor_paths:
        # A stable GUID may keep serialized references valid, but C# can
        # still resolve assets by hardcoded path strings. Never silently
        # accept an old vendor path removal/move as a safe upgrade.
        decision = "review_required_removed_or_moved_vendor_paths"
        issues = relocated_vendor_paths
    elif (consumers.get("classification") == "unknown_project_content_requires_review"
          or unknowns):
        decision = "review_required_uninspectable_customer_content"
        issues = [entry.get("reason", "unknown customer source")
                  for entry in unknowns] or ["Some customer source could not be verified"]
    elif deps:
        decision = "review_required_customer_dependencies"
        issues = ["Customer-authored code/assets depend on HPR; verify migration and tests"]
    else:
        decision = "source_preconditions_verified_editor_acceptance_required"
        issues = []

    return {
        "decision": decision,
        "read_only": True,
        "old_archive_sha256": old_sha256,
        "new_archive_sha256": new_sha256,
        "current_installed_vendor_guid_identities": prior.get("guid_identities_verified", 0),
        "old_import_status": prior.get("status"),
        "post_scan_old_import_status": post_vendor.get("status"),
        "new_candidate_guids": upgraded_guid,
        "customer_guid_collisions": foreign_guid_collisions,
        "customer_original_file_count": len(customer_original),
        "customer_original_sha256": customer_original,
        "customer_files_changed_during_preflight": changing_customer_files,
        "customer_dependency_classification": consumers.get("classification"),
        "customer_dependency_count": len(deps),
        "customer_dependency_findings": deps,
        "unknown_customer_content": unknowns,
        "issues": issues,
        "automatic_upgrade_authorized": False,
        "deletion_permitted": False,
        "actual_unity_editor_compilation_or_import_verified": False,
        "requires_real_unity_editor_import_and_customer_playmode": True,
        "requires_owner_release_approval": True,
        "explanation": "Read-only source/asset preflight; test actual Unity import in a fresh clone and preserve customer byte hashes.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--old-archive", type=Path, required=True)
    parser.add_argument("--old-sha256", required=True)
    parser.add_argument("--new-archive", type=Path, required=True)
    parser.add_argument("--new-sha256", required=True)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    try:
        if args.receipt is not None:
            validate_receipt_location(args.receipt, args.project,
                                      args.old_archive, args.new_archive)
        result = inspect(args.project, args.old_archive, args.old_sha256,
                         args.new_archive, args.new_sha256)
        raw = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.receipt is not None:
            args.receipt.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with args.receipt.open("x", encoding="utf-8") as output:
                output.write(raw)
            args.receipt.chmod(0o600)
        print(raw, end="")
        return 0 if result["decision"] == "source_preconditions_verified_editor_acceptance_required" else 2
    except (ValueError, OSError) as error:
        print(json.dumps({"decision": "invalid_or_unavailable_source_preflight",
                          "error": str(error)[:220], "read_only": True,
                          "automatic_upgrade_authorized": False}))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
