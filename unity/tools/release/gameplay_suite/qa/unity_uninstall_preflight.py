#!/usr/bin/env python3
"""Read-only inventory of customer dependencies on a Unity HPR package.

This tool NEVER uninstalls anything, edits a project, rewrites .meta files or
grants permission to remove a plugin. It is a conservative preflight for the
known SHA-pinned Unity .unitypackage, including after the HPR root was removed.

The only available classifications are:
- customer_dependencies_found: at least one specific use of HPR or its GUIDs.
- unknown_project_content_requires_review: cannot inspect every source file.
- no_direct_reference_detected: nothing observed in scanned files; it does
  NOT mean the game is safe to uninstall (binary runtime/reflection/etc).
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import re
import tarfile
from pathlib import Path, PurePosixPath

_GUID = re.compile(r"(?m)\bguid:\s*([0-9a-fA-F]{32})\b")
_HPR_CSHARP = re.compile(r"\b(?:using\s+(?:static\s+)?(?:global::)?HPR\b|HPR\.[A-Za-z_]|HPR\w*Runtime\b)")
_TEXT_SOURCE_EXTENSIONS = {
    ".asset", ".asmdef", ".asmref", ".controller", ".cs", ".json",
    ".mat", ".meta", ".overridecontroller", ".prefab", ".shader", ".unity", ".uxml",
    ".uss", ".yaml", ".yml", ".xml", ".playable", ".txt",
}
# Binary assets typically cannot refer to serialized Unity script GUIDs
# directly; uncertainty is still reported for other unknown file types.
_BINARY_MEDIA = {".png", ".jpg", ".jpeg", ".tga", ".wav", ".mp3", ".ogg", ".mp4", ".webm"}


def _relative_package_path(value: str) -> str:
    if "\\" in value:
        raise ValueError("Unexpected backslash in package asset path")
    path = PurePosixPath(value)
    if not path.parts or path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise ValueError("Unsafe package pathname")
    name = path.as_posix()
    # The root directory itself carries a stable Unity folder .meta GUID.
    # That pathname is valid alongside child assets in a genuine Unity export.
    if name != "Assets/HPRGameplaySuite" and (
        not name.startswith("Assets/HPRGameplaySuite/") or len(path.parts) < 3
    ):
        raise ValueError("Unexpected package root: " + name)
    return name


def _archive_guids(archive: Path) -> dict[str, str]:
    if not archive.is_file() or archive.is_symlink():
        raise FileNotFoundError(archive)
    found: dict[str, str] = {}
    with tarfile.open(archive, "r:gz") as package:
        for member in package:
            if not member.name.endswith("/pathname"):
                continue
            guid = member.name.removeprefix("./").removesuffix("/pathname")
            if not re.fullmatch(r"[0-9a-f]{32}", guid):
                raise ValueError("Invalid incoming vendor GUID")
            if member.size < 1 or member.size > 4096:
                raise ValueError("Unreasonable vendor pathname entry size")
            inp = package.extractfile(member)
            if inp is None:
                raise ValueError("No incoming vendor pathname data")
            try:
                path = _relative_package_path(inp.read(4097).decode("utf-8").strip())
            except UnicodeDecodeError as exc:
                raise ValueError("Invalid incoming package pathname encoding") from exc
            if guid in found or path in found.values():
                raise ValueError("Non-unique incoming vendor identity")
            found[guid] = path
    if not found:
        raise ValueError("No vendor GUIDs were found in the archive")
    return found


def _ensure_non_symlink_path(project: Path, relative: Path) -> Path:
    current = project
    for piece in relative.parts:
        current = current / piece
        if current.is_symlink():
            raise ValueError("Refusing to inspect symlinked Unity file/path: " + relative.as_posix())
    return current


def _read_package_json(path: Path, max_file_bytes: int) -> dict:
    """Bound the actual read too: metadata can grow after the size check."""
    with path.open("rb") as source:
        body = source.read(max_file_bytes + 1)
    if len(body) > max_file_bytes:
        raise ValueError("package metadata exceeded read limit during inspection")
    document = json.loads(body.decode("utf-8"))
    if not isinstance(document, dict):
        raise ValueError("package metadata must be a JSON object")
    return document


def _dependency_versions_valid(dependencies: object) -> bool:
    return isinstance(dependencies, dict) and all(
        isinstance(name, str) and bool(name.strip()) and
        isinstance(version, str) and bool(version.strip())
        for name, version in dependencies.items()
    )


def inspect(project: Path, archive: Path, *, max_file_bytes: int = 8_388_608,
            max_scanned_paths: int = 200_000) -> dict:
    """Inspect one existing local Unity project without changing any file.

    project: existing Unity project root; archive: known local HPR .unitypackage
    (requires exact source identity for reference matching even when uninstalled);
    Assets, embedded Packages and ProjectSettings are all included.
    max_file_bytes: finite positive byte ceiling to avoid opening huge files;
    max_scanned_paths: one shared positive traversal ceiling across those roots.
    Results are conservative; no finding is deletion approval.
    """
    project = Path(project)
    if project.is_symlink() or not project.is_dir() or not (project / "Assets").is_dir():
        raise ValueError("Existing non-symlink Unity project with Assets directory required")
    if isinstance(max_file_bytes, bool) or not isinstance(max_file_bytes, int) or max_file_bytes <= 0:
        raise ValueError("max_file_bytes must be a positive integer")
    if isinstance(max_scanned_paths, bool) or not isinstance(max_scanned_paths, int) or max_scanned_paths <= 0:
        raise ValueError("max_scanned_paths must be a positive integer")
    _ensure_non_symlink_path(project, Path("Assets"))
    vendor = _archive_guids(Path(archive))
    # Distinguish the product's ACTUAL vendor module package identities from
    # customer-created packages sharing a com.hpr.* prefix. The old prefix
    # test silently ignored such customer code and .asmrefs.
    vendor_module_ids = {
        bits[3] for name in vendor.values()
        if len(bits := name.split("/")) > 4 and
        bits[:3] == ["Assets", "HPRGameplaySuite", "Modules"]
    }
    dependencies: list[dict[str, str]] = []
    unknowns: list[dict[str, str]] = []
    checked = 0
    customer_root = project / "Assets"
    package_root = project / "Packages"
    settings_root = project / "ProjectSettings"
    if settings_root.is_symlink() or (settings_root.exists() and not settings_root.is_dir()):
        raise ValueError("Refusing symlinked or non-directory Unity ProjectSettings root")
    if package_root.is_symlink() or (package_root.exists() and not package_root.is_dir()):
        raise ValueError("Refusing symlinked or non-directory Unity Packages root")
    # In addition to Assets, project-embedded UPM packages can contain
    # customer-authored C#/asmdefs/asmrefs directly under Packages/com.foo.
    # Exclude Unity's resolved Library/PackageCache and the HPR package's
    # own source; do not confuse embedded package source with a manifest.
    embedded = package_root.rglob("*") if package_root.is_dir() else ()
    settings = settings_root.rglob("*") if settings_root.is_dir() else ()

    # Stream all three roots under ONE bounded traversal budget, never following
    # package paths outside this project or silently omitting embedded source.
    examined_paths = 0
    for path in itertools.chain(customer_root.rglob("*"), embedded, settings):
        examined_paths += 1
        if examined_paths > max_scanned_paths:
            unknowns.append({"path": "Assets, Packages and ProjectSettings",
                             "reason": "file traversal limit reached; remaining customer assets, embedded packages and project settings were not inspected"})
            break
        relative = path.relative_to(project)
        name = relative.as_posix()
        # Check even vendor-root symlinks, rather than ignoring an unsafe path.
        if path.is_symlink():
            raise ValueError("Refusing symlinked Unity project asset: " + name)
        if path.is_dir() or name == "Assets/HPRGameplaySuite.meta":
            continue
        if name.startswith("Assets/HPRGameplaySuite/"):
            continue
        if name in ("Packages/manifest.json", "Packages/packages-lock.json"):
            continue  # They are separately parsed below, with schema checks.
        if name.startswith("Packages/") and name.split("/")[1] in vendor_module_ids:
            continue  # HPR's own embedded source is not a customer consumer.
        if not path.is_file():
            unknowns.append({"path": name, "reason": "unsupported asset type"})
            continue
        # Customer-owned importer .meta files can themselves contain GUID
        # references to vendor shaders/materials/MonoScripts. Inspect them,
        # while skipping only the HPR vendor package's own root .meta.
        extension = path.suffix.lower()
        if extension in _BINARY_MEDIA:
            # Reference to a texture is serialized in the consumer's .unity/.asset YAML.
            continue
        if extension not in _TEXT_SOURCE_EXTENSIONS:
            unknowns.append({"path": name, "reason": "unknown source or binary asset type"})
            continue
        if path.stat().st_size > max_file_bytes:
            unknowns.append({"path": name, "reason": "asset exceeds configured read limit"})
            continue
        # Read no more than the configured byte ceiling, even if a file is
        # replaced or grows after its preflight stat check.
        with path.open("rb") as source:
            body = source.read(max_file_bytes + 1)
        if len(body) > max_file_bytes:
            unknowns.append({"path": name, "reason": "asset exceeded read limit during inspection"})
            continue
        if b"\0" in body:
            unknowns.append({"path": name, "reason": "binary content despite text extension"})
            continue
        try:
            source = body.decode("utf-8")
        except UnicodeDecodeError:
            unknowns.append({"path": name, "reason": "non-UTF8 text, cannot prove no references"})
            continue
        checked += 1
        if (extension == ".json" and len(relative.parts) == 3 and
            relative.parts[0] == "Packages" and relative.parts[-1] == "package.json"):
            # Embedded packages need not appear in the project's top-level
            # manifest, but their OWN package.json declares indirect HPR
            # dependencies. Scan that dependency graph before uninstall.
            try:
                package_info = json.loads(source)
                if not isinstance(package_info, dict):
                    raise ValueError("embedded package manifest must be a JSON object")
                dependencies_map = package_info.get("dependencies", {})
                if (not isinstance(dependencies_map, dict) or
                    any(not isinstance(key, str) or not key.strip() or
                        not isinstance(version, str) or not version.strip()
                        for key, version in dependencies_map.items())):
                    raise ValueError("invalid embedded package dependency list")
                if any(key.startswith("com.hpr.") for key in dependencies_map):
                    dependencies.append({
                        "kind": "embedded_package_manifest_reference", "path": name,
                        "reason": "embedded customer package declares a transitive HPR package dependency",
                    })
            except (ValueError, TypeError):
                unknowns.append({"path": name,
                                 "reason": "invalid embedded package manifest JSON/dependency schema"})
                continue
        direct = sorted({match.group(1).lower() for match in _GUID.finditer(source)})
        for guid in direct:
            if guid in vendor:
                dependencies.append({
                    "kind": ("project_settings_vendor_guid" if relative.parts[0] == "ProjectSettings"
                             else "importer_meta_vendor_guid" if extension == ".meta"
                             else "serialized_vendor_guid"),
                    "path": name,
                    "vendor_asset": vendor[guid],
                    "guid": guid,
                })
        if extension == ".cs" and _HPR_CSHARP.search(source):
            dependencies.append({"kind": "csharp_hpr_reference", "path": name,
                                 "reason": "C# source contains HPR API/namespace token"})
        if extension in (".asmdef", ".asmref"):
            try:
                parsed = json.loads(source)
                if not isinstance(parsed, dict):
                    raise ValueError("Unity assembly definition/reference must be a JSON object")
                if extension == ".asmref":
                    # Unity .asmref files have ONE required `reference` string,
                    # not the .asmdef `references` array. Both GUID:<32hex>
                    # and assembly-name forms are permitted by Unity's
                    # first-party Assembly Definition File Format reference.
                    reference = parsed.get("reference")
                    if not isinstance(reference, str) or not reference.strip():
                        raise ValueError("invalid required asmref reference")
                    if reference.startswith("GUID:") and not re.fullmatch(
                            r"GUID:[a-fA-F0-9]{32}", reference):
                        raise ValueError("invalid asmref assembly GUID")
                    if (reference.startswith("HPR.") or
                        (reference.startswith("GUID:") and reference[5:].lower() in vendor)):
                        dependencies.append({"kind": "asmref_reference", "path": name,
                                             "reason": "assembly reference pulls customer scripts into HPR's runtime assembly"})
                else:
                    entries = parsed.get("references", [])
                    if not isinstance(entries, list) or any(
                        not isinstance(ref, str) or not ref.strip() or
                        (ref.startswith("GUID:") and not re.fullmatch(
                            r"GUID:[a-fA-F0-9]{32}", ref)) for ref in entries
                    ):
                        raise ValueError("invalid asmdef reference list")
                    if any(ref.startswith("HPR.") or
                           ref.startswith("GUID:") and ref[5:].lower() in vendor
                           for ref in entries):
                        dependencies.append({"kind": "asmdef_reference", "path": name,
                                             "reason": "assembly definition names HPR or its GUID"})
            except (ValueError, TypeError):
                unknowns.append({"path": name,
                                 "reason": "invalid " + extension[1:] + " JSON/reference schema"})
    manifest = project / "Packages/manifest.json"
    _ensure_non_symlink_path(project, Path("Packages")) if (project / "Packages").exists() else None
    if manifest.exists():
        _ensure_non_symlink_path(project, Path("Packages/manifest.json"))
        if manifest.stat().st_size > max_file_bytes:
            unknowns.append({"path": "Packages/manifest.json", "reason": "manifest too large"})
        else:
            try:
                doc = _read_package_json(manifest, max_file_bytes)
                declared = doc.get("dependencies", {})
                if not _dependency_versions_valid(declared):
                    raise ValueError("dependency names and versions must be nonempty strings")
                if any(key.startswith("com.hpr.") for key in declared):
                    dependencies.append({"kind": "package_manifest_reference",
                                         "path": "Packages/manifest.json",
                                         "reason": "an HPR UPM module is still installed"})
                checked += 1
            except (ValueError, UnicodeDecodeError) as exc:
                unknowns.append({"path": "Packages/manifest.json",
                                 "reason": "unreadable package manifest: " + str(exc)})
    # Unity's resolved lock can retain package identities after manifest edits.
    # Never silently ignore that dependency evidence when planning uninstall.
    lock = project / "Packages/packages-lock.json"
    if lock.exists():
        _ensure_non_symlink_path(project, Path("Packages/packages-lock.json"))
        if lock.stat().st_size > max_file_bytes:
            unknowns.append({"path": "Packages/packages-lock.json", "reason": "package lock too large"})
        else:
            try:
                doc = _read_package_json(lock, max_file_bytes)
                resolved = doc.get("dependencies", {})
                if not isinstance(resolved, dict):
                    raise ValueError("resolved dependencies must be a JSON object")
                for name, entry in resolved.items():
                    if (not isinstance(name, str) or not name.strip() or
                            not isinstance(entry, dict) or
                            not isinstance(entry.get("version"), str) or
                            not entry["version"].strip() or
                            not _dependency_versions_valid(entry.get("dependencies", {}))):
                        raise ValueError("invalid resolved package version/dependency schema")
                if (any(name.startswith("com.hpr.") for name in resolved) or
                        any(name.startswith("com.hpr.")
                            for entry in resolved.values()
                            for name in entry.get("dependencies", {}))):
                    dependencies.append({"kind": "package_lock_reference",
                                         "path": "Packages/packages-lock.json",
                                         "reason": "resolved lock still references an HPR module directly or transitively"})
                checked += 1
            except (ValueError, UnicodeDecodeError) as exc:
                unknowns.append({"path": "Packages/packages-lock.json",
                                 "reason": "unreadable package lock: " + str(exc)})
    # Operator-facing next actions are advisory only. None performs a mutation
    # or treats the result as permission to remove a dependency.
    review_by_kind = {
        "project_settings_vendor_guid": "Review the cited Project Settings file in Unity, including build scenes, graphics and quality references. Preserve original settings/GUIDs and explicitly migrate and test a separate project copy before considering uninstall.",
        "serialized_vendor_guid": "Review each customer-owned scene, prefab or asset in the Unity Editor. On a new copy, explicitly migrate components and references, then verify Play mode before considering package removal.",
        "importer_meta_vendor_guid": "Review customer-owned Unity importer .meta references and their externalObjects in the Unity Editor. Preserve original GUID identities and test a separately copied project before any migration.",
        "csharp_hpr_reference": "Review customer C# HPR API calls with the source owner. Migrate code explicitly and recompile; do not automatically rewrite or remove source.",
        "asmdef_reference": "Review customer assembly definition dependencies and compile consumers after any user-approved migration; retain the original assembly and .meta identities until verified.",
        "asmref_reference": "Review customer Unity Assembly Definition Reference (.asmref) assets in the Inspector. Those scripts compile into the referenced HPR assembly, so migrate their assembly membership and recompile on a separate copy before uninstall.",
        "package_manifest_reference": "Review the project's declared HPR package dependencies with the owner before changing the Unity package manifest.",
        "package_lock_reference": "Review the existing resolved Unity package lock entry and the manifest together; do not silently edit project package resolution.",
        "embedded_package_manifest_reference": "Review customer embedded Packages/com.* package.json dependencies with the package owner. Unity loads embedded packages even when they are absent from the project manifest; migrate HPR dependency and verify Package Manager resolution before uninstall.",
    }
    used = {item["kind"] for item in dependencies}
    actions = [review_by_kind[kind] for kind in sorted(used) if kind in review_by_kind]
    if unknowns:
        actions.append("Review the unknown customer files in Unity or with the owning developer; absence of parsed references is not proof of safe removal.")
    if not actions:
        actions.append("No direct references found in checked files. Obtain explicit project-owner approval and separately test a clone before any uninstall; indirect references may remain.")
    dependencies.sort(key=lambda entry: (entry["path"], entry["kind"]))
    unknowns.sort(key=lambda entry: (entry["path"], entry["reason"]))
    # Root-specific direct reference findings take precedence over conservative unknown files.
    classification = ("customer_dependencies_found" if dependencies
                      else "unknown_project_content_requires_review" if unknowns
                      else "no_direct_reference_detected")
    return {
        "classification": classification,
        "read_only": True,
        "deletion_permitted": False,
        "warnings": ["Absence of direct references is never proof that uninstall is safe.",
                     "Reflection, binary formats, externally resolved packages, and dynamically generated scenes require review."],
        "archived_vendor_guid_count": len(vendor),
        "checked_text_files": checked,
        "examined_asset_paths": examined_paths,
        "configured_max_scanned_paths": max_scanned_paths,
        "dependencies": dependencies,
        "unknowns": unknowns,
        "review_actions": actions,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--max-file-bytes", type=int, default=8_388_608)
    parser.add_argument("--max-scanned-paths", type=int, default=200_000)
    parser.add_argument("--output", type=Path, help="new JSON report outside Unity project; will not overwrite")
    options = parser.parse_args()
    try:
        result = inspect(options.project, options.archive,
                         max_file_bytes=options.max_file_bytes,
                         max_scanned_paths=options.max_scanned_paths)
        raw = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if options.output is not None:
            if options.output.resolve().is_relative_to(options.project.resolve()):
                raise ValueError("Refusing to write a report inside the customer project")
            with options.output.open("x", encoding="utf-8") as dst:
                dst.write(raw)
        print(raw, end="")
        return 2 if result["classification"] != "no_direct_reference_detected" else 0
    except (ValueError, OSError, tarfile.TarError) as exc:
        print(json.dumps({"classification": "error", "deletion_permitted": False,
                          "read_only": True, "reason": str(exc)}))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
