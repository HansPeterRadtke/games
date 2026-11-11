#!/usr/bin/env python3
"""Stage exact HPR Unity-package C# into real asmdef-shaped offline assemblies.

The previous API check compiled all 55 scripts into one .NET assembly; that
conceals cross-assembly accessibility problems and omitted asmdef references.
This creates distinct .csproj files with precisely the package's ten runtime
asmdef dependencies, Assembly-CSharp integration and Assembly-CSharp-Editor.

It is NOT a native Unity Editor process, build/publish approval, or a way to
override resource-broker admission. It writes only to a unique private output.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import tarfile
from xml.etree import ElementTree as ET

from unity_archive_policy import read_package_members

ROOT = "Assets/HPRGameplaySuite"
MODULES = ROOT + "/Modules/"
INTEGRATION = ROOT + "/Integration/"
EDITOR = ROOT + "/Editor/"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def topological_assembly_order(graph: dict[str, list[str]]) -> list[str]:
    missing = {other for deps in graph.values() for other in deps if other not in graph}
    if missing:
        raise ValueError("missing declared Unity asmdef: " + ", ".join(sorted(missing)))
    visiting: set[str] = set()
    completed: set[str] = set()
    order: list[str] = []

    def visit(name: str) -> None:
        if name in visiting:
            raise ValueError("cyclic Unity asmdef references at: " + name)
        if name in completed:
            return
        visiting.add(name)
        for other in graph[name]:
            visit(other)
        visiting.remove(name)
        completed.add(name)
        order.append(name)

    for name in sorted(graph):
        visit(name)
    return order


def plan(archive: Path, expected_sha: str, staged: Path) -> dict:
    archive = Path(archive)
    staged = Path(staged)
    if not archive.is_file() or archive.is_symlink():
        raise ValueError("The exact non-symlink .unitypackage is required")
    if not re.fullmatch("[0-9a-f]{64}", expected_sha):
        raise ValueError("Wrong exact Unity private package checksum")
    data = read_package_members(archive, expected_sha=expected_sha)
    source_root = staged / "sources"
    manifest = staged / "SOURCE_MANIFEST.json"
    if (staged.is_symlink() or source_root.is_symlink() or
            not source_root.is_dir() or not manifest.is_file() or manifest.is_symlink()):
        raise ValueError("An exact previously staged QA source+manifest is required")
    detail = json.loads(manifest.read_text())
    if (detail.get("archive_sha256") != expected_sha or
            detail.get("verification_level") != "private_offline_api_only_not_unity_editor"):
        raise ValueError("Staged C# source provenance does not match chosen archive")
    source_sha = detail.get("source_file_sha256")
    if not isinstance(source_sha, dict) or not source_sha:
        raise ValueError("Staged source manifest is incomplete")
    for path, claimed_sha in source_sha.items():
        file = source_root / path
        if file.is_symlink() or not file.is_file() or not file.resolve().is_relative_to(source_root.resolve()):
            raise ValueError("Staged source file is missing or symlinked: " + path)
        if digest(file) != claimed_sha:
            raise ValueError("Staged source changed after original package import: " + path)

    entries: dict[str, str] = {}
    for member_name, body in data.items():
        if member_name.endswith("/pathname"):
            entries[body.decode("utf-8").rstrip("\r\n")] = member_name.split("/", 1)[0]

    definitions: dict[str, dict] = {}
    for path, guid in entries.items():
        if not path.endswith(".asmdef"):
            continue
        if not path.startswith(MODULES):
            raise ValueError("Unexpected non-runtime HPR assembly definition")
        raw = json.loads(data[guid + "/asset"])
        name = raw.get("name")
        refs = raw.get("references")
        if (not isinstance(name, str) or not name or name in definitions or
                not isinstance(refs, list) or not all(isinstance(r, str) for r in refs)):
            raise ValueError("Malformed/duplicate runtime asmdef graph")
        if raw.get("includePlatforms") or raw.get("excludePlatforms") or raw.get("defineConstraints"):
            raise ValueError("Unsupported platform-constrained asmdef for exact offline QA")
        if (raw.get("noEngineReferences") or raw.get("overrideReferences") or
                raw.get("allowUnsafeCode") or raw.get("autoReferenced") is False or
                raw.get("precompiledReferences") or raw.get("versionDefines") or
                raw.get("optionalUnityReferences")):
            # A future asmdef can change compiler semantics without changing
            # source paths. Refuse to produce a false-positive .NET compile
            # unless every Unity setting is reproduced by this QA harness.
            raise ValueError("unsupported Unity asmdef compiler settings in " + path)
        definitions[name] = {"path": path, "directory": path.rsplit("/", 1)[0],
                             "references": sorted(refs), "sources": []}

    topological = topological_assembly_order({
        name: item["references"] for name, item in definitions.items()
    })

    integration: list[str] = []
    editor: list[str] = []
    unclassified: list[str] = []
    for filename in source_sha:
        if filename.startswith(INTEGRATION):
            integration.append(filename)
        elif filename.startswith(EDITOR):
            editor.append(filename)
        else:
            found = [name for name, info in definitions.items()
                     if filename.startswith(info["directory"] + "/")]
            if len(found) != 1:
                unclassified.append(filename)
            else:
                definitions[found[0]]["sources"].append(filename)

    if unclassified or any(not item["sources"] for item in definitions.values()):
        raise ValueError("C# source is unassigned or duplicated across asmdef boundaries: " +
                         ", ".join(unclassified[:8]))
    assigned = [src for item in definitions.values() for src in item["sources"]] + integration + editor
    if len(assigned) != len(source_sha) or len(set(assigned)) != len(source_sha):
        raise ValueError("C# source assigned to multiple assemblies or omitted")
    return {
        "runtime": definitions,
        "runtime_topological_order": topological,
        "integration_sources": sorted(integration),
        "editor_sources": sorted(editor),
        "source_count": len(source_sha),
        "archive_sha256": expected_sha,
        "source_sha256": source_sha,
    }


def _csproj(name: str, sources: list[str], project_refs: list[Path],
            unity_dlls: list[Path], symbols: list[str], target: Path,
            source_root: Path) -> None:
    project = ET.Element("Project", {"Sdk": "Microsoft.NET.Sdk"})
    settings = ET.SubElement(project, "PropertyGroup")
    options = {"OutputType": "Library", "TargetFramework": "net8.0",
               "AssemblyName": name, "ImplicitUsings": "disable",
               "Nullable": "disable", "EnableDefaultCompileItems": "false",
               "LangVersion": "latest", "DefineConstants": ";".join(symbols),
               "TreatWarningsAsErrors": "false"}
    for key, value in options.items():
        ET.SubElement(settings, key).text = value
    items = ET.SubElement(project, "ItemGroup")
    for lib in sorted(unity_dlls):
        element = ET.SubElement(items, "Reference", {"Include": lib.stem})
        ET.SubElement(element, "HintPath").text = str(lib)
        ET.SubElement(element, "Private").text = "false"
    for dependency in sorted(project_refs):
        ET.SubElement(items, "ProjectReference", {"Include": str(dependency)})
    for source in sorted(sources):
        ET.SubElement(items, "Compile", {"Include": str(source_root / source)})
    ET.indent(project, space="  ")
    ET.ElementTree(project).write(target, encoding="utf-8", xml_declaration=True)


def stage(archive: Path, expected_sha: str, staged: Path, unity_editor: Path,
          output: Path, *, new_input: bool = False,
          input_dll: Path | None = None, player: bool = False,
          legacy_input: bool = False) -> dict:
    output = Path(output).absolute()
    editor = Path(unity_editor).absolute()
    if output.exists() or output.is_symlink():
        raise FileExistsError("Require a fresh unique offline C# project folder")
    if editor.is_symlink() or not editor.is_dir():
        raise ValueError("An installed Unity Editor API directory is required")
    api = editor / "Data/Managed/UnityEngine"
    if api.is_symlink() or not api.is_dir():
        raise ValueError("No installed Unity managed API assemblies")
    engine_refs = sorted(api.glob("UnityEngine.*.dll"))
    editor_refs = sorted(api.glob("UnityEditor.*.dll"))
    if not engine_refs or not editor_refs:
        raise ValueError("Installed Unity managed API references are incomplete")
    if any(f.is_symlink() or not f.is_file() for f in engine_refs + editor_refs):
        raise ValueError("Symlinked/missing Unity managed API reference")
    if new_input:
        if input_dll is None or not Path(input_dll).is_file() or Path(input_dll).is_symlink():
            raise ValueError("New-only input branch requires concrete Unity.InputSystem.dll")
    elif input_dll is not None:
        raise ValueError("An Input System DLL cannot be supplied to old-input build")
    if output.resolve(strict=False).is_relative_to(editor.resolve()):
        raise ValueError("Refusing to stage inside an installed Unity Editor")
    if output.resolve(strict=False).is_relative_to(Path(staged).resolve()):
        raise ValueError("Refusing to stage inside prior frozen C# source tree")
    if output.resolve(strict=False) == Path(archive).resolve():
        raise ValueError("Refusing to replace the original package archive")
    record = plan(archive, expected_sha, staged)
    version = editor.parent.name
    symbols = [] if player else ["UNITY_EDITOR"]
    if legacy_input:
        symbols.append("ENABLE_LEGACY_INPUT_MANAGER")
    if version.startswith("6000.6."):
        symbols.append("UNITY_6000_6_OR_NEWER")
    elif version.startswith("6000.4."):
        symbols.append("UNITY_6000_4_OR_NEWER")
    else:
        raise ValueError("Unsupported installed Unity Editor version for this QA fixture")

    output.mkdir(mode=0o700, parents=True)
    projects = output / "projects"
    projects.mkdir(mode=0o700)
    source_root = Path(staged).absolute() / "sources"
    runtime_names = set(record["runtime"])
    for name, info in record["runtime"].items():
        _csproj(name, info["sources"],
                [projects / (dep + ".csproj") for dep in info["references"]],
                engine_refs, symbols, projects / (name + ".csproj"), source_root)

    integration = "Assembly-CSharp"
    _csproj(integration, record["integration_sources"],
            [projects / (name + ".csproj") for name in runtime_names],
            engine_refs + ([Path(input_dll).absolute()] if new_input else []),
            symbols + (["ENABLE_INPUT_SYSTEM"] if new_input else []),
            projects / (integration + ".csproj"), source_root)
    if not player:
        _csproj("Assembly-CSharp-Editor", record["editor_sources"],
                [projects / (integration + ".csproj")] +
                [projects / (name + ".csproj") for name in runtime_names],
                engine_refs + editor_refs, symbols, projects / "Assembly-CSharp-Editor.csproj",
                source_root)

    audit = {
        "status": "PASS",
        "source_archive_sha256": expected_sha,
        "source_manifest_sha256": digest(Path(staged) / "SOURCE_MANIFEST.json"),
        "source_count": record["source_count"],
        "runtime_asmdefs": record["runtime"],
        "topological_compile_order": record["runtime_topological_order"] +
                                     [integration] + ([] if player else ["Assembly-CSharp-Editor"]),
        "projects_created": len(runtime_names) + 1 + (0 if player else 1),
        "scripts_included_once": record["source_count"] -
                                 (len(record["editor_sources"]) if player else 0),
        "editor_sources_excluded": len(record["editor_sources"]) if player else 0,
        "player_build": player,
        "new_input": new_input,
        "legacy_input_branch_compiled": legacy_input,
        "input_mode": ("both" if new_input and legacy_input else
                       "new_input_system" if new_input else
                       "legacy" if legacy_input else "disabled_fallback"),
        "unity_editor_apis": version,
        "actual_unity_editor_compilation_completed": False,
        "not_a_commercial_release": True,
    }
    with (output / "PROJECT_PLAN.json").open("x", encoding="utf-8") as stream:
        json.dump(audit, stream, indent=2, sort_keys=True)
        stream.write("\n")
    (output / "PROJECT_PLAN.json").chmod(0o600)
    return audit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--archive-sha", required=True)
    parser.add_argument("--source-staging", type=Path, required=True)
    parser.add_argument("--editor", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--new-input", action="store_true")
    parser.add_argument("--legacy-input", action="store_true",
                        help="compile the genuine ENABLE_LEGACY_INPUT_MANAGER branch")
    parser.add_argument("--player", action="store_true",
                        help="stage only runtime/module and Assembly-CSharp sources without UNITY_EDITOR")
    parser.add_argument("--input-dll", type=Path)
    args = parser.parse_args()
    try:
        result = stage(args.archive, args.archive_sha,
                       args.source_staging, args.editor, args.output,
                       new_input=args.new_input, input_dll=args.input_dll,
                       player=args.player, legacy_input=args.legacy_input)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, tarfile.TarError) as error:
        print(json.dumps({"status": "ERROR", "error": str(error)[:240],
                          "no_unity_process_started": True}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
