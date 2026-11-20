#!/usr/bin/env python3
"""Read-only format/manifest scope QA for a Unity .unitypackage archive."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

ROOT = "Assets/HPRGameplaySuite/"
SOURCE_DIR = Path(__file__).resolve().parent
EDITOR_SOURCES = {
    ROOT + "Editor/HprGameplaySuiteSceneBuilder.cs": SOURCE_DIR / "HprGameplaySuiteSceneBuilder.cs",
    ROOT + "Editor/HprSuiteIntegrationGuide.cs": SOURCE_DIR / "HprSuiteIntegrationGuide.cs",
    ROOT + "Editor/HprSelectedAbilityInstaller.cs": (
        SOURCE_DIR / "buyer_source_assets/HPRGameplaySuite/Editor/HprSelectedAbilityInstaller.cs"
    ),
}
REQUIRED = (
    ROOT + "Demo/GameplaySuiteShowcase.unity",
    ROOT + "Integration/HprGameplaySuitePlayground.cs",
    ROOT + "README.md",
    ROOT + "LICENSE.md",
    ROOT + "QUICKSTART.md",
    ROOT + "ARCHITECTURE.md",
    ROOT + "Integration/HprSuiteIntegration.cs",
    ROOT + "Integration/HprSuiteSnapshot.cs",
    ROOT + "Integration/HprSuiteArenaMotor.cs",
    ROOT + "Integration/HprSuiteInput.cs",
    *EDITOR_SOURCES,
    ROOT + "Editor/Styles/HprSuiteIntegrationGuide.uss",
)
MODULES = (
    "eventbus", "composition", "save", "stats", "inventory", "interaction",
    "abilities", "weapons", "ai", "world",
)


def validate_editor_sources(editor_code: dict[str, bytes]) -> None:
    different = editor_code.keys() ^ EDITOR_SOURCES.keys()
    if different:
        raise ValueError("Unexpected or missing buyer Editor scripts: " + repr(sorted(different)))
    for path, source in EDITOR_SOURCES.items():
        if editor_code[path] != source.read_bytes():
            raise ValueError("Exported Editor script differs from release source: " + path)


def validate_runtime_sources(contents: dict[str, bytes]) -> int:
    suffixes = (".cs", ".asmdef", ".asmref")
    packages = SOURCE_DIR.parents[2] / "packages"
    expected = {}
    for name in MODULES:
        package = packages / ("com.hpr." + name)
        for source in (package / "Runtime").rglob("*"):
            if source.is_file() and source.suffix in suffixes:
                key = ROOT + "Modules/" + package.name + "/" + source.relative_to(package).as_posix()
                expected[key] = source
    for path in REQUIRED:
        if path.startswith(ROOT + "Integration/") and path.endswith(suffixes):
            expected[path] = SOURCE_DIR / Path(path).name
    actual = {path for path in contents if path.endswith(suffixes) and path not in EDITOR_SOURCES}
    different = actual ^ expected.keys()
    if different:
        raise ValueError("Unexpected or missing runtime source: " + repr(sorted(different)))
    for path, source in expected.items():
        if contents[path] != source.read_bytes():
            raise ValueError("Exported runtime source differs from release source: " + path)
    return len(expected)


def authored_guid(metadata: Path) -> str:
    match = re.search(r"(?m)^guid:\s*([0-9a-f]{32})\s*$", metadata.read_text(encoding="utf-8"))
    if match is None:
        raise ValueError("Authoring metadata has invalid GUID: " + str(metadata))
    return match.group(1)


def inspect(archive: Path) -> dict:
    if not archive.is_file() or archive.stat().st_size < 4096:
        raise ValueError("Missing or trivial archive")
    from qa.unity_archive_policy import read_package_members

    members = read_package_members(archive)
    paths = []
    archive_guids = {}
    asset_contents = {}
    for key, raw in members.items():
        guid, field = key.split("/", 1)
        if field != "pathname":
            continue
        path = raw.decode("utf-8").rstrip("\r\n")
        paths.append(path)
        archive_guids[path] = guid
        if guid + "/asset" in members:
            asset_contents[path] = members[guid + "/asset"]
    if len(paths) != len(set(paths)):
        raise ValueError("Duplicate Unity asset path")
    if len(archive_guids) != len(set(archive_guids.values())):
        raise ValueError("Duplicate serialized Unity GUIDs detected in archive")
    authored_root = Path(__file__).resolve().parent / "buyer_source_assets"
    metadata = {
        "Assets/" + meta.relative_to(authored_root).with_suffix("").as_posix(): meta
        for meta in authored_root.rglob("*.meta")
    }
    if len(metadata) < 50:
        raise ValueError("Source-controlled Unity GUID baseline missing")
    for module in MODULES:
        name = "com.hpr." + module
        package = SOURCE_DIR.parents[2] / "packages" / name
        files = list((package / "Runtime").rglob("*.meta"))
        for item in ("Runtime", "README.md", "LICENSE.md", "ThirdPartyNotices.md", "CHANGELOG.md"):
            meta = package / (item + ".meta")
            if meta.is_file():
                files.append(meta)
        for meta in files:
            relative = meta.relative_to(package).with_suffix("").as_posix()
            metadata[ROOT + "Modules/" + name + "/" + relative] = meta
    different = archive_guids.keys() ^ metadata.keys()
    if different:
        raise ValueError("Unexpected or missing buyer asset paths: " + repr(sorted(different)))
    for path, meta in metadata.items():
        if archive_guids[path] != authored_guid(meta):
            raise ValueError("Unstable buyer asset GUID: " + path)

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
    validate_editor_sources(editor_code)
    runtime_sources = validate_runtime_sources(asset_contents)
    # UI Toolkit (UnityEngine.UIElements) is built into Unity; UGUI is optional.
    if any(b"using UnityEngine.UI;" in body or b"UnityEngine.UI." in body
           for path, body in asset_contents.items() if path.endswith(".cs")):
        raise ValueError("Unexpected dependency on UnityEngine.UI UGUI in standalone buyer source")
    return {"asset_count": len(paths), "modules": len(MODULES), "root": ROOT,
            "scene": REQUIRED[0], "external_paths": 0, "tests_in_release": 0,
            "editor_scripts_checked": len(editor_code), "runtime_sources_checked": runtime_sources, "outdated_upm_path_references": 0,
            "ai_disclosure": True, "unity_gui_dependency_required": False,
            "source_controlled_guids_verified": len(metadata),
            "source_controlled_yaml_verified": len(authored_yaml)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.archive), indent=2))


if __name__ == "__main__":
    main()
