#!/usr/bin/env python3
"""Read-only format/manifest scope QA for a Unity .unitypackage archive."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
import tarfile

ROOT = "Assets/HPRGameplaySuite/"
REQUIRED = (
    ROOT + "Demo/GameplaySuiteShowcase.unity",
    ROOT + "Integration/HprGameplaySuitePlayground.cs",
    ROOT + "Editor/HprGameplaySuiteSceneBuilder.cs",
    ROOT + "README.md",
    ROOT + "LICENSE.md",
    ROOT + "QUICKSTART.md",
    ROOT + "ARCHITECTURE.md",
    ROOT + "Integration/HprSuiteIntegration.cs",
    ROOT + "Integration/HprSuiteSnapshot.cs",
    ROOT + "Integration/HprSuiteArenaMotor.cs",
    ROOT + "Integration/HprSuiteInput.cs",
    ROOT + "Editor/HprSuiteIntegrationGuide.cs",
    ROOT + "Editor/Styles/HprSuiteIntegrationGuide.uss",
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
        archive_guids = {}
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
            archive_guids[path] = m.name.split("/", 1)[0]
            if path.endswith((".cs", ".md", ".unity", ".asset", ".mat")):
                blob = t.extractfile(m.name.rsplit("/", 1)[0] + "/asset")
                if blob is not None:
                    asset_contents[path] = blob.read(2_000_000)
    if len(paths) != len(set(paths)):
        raise ValueError("Duplicate Unity asset path")
    if len(archive_guids) != len(set(archive_guids.values())):
        raise ValueError("Duplicate serialized Unity GUIDs detected in archive")
    authored_root = Path(__file__).resolve().parent / "buyer_source_assets"
    authored_metadata = sorted(authored_root.rglob("*.meta"))
    if len(authored_metadata) < 50:
        raise ValueError("Source-controlled Unity GUID baseline missing")
    for metadata in authored_metadata:
        relative = metadata.relative_to(authored_root)
        asset_path = "Assets/" + str(relative.with_suffix("")).replace("\\", "/")
        match = re.search(r"(?m)^guid:\s*([0-9a-f]{32})\s*$",
                          metadata.read_text(encoding="utf-8"))
        if match is None:
            raise ValueError("Authoring metadata has invalid GUID: " + str(relative))
        actual = archive_guids.get(asset_path)
        if actual != match.group(1):
            raise ValueError("Unstable buyer asset GUID: " + asset_path)

    # The archived Unity source scene, ScriptableObjects and materials must
    # contain the exact source-controlled YAML, not a regenerated imitation.
    authored_yaml = [
        asset for asset in authored_root.rglob("*")
        if asset.is_file() and asset.suffix in (".unity", ".asset", ".mat")
    ]
    if len(authored_yaml) < 20:
        raise ValueError("Incomplete checked-in sample/scene authoring source")
    for yaml_path in authored_yaml:
        asset_path = "Assets/" + yaml_path.relative_to(authored_root).as_posix()
        if asset_contents.get(asset_path) != yaml_path.read_bytes():
            raise ValueError("Exported authored Unity asset content changed: " + asset_path)
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
        module_readme = asset_contents.get(base + "README.md", b"")
        if (not module_readme.startswith(b"INTEGRATED SUITE INSTALLATION:") or
            b"## Installation" in module_readme or b"## Demo" in module_readme or
            b"## Samples" in module_readme):
            raise ValueError("Buyer module README describes unavailable standalone workflows: " + name)
    if any("/Tests/" in p or p.endswith("/Tests.meta") for p in paths):
        raise ValueError("Test assemblies leaked into buyer package")
    if any("/Modules/com.hpr." in p and ("/Demo/" in p or "/Editor/" in p)
           for p in paths):
        raise ValueError("Old standalone demos/editors leaked into the unified buyer release")
    readme = asset_contents.get(ROOT + "README.md", b"")
    if b"AI-assisted coding tools" not in readme or b"Dependency-free cleanroom compilation" not in readme:
        raise ValueError("Buyer README lacks AI disclosure or self-contained dependency guidance")
    for sample in ("TrainingKey", "RepairAbility", "PulseAbility", "TrainingWorldRegistry"):
        if ROOT + "Samples/" + sample + ".asset" not in paths:
            raise ValueError("Missing integrated data example: " + sample)
    if ROOT + "ThirdPartyNotices.md" not in paths:
        raise ValueError("Missing consolidated ThirdPartyNotices.md")
    editor_code = {path: body for path, body in asset_contents.items()
                   if "/Editor/" in path and path.endswith(".cs")}
    bad_paths = [path for path, body in editor_code.items() if b"Packages/com.hpr." in body]
    if bad_paths:
        raise ValueError("Buyer Editor code still expects obsolete UPM layout: " + repr(bad_paths))
    expected_editors = {
        ROOT + "Editor/HprGameplaySuiteSceneBuilder.cs",
        ROOT + "Editor/HprSuiteIntegrationGuide.cs",
    }
    if set(editor_code) != expected_editors:
        raise ValueError("Unexpected or missing buyer Editor scripts: " + repr(set(editor_code) ^ expected_editors))
    # UI Toolkit (UnityEngine.UIElements) is built into Unity; UGUI is optional.
    if any(b"using UnityEngine.UI;" in body or b"UnityEngine.UI." in body
           for path, body in asset_contents.items() if path.endswith(".cs")):
        raise ValueError("Unexpected dependency on UnityEngine.UI UGUI in standalone buyer source")
    return {"asset_count": len(paths), "modules": len(MODULES), "root": ROOT,
            "scene": REQUIRED[0], "external_paths": 0, "tests_in_release": 0,
            "editor_scripts_checked": len(editor_code), "outdated_upm_path_references": 0,
            "ai_disclosure": True, "unity_gui_dependency_required": False,
            "source_controlled_guids_verified": len(authored_metadata),
            "source_controlled_yaml_verified": len(authored_yaml)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.archive), indent=2))


if __name__ == "__main__":
    main()
