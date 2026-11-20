#!/usr/bin/env python3
"""Read-only source-only Unity detachment overlay provenance check.

Use with two independent source trees, before any real Unity build.
The ONLY allowed changes are the experimental selected ability Editor
script and three explicit buyer-facing documentation files. Every prior
.meta GUID, module source, material, demo scene and source file must
remain byte-identical. A successful report is NOT Unity Editor QA.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


PREFIX = "unity/tools/release/gameplay_suite/"
MODIFIED_SOURCE = PREFIX + "HprSelectedAbilityInstaller.cs"
CHANGED_DOCUMENTS = tuple(PREFIX + name for name in
                          ("README.md", "QUICKSTART.md", "ARCHITECTURE.md"))
ALLOWED_CHANGES = {MODIFIED_SOURCE, *CHANGED_DOCUMENTS}
REQUIRED_IMPLEMENTATION_MARKERS = (
    "public static string ValidateRemoval(",
    "public static bool RemoveExplicitly(",
    "void RemoveRequested(",
    "Undo.DestroyObjectImmediate(",
    "Undo.RevertAllDownToGroup(",
    "EditorUtility.DisplayDialog(",
    "EditorSceneManager.MarkSceneDirty(",
    "PrefabUtility.IsPartOfPrefabAsset(",
    "EditorApplication.isPlayingOrWillChangePlaymode",
)
FORBIDDEN_OPERATIONS = ("AssetDatabase.DeleteAsset(", "EditorSceneManager.SaveScene(")


def _sha256(source: Path) -> str:
    digest = hashlib.sha256()
    with source.open("rb") as handle:
        for block in iter(lambda: handle.read(1_048_576), b""):
            digest.update(block)
    return digest.hexdigest()


def _files(root: Path) -> tuple[dict[str, str], list[str]]:
    if not root.is_dir() or root.is_symlink():
        raise ValueError("A real non-symlink source directory is required")
    entries: dict[str, str] = {}
    legacy_external: list[str] = []
    for p in root.rglob("*"):
        name = p.relative_to(root).as_posix()
        if p.is_symlink():
            target = p.readlink()  # Examine link text; never read the target content.
            if target.is_absolute():
                # These two *non-shipping* historical Unity helper project
                # aliases were already in the frozen source. Warn, do not
                # dereference them or pretend the entire repository is hermetic.
                if not (name.startswith("unity/tools/assetstore/helper_project/Packages/")
                        and str(target).startswith("/data/src/github/games/unity/packages/")):
                    raise ValueError("Unexpected external source symlink: " + name)
                legacy_external.append(name)
            else:
                resolved = (p.parent / target).resolve(strict=False)
                if not resolved.is_relative_to(root.resolve()) or not resolved.exists():
                    raise ValueError("Symlink escapes source tree or is broken: " + name)
            entries[name] = hashlib.sha256(
                ("SYMLINK->" + str(target)).encode("utf-8")).hexdigest()
            continue
        if p.is_dir():
            continue
        if not p.is_file():
            raise ValueError("Unrecognized source tree entry: " + name)
        entries[name] = _sha256(p)
    if not entries:
        raise ValueError("Source tree is empty")
    return entries, sorted(legacy_external)


def verify_overlay(frozen: Path, proposed: Path) -> dict:
    before, earlier_external = _files(Path(frozen))
    after, proposed_external = _files(Path(proposed))
    if earlier_external != proposed_external:
        raise ValueError("Existing external helper symlinks changed")
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    if added or removed:
        raise ValueError("Unexpected source file addition/removal: " +
                         str({"added": added[:10], "removed": removed[:10]}))
    changed = sorted(name for name in after if after[name] != before[name])
    if set(changed) != ALLOWED_CHANGES:
        raise ValueError("The source overlay did not change exactly the four authorized files: " +
                         ", ".join(changed))
    metas = sorted(name for name in after if name.endswith(".meta"))
    if any(after[name] != before[name] for name in metas):
        raise ValueError("Unity asset GUID metadata changed unexpectedly")
    src = (Path(proposed) / MODIFIED_SOURCE).read_text(encoding="utf-8")
    absent = [marker for marker in REQUIRED_IMPLEMENTATION_MARKERS if marker not in src]
    if absent:
        raise ValueError("Detachment public Unity API contract missing: " + ", ".join(absent))
    for forbidden in FORBIDDEN_OPERATIONS:
        if forbidden in src:
            raise ValueError("Unexpected destructive or automatic save API: " + forbidden)
    for name in CHANGED_DOCUMENTS:
        info = (Path(proposed) / name).read_text(encoding="utf-8").casefold()
        if not any(claim in info for claim in
                   ("source-only", "not yet", "not in", "not compiled", "not shipped")):
            raise ValueError("Buyer-facing documentation failed to state nonreleased status: " + name)
    return {
        "result": "PASS",
        "read_only": True,
        "not_a_published_package": True,
        "prior_files_checked": len(before),
        "changed_paths": changed,
        "unchanged_meta_file_count": len(metas),
        "unchanged_other_files": len(before) - len(changed),
        "non_shipping_external_symlinks": len(earlier_external),
        "non_shipping_external_symlink_paths": earlier_external,
        "entire_repository_snapshot_hermetic": not bool(earlier_external),
        "release_gameplay_suite_source_hermetic": not any(
            name.startswith(PREFIX) for name in earlier_external),
        "experimental_source_sha256": after[MODIFIED_SOURCE],
        "warning": "Source-only content provenance, not a Unity compile, import, visual or user-value acceptance.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frozen", type=Path, required=True)
    parser.add_argument("--proposed", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(verify_overlay(args.frozen, args.proposed),
                         sort_keys=True, indent=2))
        return 0
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(json.dumps({"result": "FAIL", "reason": str(exc),
                          "read_only": True,
                          "not_a_published_package": True}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
