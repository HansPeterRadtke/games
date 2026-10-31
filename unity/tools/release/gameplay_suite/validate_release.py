#!/usr/bin/env python3
"""Read-only format/manifest scope QA for a Unity .unitypackage archive."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import tarfile

ROOT = "Assets/HPRGameplaySuite/"
REQUIRED = (
    ROOT + "Demo/GameplaySuiteShowcase.unity",
    ROOT + "Integration/HprGameplaySuitePlayground.cs",
    ROOT + "Editor/HprGameplaySuiteSceneBuilder.cs",
    ROOT + "README.md",
    ROOT + "LICENSE.md",
)
MODULES = (
    "eventbus", "composition", "save", "stats", "inventory", "interaction",
    "abilities", "weapons", "ai", "world",
)


def inspect(archive: Path) -> dict:
    if not archive.is_file() or archive.stat().st_size < 4096:
        raise ValueError("Missing or trivial archive")
    with tarfile.open(archive, "r:gz") as t:
        members = t.getmembers()
        if not members:
            raise ValueError("Empty archive")
        for m in members:
            # Real Unitypackage archives contain one ordinary tar directory per
            # Unity GUID, followed by `pathname`, `asset`, and `asset.meta` files.
            if not (m.isfile() or m.isdir()) or m.size > 70 * 1024 * 1024:
                raise ValueError("Unexpected tar member type or size")
            if m.name.startswith("/") or ".." in Path(m.name).parts:
                raise ValueError("Unsafe tar member path")
        paths = []
        asset_contents = {}
        for m in members:
            if not m.name.endswith("/pathname"):
                continue
            content = t.extractfile(m)
            if content is None:
                raise ValueError("Missing asset pathname")
            path = content.read(4096).decode("utf-8").strip().replace("\\", "/")
            if not path.startswith(ROOT) and path != ROOT.rstrip("/"):
                raise ValueError("Unity package contains files outside one approved root: " + path)
            paths.append(path)
            if path.endswith(".cs") or path.endswith(".md"):
                blob = t.extractfile(m.name.rsplit("/", 1)[0] + "/asset")
                if blob is not None:
                    asset_contents[path] = blob.read(2_000_000)
    if len(paths) != len(set(paths)):
        raise ValueError("Duplicate Unity asset path")
    if any(len(path) >= 150 for path in paths):
        raise ValueError("Unity Asset Store filename limit exceeded")
    forbidden_extensions = (".dll", ".exe", ".apk", ".so", ".unitypackage", ".zip")
    if any(path.lower().endswith(forbidden_extensions) for path in paths):
        raise ValueError("External executable or nested archive present in the buyer package")
    missing = [p for p in REQUIRED if p not in paths]
    if missing:
        raise ValueError("Missing required demo/integration: " + repr(missing))
    for name in MODULES:
        base = ROOT + "Modules/com.hpr." + name + "/"
        if not any(p.startswith(base + "Runtime/") and p.endswith(".cs") for p in paths):
            raise ValueError("No runtime scripts for " + name)
        if base + "LICENSE.md" not in paths:
            raise ValueError("No module license for " + name)
    if any("/Tests/" in p or p.endswith("/Tests.meta") for p in paths):
        raise ValueError("Test assemblies leaked into buyer package")
    if any("/Modules/com.hpr." in p and ("/Demo/" in p or "/Editor/" in p)
           for p in paths):
        raise ValueError("Old standalone demos/editors leaked into the unified buyer release")
    readme = asset_contents.get(ROOT + "README.md", b"")
    if b"AI-assisted coding tools" not in readme or b"Dependency-free cleanroom compilation" not in readme:
        raise ValueError("Buyer README lacks AI disclosure or self-contained dependency guidance")
    if ROOT + "ThirdPartyNotices.md" not in paths:
        raise ValueError("Missing consolidated ThirdPartyNotices.md")
    editor_code = {path: body for path, body in asset_contents.items()
                   if "/Editor/" in path and path.endswith(".cs")}
    bad_paths = [path for path, body in editor_code.items() if b"Packages/com.hpr." in body]
    if bad_paths:
        raise ValueError("Buyer Editor code still expects obsolete UPM layout: " + repr(bad_paths))
    if len(editor_code) != 1 or ROOT + "Editor/HprGameplaySuiteSceneBuilder.cs" not in editor_code:
        raise ValueError("Buyer must contain only the integrated scene builder editor script")
    if any(b"UnityEngine.UI" in body for path, body in asset_contents.items() if path.endswith(".cs")):
        raise ValueError("Unexpected dependency on UnityEngine.UI in standalone buyer source")
    return {"asset_count": len(paths), "modules": len(MODULES), "root": ROOT,
            "scene": REQUIRED[0], "external_paths": 0, "tests_in_release": 0,
            "editor_scripts_checked": len(editor_code), "outdated_upm_path_references": 0,
            "ai_disclosure": True, "unity_gui_dependency_required": False}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.archive), indent=2))


if __name__ == "__main__":
    main()
