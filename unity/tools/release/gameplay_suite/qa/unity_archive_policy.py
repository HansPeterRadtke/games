#!/usr/bin/env python3
"""Read-only HPR .unitypackage structural and Unity Asset Store policy audit.

Validates immutable archive bytes, source/metadata identities, paths,
references and C# test/QA exclusion. This is not a Unity Editor import,
a runtime test, or approval to publish. Results are purely diagnostic.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import tarfile
import unicodedata

ROOT = "Assets/HPRGameplaySuite"
MAX_PACKAGE_BYTES = 160 * 1024 * 1024   # intentionally conservative for this product
MAX_ENTRY_BYTES = 32 * 1024 * 1024
MAX_MEMBERS = 30000
MAX_PATH_BYTES = 150
GUID = re.compile(r"^[0-9a-f]{32}$")
GUID_META = re.compile(rb"(?m)^guid:\s*([0-9a-fA-F]{32})\s*$")
ALLOWED_SUFFIXES = {"pathname", "asset", "asset.meta"}
SHIPPED_QA_FRAGMENTS = ("/tests/", "/test-runner", "/test_runner", "/qa/", "/nunit/")
SCRIPT_CONTENT_TYPES = {".cs", ".asmdef", ".asmref", ".unity", ".mat", ".asset",
                        ".prefab", ".md", ".txt", ".uss", ".uxml", ".json",
                        ".shader", ".compute", ".png", ".jpg", ".jpeg", ".unitypackage"}
WINDOWS_DEVICE_NAMES = frozenset({"con", "prn", "aux", "nul"} |
    {f"com{i}" for i in range(1, 10)} |
    {f"lpt{i}" for i in range(1, 10)})
WINDOWS_INVALID_PATH_CHARS = frozenset('<>:"|?*')


def _safe_unity_path(value: str) -> bool:
    if not isinstance(value, str) or not value.startswith(ROOT) or "\\" in value:
        return False
    path = PurePosixPath(value)
    if path.is_absolute() or any(p in ("", ".", "..") for p in value.split("/")):
        return False
    if value != ROOT and not value.startswith(ROOT + "/"):
        return False
    # Unity distributes the same package to Windows, Linux and macOS.
    # Names that look distinct on Linux can collide or be inaccessible on
    # Windows (reserved DOS device basename, trailing dot/space, characters)
    # or after Unicode NFC/NFD filename normalization on macOS.
    for segment in value.split("/"):
        if not segment or segment.endswith((" ", ".")) or segment.startswith(" "):
            return False
        if any(ord(char) < 32 or char in WINDOWS_INVALID_PATH_CHARS for char in segment):
            return False
        if segment.split(".", 1)[0].casefold() in WINDOWS_DEVICE_NAMES:
            return False
    return len(value.encode("utf-8")) <= MAX_PATH_BYTES


def _load_members(path: Path) -> tuple[dict[str, bytes], list[str]]:
    issues: list[str] = []
    parts: dict[str, bytes] = {}
    with tarfile.open(path, "r:gz") as tf:
        for index, member in enumerate(tf):
            if index >= MAX_MEMBERS:
                issues.append("archive member count exceeds permitted QA limit")
                break
            name = member.name
            if not member.isfile() or name.startswith("/") or "\\" in name:
                issues.append("invalid archive member or unsafe path: " + name[:100])
                continue
            segments = name.split("/")
            if len(segments) != 2 or not GUID.fullmatch(segments[0]) or \
                    segments[1] not in ALLOWED_SUFFIXES:
                issues.append("nonstandard or unsafe tar entry: " + name[:100])
                continue
            if name in parts:
                issues.append("duplicate archive entry: " + name[:100])
                continue
            if member.size > MAX_ENTRY_BYTES or member.size < 0:
                issues.append("unreasonably large archive entry: " + name[:100])
                continue
            stream = tf.extractfile(member)
            if stream is None:
                issues.append("tar payload unavailable: " + name[:100])
                continue
            data = stream.read(MAX_ENTRY_BYTES + 1)
            if len(data) != member.size:
                issues.append("truncated or oversized archive entry: " + name[:100])
                continue
            parts[name] = data
    return parts, issues


def _asmdef_issues(paths: dict[str, tuple[str, bool, bytes]]) -> tuple[list[str], int]:
    issues: list[str] = []
    asmdefs: dict[str, tuple[str, list[str]]] = {}
    for path, (_, has_body, raw) in paths.items():
        if not path.endswith(".asmdef"):
            continue
        if not has_body:
            issues.append("missing assembly definition body: " + path)
            continue
        try:
            data = json.loads(raw.decode("utf-8"))
            if not isinstance(data, dict):
                raise ValueError("assembly definition JSON must be an object")
            name = data["name"]
            refs = data.get("references", [])
            if not isinstance(name, str) or not name.strip() or \
                    not isinstance(refs, list) or not all(isinstance(x, str) for x in refs):
                raise ValueError("invalid assembly name/references")
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, ValueError) as exc:
            issues.append("invalid assembly definition: " + path + " (" + type(exc).__name__ + ")")
            continue
        if name in asmdefs:
            issues.append("duplicate assembly name: " + name)
        asmdefs[name] = (path, refs)
    for name, (_, refs) in asmdefs.items():
        for ref in refs:
            if ref not in asmdefs:
                issues.append("missing assembly dependency for " + name + ": " + ref)
    graph = {name: refs for name, (_, refs) in asmdefs.items()}
    visiting: set[str] = set()
    visited: set[str] = set()
    def dfs(node: str) -> None:
        if node in visiting:
            issues.append("circular assembly reference involving " + node)
            return
        if node in visited:
            return
        visiting.add(node)
        for other in graph.get(node, []):
            if other in graph:
                dfs(other)
        visiting.remove(node)
        visited.add(node)
    for name in graph:
        dfs(name)
    return issues, len(asmdefs)


def inspect_archive(path: Path) -> dict:
    path = Path(path)
    if not path.is_file() or path.is_symlink():
        raise FileNotFoundError("A concrete local immutable .unitypackage is required")
    if path.suffix != ".unitypackage":
        raise ValueError("Require an authentic .unitypackage suffix")
    if path.stat().st_size > MAX_PACKAGE_BYTES:
        raise ValueError("Internal QA package exceeds the bounded read limit")
    archive_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    try:
        parts, issues = _load_members(path)
    except (tarfile.TarError, OSError, EOFError) as exc:
        return {"status": "FAIL", "issues": ["invalid Unity tar container: " + type(exc).__name__],
                "read_only": True, "archive_sha256": archive_sha}
    entries: dict[str, dict[str, bytes]] = {}
    for name, blob in parts.items():
        identity, suffix = name.split("/")
        entries.setdefault(identity, {})[suffix] = blob
    paths: dict[str, tuple[str, bool, bytes]] = {}
    unicode_paths: dict[str, str] = {}
    case_insensitive_paths: dict[str, str] = {}
    for identity, group in entries.items():
        if "pathname" not in group or "asset.meta" not in group:
            issues.append("missing pathname or .meta for exported GUID " + identity)
            continue
        try:
            # Strip only Unity export's optional line ending. A raw filename
            # ending with a SPACE must not be silently normalized and accepted.
            name = group["pathname"].decode("utf-8").rstrip("\r\n")
        except UnicodeDecodeError:
            issues.append("invalid UTF-8 asset pathname for " + identity)
            continue
        if not _safe_unity_path(name):
            issues.append("unsafe, non-suite or overlong Unity asset path: " + name[:160])
        if any(fragment in name.casefold() for fragment in SHIPPED_QA_FRAGMENTS):
            issues.append("private test/QA path shipped: " + name)
        if name in paths:
            issues.append("duplicate asset path: " + name)
        unicode_key = unicodedata.normalize("NFC", name)
        previous_unicode = unicode_paths.get(unicode_key)
        if previous_unicode is not None and previous_unicode != name:
            issues.append("unicode normalization collision across platforms: " +
                          previous_unicode + " / " + name)
        unicode_paths[unicode_key] = name
        case_key = unicode_key.casefold()
        previous_case = case_insensitive_paths.get(case_key)
        if previous_case is not None and previous_case != name and \
                unicodedata.normalize("NFC", previous_case) != unicode_key:
            issues.append("case-insensitive asset path collision on Windows/macOS: " +
                          previous_case + " / " + name)
        case_insensitive_paths[case_key] = name
        meta = GUID_META.search(group["asset.meta"])
        if meta is None or meta.group(1).decode("ascii").lower() != identity:
            issues.append("asset GUID metadata mismatch: " + name)
        has_body = "asset" in group
        paths[name] = (identity, has_body, group.get("asset", b""))
        if name == ROOT and has_body:
            issues.append("top-level suite root should be a folder, not a file")
    if ROOT not in paths:
        issues.append("missing single Assets/HPRGameplaySuite root folder")
    for name, (_, has_body, _) in paths.items():
        if has_body:
            continue
        if name == ROOT:
            continue
        if name.endswith(tuple(SCRIPT_CONTENT_TYPES)) or \
                not any(other.startswith(name + "/") for other in paths):
            issues.append("missing non-directory asset payload: " + name)
    asm_issues, asm_count = _asmdef_issues(paths)
    issues.extend(asm_issues)
    return {
        "status": "FAIL" if issues else "PASS",
        "read_only": True,
        "not_a_unity_editor_test": True,
        "not_a_store_approval": True,
        "asset_count": len(paths),
        "assembly_definitions": asm_count,
        "archive_sha256": archive_sha,
        "max_asset_path_bytes": max((len(name.encode("utf-8")) for name in paths), default=0),
        "issues": sorted(set(issues)),
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("archive", type=Path)
    p.add_argument("--output", type=Path, help="create a new private receipt; never overwrite")
    args = p.parse_args()
    try:
        result = inspect_archive(args.archive)
        payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if args.output is not None:
            target = args.output.resolve(strict=False)
            if target == args.archive.resolve():
                raise ValueError("Refusing to overwrite the immutable source archive")
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with target.open("x", encoding="utf-8") as file:
                file.write(payload)
            target.chmod(0o600)
        print(payload, end="")
        return 0 if result["status"] == "PASS" else 2
    except (ValueError, OSError) as exc:
        print(json.dumps({"status": "ERROR", "reason": str(exc),
                          "read_only": True, "no_publication": True}))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
