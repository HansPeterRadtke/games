#!/usr/bin/env python3
"""Read-only cumulative Unity Editor buyer candidate source provenance.

Compare a new source-only proposal with the exact original frozen 161-asset
seller-candidate source. Never read symlink targets outside the source tree;
do not modify user assets, GUIDs, Unity packages, or publisher accounts.

This verifies PATH/CONTENT provenance and source-API contracts only.
It cannot certify a Unity Editor compilation, demo scene or sales value.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from verify_detach_overlay import _files

PREFIX = "unity/tools/release/gameplay_suite/"
EDITOR = PREFIX + "HprSelectedAbilityInstaller.cs"
INTEGRATION = PREFIX + "HprSuiteIntegration.cs"
GUIDE = PREFIX + "HprSuiteIntegrationGuide.cs"
DOCS = tuple(PREFIX + n for n in
             ("README.md", "QUICKSTART.md", "ARCHITECTURE.md"))
CHANGES = {EDITOR, INTEGRATION, GUIDE, *DOCS}


def verify(original: Path, proposal: Path) -> dict:
    previous, original_aliases = _files(Path(original))
    current, proposed_aliases = _files(Path(proposal))
    if original_aliases != proposed_aliases:
        raise ValueError("Historical non-shipping helper symlink changed")
    if set(previous) != set(current):
        missing = sorted(set(previous) - set(current))
        added = sorted(set(current) - set(previous))
        raise ValueError("Source paths added or removed: " +
                         str({"added": added[:8], "missing": missing[:8]}))
    changed = sorted(path for path in previous if previous[path] != current[path])
    if set(changed) != CHANGES:
        raise ValueError("Cumulative proposal changed unexpected paths: " + ", ".join(changed))
    metas = sorted(path for path in previous if path.endswith(".meta"))
    if any(previous[key] != current[key] for key in metas):
        raise ValueError("Unity source-controlled metadata identities have changed")
    root = Path(proposal)
    editor = (root / EDITOR).read_text(encoding="utf-8")
    native = (root / INTEGRATION).read_text(encoding="utf-8")
    guide = (root / GUIDE).read_text(encoding="utf-8")
    for marker in ("Undo.DestroyObjectImmediate(", "RemoveExplicitly(",
                   "HprSuiteAbilityPool", "HasValidStatsSource"):
        if marker not in editor:
            raise ValueError("Selected-object Editor feature is missing " + marker)
    for marker in ("[SerializeField] private ActorStatsComponent stats;",
                   "GetComponent<ActorStatsComponent>()", "HasValidStatsSource"):
        if marker not in native:
            raise ValueError("Native HPR Stats adapter is missing " + marker)
    if "AssetDatabase.SaveAssets();" in guide or \
            "AssetDatabase.SaveAssetIfDirty(copy)" not in guide:
        raise ValueError("Customer sample saving remains globally destructive")
    if 'File.Exists(physical + ".meta")' not in guide:
        raise ValueError("Customer GUID metadata collision guard is missing")
    if "AssetDatabase.DeleteAsset(" in editor or "EditorSceneManager.SaveScene(" in editor:
        raise ValueError("User-created ability Editor tool has destructive save/delete API")
    for name in DOCS:
        doc = (root / name).read_text(encoding="utf-8").casefold()
        if not any(term in doc for term in ("source-only", "not yet", "not in",
                                           "not compiled", "not shipped")):
            raise ValueError("Buyer documentation fails to disclose source-only status")
    external_in_release = [x for x in original_aliases if x.startswith(PREFIX)]
    if external_in_release:
        raise ValueError("A source-only seller suite points to external symlink targets")
    return {
        "status": "PASS",
        "read_only": True,
        "not_a_published_package": True,
        "full_source_tree_same_paths": True,
        "original_file_count": len(previous),
        "changed_paths": changed,
        "unchanged_guid_meta_count": len(metas),
        "unchanged_other_paths": len(previous) - len(changed),
        "nonshipping_historical_external_alias_count": len(original_aliases),
        "release_source_symlinks_external": False,
        "proposal_editor_sha256": current[EDITOR],
        "proposal_guide_sha256": current[GUIDE],
        "proposal_native_pool_sha256": current[INTEGRATION],
        "warning": "Source-only C# and user documentation provenance; not Unity Editor, render pipeline or publisher acceptance.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frozen", type=Path, required=True)
    parser.add_argument("--proposed", type=Path, required=True)
    parser.add_argument("--output", type=Path, help="write a new private receipt; never overwrite")
    args = parser.parse_args()
    try:
        report = verify(args.frozen, args.proposed)
        raw = json.dumps(report, indent=2, sort_keys=True) + "\n"
        if args.output is not None:
            # One-time receipt creation only, outside each source tree.
            target = args.output.resolve(strict=False)
            if target.is_relative_to(args.frozen.resolve()) or \
                    target.is_relative_to(args.proposed.resolve()):
                raise ValueError("Cannot write source QA receipt into either source tree")
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with target.open("x", encoding="utf-8") as stream:
                stream.write(raw)
            target.chmod(0o600)
        print(raw, end="")
        return 0
    except (ValueError, OSError, UnicodeDecodeError) as exc:
        print(json.dumps({"status": "FAIL", "reason": str(exc),
                          "read_only": True, "not_a_published_package": True}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
