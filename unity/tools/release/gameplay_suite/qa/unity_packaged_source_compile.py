#!/usr/bin/env python3
"""Stage exact Unity .unitypackage C# for standalone API-only compilation.

The staged compiler never launches Unity Editor. Assembly-definition
isolation and Unity serialization remain untested by one offline C#
assembly; real Unity Editor compilation must be separately verified.

Input and output are create-only and GUID/source bytes are pinned.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import tarfile
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET

from unity_archive_policy import inspect_archive

PACKAGE_ROOT = "Assets/HPRGameplaySuite"
EDITOR_VERSION = re.compile(r"6000\.(\d+)\.(\d+)f(\d+)")


def stage(archive: Path, expected_sha: str, editor: Path, output: Path, *,
          new_input: bool = False, inputsystem_dll: Path | None = None) -> dict:
    archive = Path(archive)
    editor = Path(editor)
    output = Path(output)
    if (output.exists() or output.is_symlink()):
        raise FileExistsError("A unique offline source QA folder is required")
    if (not archive.is_file() or archive.is_symlink()
            or not isinstance(expected_sha, str)
            or not re.fullmatch(r"[0-9a-f]{64}", expected_sha)):
        raise ValueError("Explicit pinned non-symlink Unity .unitypackage required")
    original_bytes = archive.read_bytes()
    observed_sha = hashlib.sha256(original_bytes).hexdigest()
    if observed_sha != expected_sha:
        raise ValueError("The exact Unity package archive SHA-256 has changed")
    if inspect_archive(archive)["status"] != "PASS":
        raise ValueError("The original package failed structural Unity QA")
    if not editor.is_dir() or editor.is_symlink():
        raise ValueError("Exact installed Unity Editor directory required")
    version = editor.parent.name
    match = EDITOR_VERSION.fullmatch(version)
    if match is None:
        raise ValueError("Unexpected Unity Editor version directory name")
    managed = editor / "Data/Managed/UnityEngine"
    if managed.is_symlink() or not managed.is_dir():
        raise ValueError("Installed Unity managed API reference directory absent")
    references = sorted(managed.glob("Unity*.dll"))
    if not references or any(p.is_symlink() or not p.is_file() for p in references):
        raise ValueError("No safe Unity managed API assembly references found")
    if (output.resolve(strict=False).is_relative_to(editor.resolve()) or
            output.resolve(strict=False) == archive.resolve() or
            output.resolve(strict=False) == editor.resolve()):
        raise ValueError("The QA staging destination would mutate an installed Editor or archive")

    if new_input:
        if (inputsystem_dll is None or not Path(inputsystem_dll).is_file()
                or Path(inputsystem_dll).is_symlink()):
            raise ValueError("New Input System branch requires an explicit available Unity.InputSystem.dll")
        references.append(Path(inputsystem_dll))
    elif inputsystem_dll is not None:
        raise ValueError("InputSystem.dll must not be supplied for the Built-in-only source branch")

    # Load only tested HPR source entries. No source execution or tar extraction.
    with tarfile.open(archive, "r:gz") as tf:
        payloads = {}
        for member in tf:
            if not member.isfile():
                raise ValueError("Unexpected tar member type")
            stream = tf.extractfile(member)
            if stream is None or member.size > 33_554_432:
                raise ValueError("Unexpected Unity archive payload")
            payload = stream.read(member.size + 1)
            if len(payload) != member.size:
                raise ValueError("Short/oversized Unity archive payload")
            payloads[member.name] = payload
    sources = {}
    for entry, data in payloads.items():
        if not entry.endswith("/pathname"):
            continue
        name = data.decode("utf-8").strip()
        if not name.endswith(".cs"):
            continue
        pure = PurePosixPath(name)
        if (pure.is_absolute() or ".." in pure.parts or "\\" in name
                or not name.startswith(PACKAGE_ROOT + "/")):
            raise ValueError("Unexpected C# pathname in Unity package")
        guid = entry.split("/", 1)[0]
        body = payloads.get(guid + "/asset")
        if body is None or name in sources:
            raise ValueError("Missing or duplicate C# payload")
        sources[name] = body
    if not sources:
        raise ValueError("No HPR C# source files found in this package")

    symbols = ["UNITY_EDITOR"]
    if int(match.group(1)) >= 6:
        symbols.append("UNITY_6000_6_OR_NEWER")
    elif int(match.group(1)) >= 4:
        symbols.append("UNITY_6000_4_OR_NEWER")
    if new_input:
        symbols.append("ENABLE_INPUT_SYSTEM")
    project = ET.Element("Project", {"Sdk": "Microsoft.NET.Sdk"})
    settings = ET.SubElement(project, "PropertyGroup")
    for tag, text in {
        "OutputType": "Library",
        "TargetFramework": "net8.0",
        "ImplicitUsings": "disable",
        "Nullable": "disable",
        "EnableDefaultCompileItems": "false",
        "LangVersion": "latest",
        "DefineConstants": ";".join(symbols),
        "TreatWarningsAsErrors": "false",
    }.items():
        ET.SubElement(settings, tag).text = text
    members = ET.SubElement(project, "ItemGroup")
    for ref in references:
        item = ET.SubElement(members, "Reference", {"Include": ref.stem})
        ET.SubElement(item, "HintPath").text = str(ref)
        ET.SubElement(item, "Private").text = "false"
    for source in sorted(sources):
        ET.SubElement(members, "Compile", {"Include": str(output / "sources" / source)})
    ET.indent(project, space="  ")

    # Only now is the fresh, validated output directory created.
    output.mkdir(parents=True, mode=0o700)
    checksums = {}
    for name, body in sorted(sources.items()):
        dest = output / "sources" / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("xb") as stream:
            stream.write(body)
        checksums[name] = hashlib.sha256(body).hexdigest()
    ET.ElementTree(project).write(output / "hpr-package-compile.csproj", encoding="utf-8",
                                  xml_declaration=True)
    receipt = {
        "status": "PASS",
        "verification_level": "private_offline_api_only_not_unity_editor",
        "actual_unity_editor_executed": False,
        "archive_sha256": observed_sha,
        "source_file_count": len(sources),
        "source_file_sha256": checksums,
        "managed_api_editor": version,
        "reference_assembly_count": len(references),
        "new_input_system_branch": new_input,
        "no_commercial_release_approved": True,
    }
    (output / "SOURCE_MANIFEST.json").write_text(json.dumps(receipt, indent=2) + "\n")
    (output / "SOURCE_MANIFEST.json").chmod(0o600)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--expected-sha256", type=str, required=True)
    parser.add_argument("--editor", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--new-input", action="store_true")
    parser.add_argument("--inputsystem-dll", type=Path)
    args = parser.parse_args()
    try:
        result = stage(args.archive, args.expected_sha256, args.editor, args.out,
                       new_input=args.new_input,
                       inputsystem_dll=args.inputsystem_dll)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (ValueError, OSError, tarfile.TarError) as exc:
        print(json.dumps({"status": "ERROR", "type": type(exc).__name__,
                          "message": str(exc)[:250], "no_unity_editor_started": True}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
