#!/usr/bin/env python3
"""Check that a new Unity buyer archive preserves serialized asset identity.

Unity's .unitypackage format uses a top-level folder named by each asset GUID.
A moved or regenerated GUID breaks existing scene, prefab and ScriptableObject
references even when the pathname looks unchanged. This check is read-only.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import tarfile


def asset_guids(archive: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    reverse: dict[str, str] = {}
    with tarfile.open(archive, "r:gz") as handle:
        for entry in handle:
            if not entry.name.endswith("/pathname"):
                continue
            body = handle.extractfile(entry)
            if body is None:
                raise ValueError("Missing Unity pathname record")
            name = body.read(4096).decode("utf-8").strip().replace("\\", "/")
            guid = entry.name.split("/", 1)[0]
            if len(guid) != 32 or any(letter not in "0123456789abcdef" for letter in guid):
                raise ValueError("Invalid Unity GUID in archive")
            if name in result or guid in reverse:
                raise ValueError("Duplicate Unity path or asset GUID")
            result[name] = guid
            reverse[guid] = name
    if len(result) < 100:
        raise ValueError("Archive is missing expected Unity files")
    return result


def compare(baseline: Path, candidate: Path) -> dict:
    old = asset_guids(baseline)
    new = asset_guids(candidate)
    common = set(old) & set(new)
    changed = sorted(path for path in common if old[path] != new[path])
    candidate_guids = set(new.values())
    removed_references = sorted(path for path in old if old[path] not in candidate_guids)
    return {
        "baseline_assets": len(old),
        "candidate_assets": len(new),
        "shared_assets": len(common),
        "unchanged_shared_guids": len(common) - len(changed),
        "changed_shared_guids": changed,
        "removed_reference_guids": removed_references,
        "added_assets": sorted(set(new) - set(old)),
        "removed_assets": sorted(set(old) - set(new)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    results = compare(args.baseline, args.candidate)
    outcome = "PASS" if not (results["changed_shared_guids"] or
                             results["removed_reference_guids"]) else "FAIL"
    results["upgrade_guid_identity"] = outcome
    if args.receipt is not None:
        if args.receipt.exists():
            raise FileExistsError("Refusing to overwrite an existing QA receipt")
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2))
    if outcome == "FAIL":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
