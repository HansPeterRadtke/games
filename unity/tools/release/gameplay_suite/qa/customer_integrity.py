#!/usr/bin/env python3
"""Private customer-file preservation gate for imported Unity archives.

Use snapshots of one *disposable* customer project before and after a real
Unity Editor import. The gate never edits the project or unpacks the archive.
Its snapshot files contain hashes and paths, not customer asset contents.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import tarfile

DEFAULT_CUSTOMER_ROOTS = ("Assets/ExternalCustomerGame",)
PROTECTED_PROJECT_FILES = (
    "ProjectSettings/EditorBuildSettings.asset",
    "ProjectSettings/EditorSettings.asset",
    "ProjectSettings/GraphicsSettings.asset",
    "ProjectSettings/InputManager.asset",
    "ProjectSettings/ProjectSettings.asset",
    "ProjectSettings/QualitySettings.asset",
    "ProjectSettings/TagManager.asset",
    "Packages/manifest.json",
)
_GUID = re.compile(r"(?m)^guid:\s*([a-f0-9]{32})\s*$")


def _relative_path(raw: str) -> Path:
    """Reject watch paths that could escape the selected project root."""
    rel = PurePosixPath(raw)
    if not raw or rel.is_absolute() or ".." in rel.parts or "\\" in raw:
        raise ValueError("Watched Unity path must be project-relative: " + raw)
    if rel.parts[0] not in ("Assets", "ProjectSettings", "Packages"):
        raise ValueError("Watched path must belong to Unity project: " + raw)
    return Path(*rel.parts)


def _reject_symlink_components(project: Path, rel: Path) -> None:
    cursor = project
    for component in rel.parts:
        cursor = cursor / component
        if cursor.is_symlink():
            raise ValueError("Refusing symlinked Unity project path: " +
                             (cursor.relative_to(project)).as_posix())


def _watched_files(project: Path, customer_roots: tuple[str, ...]) -> dict[str, Path]:
    if not project.is_dir() or project.is_symlink():
        raise ValueError("Must provide an existing non-symlink Unity project")
    result: dict[str, Path] = {}
    customer_found = False
    for raw in customer_roots:
        rel = _relative_path(raw)
        if rel.parts[:1] != ("Assets",) or len(rel.parts) < 2:
            raise ValueError("Customer roots must name a dedicated Assets subfolder")
        _reject_symlink_components(project, rel)
        base = project / rel
        if not base.is_dir():
            continue
        for item in base.rglob("*"):
            if item.is_symlink():
                raise ValueError("Refusing customer file symlink: " +
                                 item.relative_to(project).as_posix())
            if not item.is_file():
                continue
            relative = item.relative_to(project).as_posix()
            result[relative] = item
            customer_found = True
    if not customer_found:
        raise ValueError("No customer-owned files were found to protect")
    for raw in PROTECTED_PROJECT_FILES:
        rel = _relative_path(raw)
        _reject_symlink_components(project, rel)
        path = project / rel
        if path.is_file():
            result[raw] = path
    return result


def _digest(file: Path) -> str:
    sha = hashlib.sha256()
    with file.open("rb") as source:
        for block in iter(lambda: source.read(1048576), b""):
            sha.update(block)
    return sha.hexdigest()


def snapshot_customer_project(
    project: Path, customer_roots: tuple[str, ...] = DEFAULT_CUSTOMER_ROOTS
) -> dict[str, str]:
    """Capture original file bytes, .meta GUIDs, game scenes and relevant settings."""
    root = Path(project)
    return {name: _digest(path)
            for name, path in sorted(_watched_files(root, customer_roots).items())}


def compare_customer_snapshot(
    project: Path,
    baseline: dict[str, str],
    customer_roots: tuple[str, ...] = DEFAULT_CUSTOMER_ROOTS,
) -> list[str]:
    """Return every added, deleted or modified protected project file."""
    if not isinstance(baseline, dict) or not baseline:
        raise ValueError("A nonempty trusted customer baseline is required")
    for name, digest in baseline.items():
        _relative_path(name)
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("Invalid baseline digest for " + name)
    current = snapshot_customer_project(project, customer_roots)
    return sorted(
        name for name in (set(current) | set(baseline))
        if current.get(name) != baseline.get(name)
    )


def find_customer_guid_collisions(project: Path, archive: Path) -> list[str]:
    """Pre-import guard for vendor GUIDs already owned by unrelated buyer files."""
    project = Path(project)
    _reject_symlink_components(project, Path("Assets"))
    assets = project / "Assets"
    if not assets.is_dir():
        raise ValueError("Missing Unity Assets directory")
    if not Path(archive).is_file():
        raise FileNotFoundError(archive)
    incoming: set[str] = set()
    with tarfile.open(archive, "r:gz") as package:
        for entry in package:
            if not entry.name.endswith("/pathname"):
                continue
            guid = entry.name.split("/", 1)[0]
            if not re.fullmatch(r"[0-9a-f]{32}", guid):
                raise ValueError("Invalid Unity asset GUID in candidate")
            incoming.add(guid)
    conflicts: list[str] = []
    for meta in assets.rglob("*.meta"):
        if meta.is_symlink():
            raise ValueError("Refusing symlinked asset metadata")
        rel = meta.relative_to(project).as_posix()
        if rel == "Assets/HPRGameplaySuite.meta" or rel.startswith("Assets/HPRGameplaySuite/"):
            continue  # A separately tested and explicitly approved vendor update.
        match = _GUID.search(meta.read_text(encoding="utf-8", errors="replace"))
        if match and match.group(1) in incoming:
            conflicts.append(rel)
    return sorted(conflicts)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--capture", type=Path, help="new snapshot JSON path")
    group.add_argument("--verify", type=Path, help="existing snapshot JSON path")
    parser.add_argument("--customer-root", action="append",
                        default=None, help="e.g. Assets/MyGame, repeatable")
    parser.add_argument("--archive", type=Path,
                        help="optional pre-import unrelated GUID conflict check")
    args = parser.parse_args()
    roots = tuple(args.customer_root or DEFAULT_CUSTOMER_ROOTS)
    if args.archive:
        collisions = find_customer_guid_collisions(args.project, args.archive)
        if collisions:
            raise SystemExit("Customer GUID collision: " + ", ".join(collisions))
    if args.capture:
        baseline = snapshot_customer_project(args.project, roots)
        args.capture.parent.mkdir(parents=True, exist_ok=True)
        with args.capture.open("x", encoding="utf-8") as target:
            json.dump({"schema": 1, "roots": roots, "files": baseline},
                      target, indent=2, sort_keys=True)
            target.write("\n")
        print("CUSTOMER_INTEGRITY_BASELINE_CAPTURED", len(baseline))
        return
    receipt = json.loads(args.verify.read_text(encoding="utf-8"))
    if receipt.get("schema") != 1 or tuple(receipt.get("roots", ())) != roots:
        raise ValueError("Snapshot schema or customer roots mismatch")
    changed = compare_customer_snapshot(args.project, receipt["files"], roots)
    if changed:
        raise SystemExit("CUSTOMER_INTEGRITY_FAILED: " + ", ".join(changed))
    print("CUSTOMER_INTEGRITY_PASS", len(receipt["files"]))


if __name__ == "__main__":
    main()
