#!/usr/bin/env python3
"""Original, offline, fail-closed Unity assembly-definition preflight.

Static *saved-file* evidence only. Never invokes Unity, builds a Player,
resolves remote Registry packages, or changes project files.
"""
from __future__ import annotations
import argparse
import hashlib
import html
import json
import os
from pathlib import Path
import re
import stat
import sys

MAX_FILES = 3000
MAX_BYTES_PER_FILE = 1024 * 1024
MAX_TOTAL_BYTES = 32 * 1024 * 1024
MAX_FINDINGS = 3000
GUID_RE = re.compile(rb"(?m)^guid:\s*([0-9a-fA-F]{32})\s*$")
GUID_REF = re.compile(r"^GUID:([0-9a-fA-F]{32})$")
SCHEMA = "hpr-assembly-preflight/v1"


class Incomplete(Exception):
    """An input could not be inspected safely or completely."""


def _read_regular(path: Path, maximum: int) -> bytes:
    """Read a bounded regular file without following a final symlink."""
    if path.is_symlink():
        raise Incomplete("Linked input: " + str(path))
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        fd = os.open(path, flags)
    except OSError as error:
        raise Incomplete("Cannot open regular input: " + str(path)) from error
    try:
        start = os.fstat(fd)
        if not stat.S_ISREG(start.st_mode) or not 0 <= start.st_size <= maximum:
            raise Incomplete("Input is not a bounded regular file: " + str(path))
        with os.fdopen(os.dup(fd), "rb") as src:
            data = src.read(maximum + 1)
        end = os.fstat(fd)
        if len(data) != start.st_size or len(data) > maximum or (
            start.st_dev, start.st_ino, start.st_size, start.st_mtime_ns,
        ) != (end.st_dev, end.st_ino, end.st_size, end.st_mtime_ns):
            raise Incomplete("Input changed while reading: " + str(path))
        return data
    finally:
        os.close(fd)


def _json_unique(blob: bytes, path: Path) -> dict:
    def pairs(items):
        d = {}
        for key, value in items:
            if key in d:
                raise Incomplete("Duplicate JSON key in " + str(path) + ": " + key)
            d[key] = value
        return d
    try:
        obj = json.loads(blob.decode("utf-8-sig"), object_pairs_hook=pairs)
    except (UnicodeError, ValueError, TypeError, RecursionError) as error:
        raise Incomplete("Invalid JSON in " + str(path)) from error
    if not isinstance(obj, dict):
        raise Incomplete("Assembly JSON must be an object: " + str(path))
    return obj


def _file_roots(project: Path) -> list[Path]:
    if project.is_symlink() or not project.is_dir():
        raise Incomplete("Project path must be a real directory")
    assets = project / "Assets"
    version = project / "ProjectSettings" / "ProjectVersion.txt"
    if not assets.is_dir() or assets.is_symlink() or not version.is_file():
        raise Incomplete("Missing saved Unity Assets or ProjectSettings/ProjectVersion.txt")
    _read_regular(version, 32768)
    roots = [assets]
    packages = project / "Packages"
    if packages.exists():
        if packages.is_symlink() or not packages.is_dir():
            raise Incomplete("Packages path is not a real directory")
        for item in sorted(packages.iterdir()):
            if item.is_symlink():
                raise Incomplete("Linked embedded package directory: " + str(item))
            manifest = item / "package.json"
            if item.is_dir() and manifest.is_symlink():
                raise Incomplete("Linked embedded package manifest: " + str(manifest))
            if item.is_dir() and manifest.is_file():
                roots.append(item)
            if len(roots) > 129:
                raise Incomplete("Too many embedded package roots")
    return roots


def _walk_sources(root: Path, project: Path) -> list[Path]:
    result = []
    for directory, names, files in os.walk(root, topdown=True, followlinks=False):
        names.sort()
        files.sort()
        for name in names:
            p = Path(directory) / name
            if p.is_symlink():
                raise Incomplete("Linked directory under source root: " + str(p))
        for filename in files:
            path = Path(directory) / filename
            if path.is_symlink():
                raise Incomplete("Linked file under source root: " + str(path))
            if path.suffix.lower() in (".asmdef", ".asmref"):
                if not path.is_relative_to(project):
                    raise Incomplete("Unexpected input outside Unity project")
                result.append(path)
                if len(result) > MAX_FILES:
                    raise Incomplete("Too many saved assembly files")
    return result


def _guid_for(file: Path, embedded: bool) -> tuple[str | None, bool]:
    meta = Path(str(file) + ".meta")
    if not meta.exists():
        if embedded:
            # Packages may legitimately rely on generated metadata; no stable
            # GUID inference is allowed when this evidence is missing.
            return None, True
        raise Incomplete("Missing .meta file for asset-defined assembly: " + str(file))
    match = GUID_RE.search(_read_regular(meta, 128 * 1024))
    if match is None:
        raise Incomplete("Invalid assembly metadata GUID: " + str(meta))
    return match.group(1).decode("ascii").lower(), False


def _references(value, path: Path, field: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(x, str) for x in value):
        raise Incomplete("Expected string array '" + field + "' in " + str(path))
    if len(value) > 4096:
        raise Incomplete("Excessive references in " + str(path))
    return value


def inspect(project_path: Path) -> dict:
    project = Path(project_path)
    roots = _file_roots(project)
    files = sorted({p for root in roots for p in _walk_sources(root, project)})
    findings = []
    assemblies = []
    references = []
    total = 0

    def add(severity: str, code: str, path: str, explanation: str):
        if len(findings) >= MAX_FINDINGS:
            raise Incomplete("Too many findings; result would be truncated")
        findings.append({"severity": severity, "code": code, "path": path,
                         "explanation": explanation})

    for file in files:
        relative = file.relative_to(project).as_posix()
        source = _read_regular(file, MAX_BYTES_PER_FILE)
        total += len(source)
        if total > MAX_TOTAL_BYTES:
            raise Incomplete("Assembly source exceeds aggregate read limit")
        raw = _json_unique(source, file)
        guid, generated = _guid_for(file, relative.startswith("Packages/"))
        kind = file.suffix.lower()
        if kind == ".asmdef":
            name = raw.get("name")
            if not isinstance(name, str) or not name.strip() or len(name) > 256:
                raise Incomplete("Assembly definition has invalid name: " + relative)
            refs = _references(raw.get("references"), file, "references")
            constraints = _references(raw.get("defineConstraints"), file, "defineConstraints")
            includes = _references(raw.get("includePlatforms"), file, "includePlatforms")
            excludes = _references(raw.get("excludePlatforms"), file, "excludePlatforms")
            if includes and excludes:
                add("REVIEW", "CONFLICTING_PLATFORM_FILTERS", relative,
                    "Both includePlatforms and excludePlatforms contain entries; check the Unity Inspector.")
            if "UNITY_INCLUDE_TESTS" in constraints and "/Test" not in "/" + relative:
                add("REVIEW", "TEST_ONLY_CONSTRAINT", relative,
                    "UNITY_INCLUDE_TESTS can exclude production assemblies from normal Player builds.")
            if len(refs) != len(set(refs)):
                add("REVIEW", "REPEATED_ASSEMBLY_REFERENCE", relative,
                    "The same assembly reference appears more than once.")
            if generated:
                add("REVIEW", "EMBEDDED_GUID_UNKNOWN", relative,
                    "Embedded package asmdef has no saved .meta GUID; GUID references cannot be certified.")
            assemblies.append({"path": relative, "name": name, "guid": guid,
                               "constraints": constraints, "references": refs,
                               "include_platforms": includes, "exclude_platforms": excludes})
            references.extend((relative, ref) for ref in refs)
        else:
            reference = raw.get("reference")
            if not isinstance(reference, str) or not reference:
                raise Incomplete("Assembly reference has missing target: " + relative)
            if generated:
                add("REVIEW", "EMBEDDED_GUID_UNKNOWN", relative,
                    "Embedded package asmref has no saved .meta GUID.")
            references.append((relative, reference))

    names = {}
    guids = {}
    for row in assemblies:
        names.setdefault(row["name"], []).append(row["path"])
        if row["guid"]:
            guids.setdefault(row["guid"], []).append(row["path"])
    for name, paths in sorted(names.items()):
        if len(paths) > 1:
            for path in paths:
                add("FAIL", "DUPLICATE_ASSEMBLY_NAME", path,
                    "Assembly '" + name + "' occurs in multiple local saved definitions: " + ", ".join(paths))
    for guid, paths in sorted(guids.items()):
        if len(paths) > 1:
            for path in paths:
                add("FAIL", "DUPLICATE_ASMDEF_GUID", path,
                    "Repeated GUID across saved local assembly definitions: " + guid)
    for source, reference in references:
        match = GUID_REF.fullmatch(reference)
        if match:
            if match.group(1).lower() not in guids:
                add("REVIEW", "UNRESOLVED_GUID_REFERENCE", source,
                    "Referenced GUID not found in scanned local assemblies: " + reference +
                    ". It may belong to a registry package; no automatic fix is safe.")
        elif reference not in names:
            add("REVIEW", "UNRESOLVED_NAME_REFERENCE", source,
                "Referenced assembly not found in scanned local definitions: " + reference +
                ". It may belong to a registry package or precompiled library.")
    if not assemblies:
        add("REVIEW", "NO_LOCAL_ASMDEF", "Assets",
            "No .asmdef files discovered in saved Assets or embedded packages; runtime compilation is not certified.")
    findings.sort(key=lambda item: (item["path"], item["code"], item["explanation"]))
    critical = sum(row["severity"] == "FAIL" for row in findings)
    result = {"schema": SCHEMA,
              "status": "FAIL" if critical else "REVIEW" if findings else "CLEAR_WITH_LIMITS",
              "project": str(project), "asmdef_count": len(assemblies),
              "asmref_count": len(files) - len(assemblies),
              "embedded_roots_scanned": len(roots) - 1,
              "bytes_read_from_assembly_json": total,
              "findings": findings,
              "coverage": "Saved Assets and embedded Packages folder asmdef/asmref JSON only",
              "limitations": ["No remote Unity Registry/PackageCache resolution",
                              "No real Unity compilation, Player build, or final symbol evaluation",
                              "No unsaved Editor state, platform build or global project define evaluation",
                              "Review unresolved external references; never auto-remove references"]}
    return result


def render_html(report: dict) -> str:
    esc = lambda value: html.escape(str(value), quote=True)
    rows = "".join("<tr><td>" + esc(x["severity"]) + "</td><td>" + esc(x["code"]) +
                   "</td><td>" + esc(x["path"]) + "</td><td>" + esc(x["explanation"]) +
                   "</td></tr>" for x in report.get("findings", []))
    notes = "".join("<li>" + esc(line) + "</li>" for line in report["limitations"])
    return ("<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<meta http-equiv='Content-Security-Policy' content=\"default-src 'none'; "
            "style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'\">"
            "<title>HPR Assembly Preflight — private report</title>"
            "<style>body{background:#111827;color:#e5edf7;font:16px system-ui;max-width:1100px;"
            "margin:40px auto;padding:0 20px}h1{font-size:30px}p,li{line-height:1.55}"
            ".badge{display:inline-block;padding:10px 16px;border-radius:10px;background:#273852;}"
            "table{width:100%;border-collapse:collapse;table-layout:fixed}td,th{padding:12px;"
            "border-bottom:1px solid #38455c;text-align:left;overflow-wrap:anywhere}"
            "th{color:#b3d8ff}td:first-child,th:first-child{width:10%}"
            "td:nth-child(2),th:nth-child(2){width:22%}"
            "td:nth-child(3),th:nth-child(3){width:25%}"
            "small{color:#aabacf}</style></head><body><small>HPR / PRIVATE UNITY SOURCE CHECK</small>"
            "<h1>Assembly definition preflight</h1><p>" + esc(report["project"]) + "</p>"
            "<p class='badge'>Result: " + esc(report["status"]) + "</p>"
            "<p>" + esc(report["asmdef_count"]) + " local assembly definitions; " +
            esc(report["asmref_count"]) + " assembly references; " +
            esc(len(report["findings"])) + " findings.</p>"
            "<h2>Findings requiring review</h2><table><thead><tr><th>Severity</th>"
            "<th>Finding</th><th>Saved path</th><th>What to check</th></tr></thead><tbody>" +
            (rows or "<tr><td colspan='4'>No findings in the supported saved-file scope.</td></tr>") +
            "</tbody></table><h2>Coverage limits</h2><ul>" + notes + "</ul>"
            "<p><small>Read-only local report. No automatic repair, no claim of Unity Editor acceptance, "
            "no network requests. Review private project paths before sharing.</small></p></body></html>")


def _write_new(out: Path, source: str, root: Path) -> None:
    if out.suffix.lower() not in (".json", ".html"):
        raise Incomplete("Choose a .json or .html output file")
    if out.exists() or out.is_symlink():
        raise Incomplete("Refusing to overwrite existing output")
    if not out.parent.is_dir() or out.parent.is_symlink():
        raise Incomplete("Output parent must be a pre-existing real directory")
    # No linked ancestor of an output path should silently redirect writes.
    for ancestor in (out.parent, *out.parent.parents):
        if ancestor.is_symlink():
            raise Incomplete("Linked output ancestor: " + str(ancestor))
    # Disallow creating results inside source project, even for a nested path.
    candidate = out.parent.resolve(strict=True) / out.name
    project = root.resolve(strict=True)
    if candidate == project or project in candidate.parents:
        raise Incomplete("Refusing to write report inside Unity project")
    fd = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as output:
        output.write(source)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("project", type=Path, help="Saved Unity project root, not a live unsaved session")
    ap.add_argument("--json-out", type=Path, help="Create-only JSON outside the Unity project")
    ap.add_argument("--html-out", type=Path, help="Create-only HTML outside the Unity project")
    args = ap.parse_args(argv)
    if args.json_out and args.html_out:
        ap.error("Select only one output format per invocation")
    try:
        result = inspect(args.project)
        if args.html_out:
            _write_new(args.html_out, render_html(result), args.project)
        else:
            serialized = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
            if args.json_out:
                _write_new(args.json_out, serialized, args.project)
            else:
                print(serialized, end="")
        return 1 if result["status"] != "CLEAR_WITH_LIMITS" else 0
    except (Incomplete, OSError) as exc:
        print("INCOMPLETE: " + str(exc), file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
