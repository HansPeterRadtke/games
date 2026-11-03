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

DEFAULT_CUSTOMER_ROOTS = ("Assets",)
PROTECTED_PROJECT_FILES = (
    "ProjectSettings/EditorBuildSettings.asset",
    "ProjectSettings/EditorSettings.asset",
    "ProjectSettings/GraphicsSettings.asset",
    "ProjectSettings/InputManager.asset",
    "ProjectSettings/ProjectSettings.asset",
    "ProjectSettings/QualitySettings.asset",
    "ProjectSettings/TagManager.asset",
    "Packages/manifest.json",
    "Packages/packages-lock.json",
)
_GUID = re.compile(r"(?mi)^guid:\s*([a-f0-9]{32})\s*$")

# Exactly these ten module identifiers were observed inside the original
# frozen 161-asset HPR package's Modules folder. Prefix matching on
# "com.hpr." would also hide customer-owned packages such as
# "com.hpr.customerbridge", causing GUID and source-preservation gaps.
# Unknown future module names fail conservatively as customer content.
HPR_OWNED_EMBEDDED_MODULES = frozenset({
    "com.hpr.abilities", "com.hpr.ai", "com.hpr.composition",
    "com.hpr.eventbus", "com.hpr.interaction", "com.hpr.inventory",
    "com.hpr.save", "com.hpr.stats", "com.hpr.weapons", "com.hpr.world",
})


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
        if rel.parts[:1] != ("Assets",):
            raise ValueError("Customer roots must be Unity Assets folders")
        _reject_symlink_components(project, rel)
        base = project / rel
        if not base.is_dir():
            continue
        for item in base.rglob("*"):
            relative = item.relative_to(project).as_posix()
            if rel.parts == ("Assets",) and (
                relative == "Assets/HPRGameplaySuite.meta" or
                relative.startswith("Assets/HPRGameplaySuite/")
            ):
                continue  # This vendor-owned root is checked separately for upgrade.
            if item.is_symlink():
                raise ValueError("Refusing customer file symlink: " + relative)
            if not item.is_file():
                continue
            result[relative] = item
            customer_found = True
    if not customer_found:
        raise ValueError("No customer-owned files were found to protect")
    # Unity has many persistent project controls beyond the common input and
    # graphics settings. Protect every existing setting, not an arbitrary shortlist.
    settings_root = project / "ProjectSettings"
    if settings_root.is_symlink():
        raise ValueError("Refusing symlinked Unity ProjectSettings directory")
    if settings_root.is_dir():
        for item in settings_root.rglob("*"):
            if item.is_symlink():
                raise ValueError("Refusing symlinked Unity setting: " +
                                 item.relative_to(project).as_posix())
            if item.is_file():
                result[item.relative_to(project).as_posix()] = item
    # Unity supports editable CUSTOMER embedded packages. Their scripts,
    # assembly references, package.json files and .meta identities are just
    # as important to protect as files under Assets and ProjectSettings.
    # The project's two top-level manifest/lock files are separately retained
    # below; their duplicate dictionary keys have identical byte identities.
    package_root = project / "Packages"
    if package_root.is_symlink() or (package_root.exists() and not package_root.is_dir()):
        raise ValueError("Refusing symlinked/non-directory Unity Packages root")
    if package_root.is_dir():
        for item in package_root.rglob("*"):
            relative = item.relative_to(project).as_posix()
            if item.is_symlink():
                raise ValueError("Refusing symlinked embedded customer package file: " + relative)
            if item.is_dir() or not item.is_file():
                continue
            if (relative.startswith("Packages/") and
                relative.split("/")[1] in HPR_OWNED_EMBEDDED_MODULES):
                continue  # HPR's own embedded runtime is checked as a vendor dependency.
            result[relative] = item
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
    package_root = project / "Packages"
    if package_root.is_symlink() or (package_root.exists() and not package_root.is_dir()):
        raise ValueError("Refusing symlinked/non-directory Unity Packages root")
    # Unity AssetDatabase GUIDs are project-wide, including editable UPM
    # packages in Packages/com.customer.*. A collision there could redirect
    # existing customer references even when Assets itself is conflict-free.
    roots = (assets, package_root) if package_root.is_dir() else (assets,)
    conflicts: list[str] = []
    seen_customer_guids: dict[str, str] = {}
    max_meta_bytes = 4_194_304
    for root in roots:
        for item in root.rglob("*"):
            rel = item.relative_to(project).as_posix()
            if item.is_symlink():
                raise ValueError("Refusing symlinked asset or embedded package path: " + rel)
            if not item.is_file() or not rel.endswith(".meta"):
                continue
            if rel == "Assets/HPRGameplaySuite.meta" or rel.startswith("Assets/HPRGameplaySuite/"):
                continue  # HPR's own vendor identities are checked separately.
            if rel.startswith("Packages/") and rel.split("/")[1] in HPR_OWNED_EMBEDDED_MODULES:
                continue  # Do not count HPR's own embedded package metadata as a buyer collision.
            if item.stat().st_size > max_meta_bytes:
                raise ValueError("Customer metadata exceeds bounded safety scan: " + rel)
            # A hostile/broken .meta may change between stat and read.
            # Do not allocate its entire potentially huge content.
            with item.open("rb") as stream:
                raw = stream.read(max_meta_bytes + 1)
            if len(raw) > max_meta_bytes:
                raise ValueError("Customer metadata grew beyond bounded safety scan: " + rel)
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError as error:
                raise ValueError("Customer metadata is not valid UTF-8: " + rel) from error
            matches = _GUID.findall(text)
            if not matches:
                raise ValueError("malformed customer Unity metadata: no valid root GUID in " + rel)
            if len(matches) != 1:
                raise ValueError("multiple root GUID entries in customer metadata: " + rel)
            guid = matches[0].lower()
            former = seen_customer_guids.get(guid)
            if former is not None:
                raise ValueError("duplicate customer asset GUID at " + former + " and " + rel)
            seen_customer_guids[guid] = rel
            if guid in incoming:
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
