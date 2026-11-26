#!/usr/bin/env python3
"""Read-only, bounded Unity text-scene identity witness for release comparisons.

This intentionally covers *direct serialized GameObject YAML documents* in scene
and prefab assets. It does not certify gameplay save compatibility, nested
prefab-instance children, unsaved Editor state, or binary assets.

The command never opens Unity, edits project files or overwrites an output.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
from pathlib import Path

SCHEMA = "hpr.scene-identity-snapshot.v1"
COVERAGE = "direct-serialized-gameobject-documents-only"
ALLOWED_SUFFIXES = {".unity": "scene", ".prefab": "prefab"}
GUID_RE = re.compile(r"^guid:\s*([0-9a-fA-F]{32})\s*$", re.MULTILINE)
HEADER_RE = re.compile(r"^--- !u!1 &(-?[1-9][0-9]*)(?:\s+(stripped))?\s*$")
NAME_RE = re.compile(r"^  m_Name:\s*(.*)$")
PROJECT_VERSION = Path("ProjectSettings/ProjectVersion.txt")
MAX_FILES = 3000
MAX_BYTES_EACH = 32 * 1024 * 1024
MAX_BYTES_TOTAL = 128 * 1024 * 1024
MAX_BASELINE_BYTES = 16 * 1024 * 1024
MAX_RECORDS = 200000


class IncompleteScan(Exception):
    """The scan cannot responsibly report a complete result."""


def _is_normal_file(path: Path) -> bool:
    try:
        mode = path.lstat().st_mode
        return stat.S_ISREG(mode)
    except OSError:
        return False


def _read_stable_file(path: Path, limit: int) -> bytes:
    """Reject device files, symlinks and files changing during a single read."""
    try:
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode):
            raise IncompleteScan("Not a regular file (including symlinks): " + str(path))
        if before.st_size > limit:
            raise IncompleteScan("File over size limit: " + str(path))
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
                     | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NONBLOCK", 0))
        with os.fdopen(fd, "rb") as stream:
            # Nonblocking open + fstat prevents a replaced FIFO/device from hanging reads.
            during = os.fstat(stream.fileno())
            if not stat.S_ISREG(during.st_mode):
                raise IncompleteScan("Opened object was replaced by a nonregular file: " + str(path))
            data = stream.read(limit + 1)
        after = path.lstat()
    except OSError as exc:
        raise IncompleteScan("Cannot read file: " + str(path) + ": " + str(exc)) from exc
    if len(data) > limit:
        raise IncompleteScan("File exceeded size limit while reading: " + str(path))
    fingerprint = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns)
    if fingerprint(before) != fingerprint(during) or fingerprint(before) != fingerprint(after):
        raise IncompleteScan("File changed during scan: " + str(path))
    if not stat.S_ISREG(during.st_mode):
        raise IncompleteScan("Nonregular file during scan: " + str(path))
    return data


def _guid_from_meta(meta: Path) -> str:
    data = _read_stable_file(meta, 512 * 1024)
    try:
        text = data.decode("utf-8-sig")
    except UnicodeError as exc:
        raise IncompleteScan("Invalid metadata text: " + str(meta)) from exc
    matches = GUID_RE.findall(text)
    if len(matches) != 1:
        raise IncompleteScan("Missing or repeated asset GUID: " + str(meta))
    return matches[0].lower()


def _direct_objects(data: bytes, rel_path: str) -> tuple[list[tuple[str, str]], int]:
    if not data.startswith(b"%YAML "):
        raise IncompleteScan("Not a Unity Force Text YAML asset: " + rel_path)
    try:
        text = data.decode("utf-8-sig")
    except UnicodeError as exc:
        raise IncompleteScan("Invalid YAML UTF-8 text: " + rel_path) from exc
    result: list[tuple[str, str]] = []
    active_id: str | None = None
    active_name = ""
    active_is_gameobject = False
    stripped_count = 0

    def finish() -> None:
        if active_id is not None:
            if not active_is_gameobject:
                raise IncompleteScan("GameObject document has no GameObject type marker: " + rel_path)
            result.append((active_id, active_name[:500]))

    for line in text.splitlines():
        if line.startswith("--- "):
            finish()
            active_id = None
            active_name = ""
            active_is_gameobject = False
            m = HEADER_RE.fullmatch(line)
            if m:
                if m.group(2):
                    stripped_count += 1
                else:
                    active_id = m.group(1)
            continue
        if active_id is not None:
            if line == "GameObject:":
                active_is_gameobject = True
            m = NAME_RE.fullmatch(line)
            if m:
                active_name = m.group(1)
    finish()
    if not result:
        raise IncompleteScan("No directly serialized GameObjects (may be a variant): " + rel_path)
    file_ids = [r[0] for r in result]
    if len(file_ids) != len(set(file_ids)):
        raise IncompleteScan("Duplicate GameObject YAML identifiers: " + rel_path)
    return result, stripped_count


def _assets_to_scan(project: Path) -> list[tuple[Path, str]]:
    if not project.is_dir() or project.is_symlink():
        raise IncompleteScan("Project directory is missing or a symlink")
    if not _is_normal_file(project / PROJECT_VERSION):
        raise IncompleteScan("Missing regular ProjectSettings/ProjectVersion.txt")
    root = project / "Assets"
    if not root.is_dir() or root.is_symlink():
        raise IncompleteScan("Missing or linked Assets folder")
    paths: list[tuple[Path, str]] = []
    for dirpath, dirs, names in os.walk(root, topdown=True, followlinks=False):
        here = Path(dirpath)
        for dirname in dirs:
            if (here / dirname).is_symlink():
                raise IncompleteScan("Linked asset folder cannot be safely enumerated: " + str(here / dirname))
        dirs.sort()
        for name in sorted(names):
            candidate = here / name
            kind = ALLOWED_SUFFIXES.get(candidate.suffix.lower())
            if kind:
                paths.append((candidate, kind))
                if len(paths) > MAX_FILES:
                    raise IncompleteScan("Asset count exceeds bounded scan limit")
    if not paths:
        raise IncompleteScan("No .unity or .prefab assets in Assets folder")
    return paths


def scan(project: Path) -> dict:
    project = Path(project).absolute()
    assets = _assets_to_scan(project)
    rows = []
    file_evidence = []
    guid_paths: dict[str, str] = {}
    cumulative_bytes = 0
    stripped = 0
    for path, kind in assets:
        relative = path.relative_to(project).as_posix()
        data = _read_stable_file(path, MAX_BYTES_EACH)
        cumulative_bytes += len(data)
        if cumulative_bytes > MAX_BYTES_TOTAL:
            raise IncompleteScan("Combined YAML size exceeds bounded scan limit")
        meta = Path(str(path) + ".meta")
        guid = _guid_from_meta(meta)
        if guid in guid_paths:
            raise IncompleteScan("Duplicate asset GUID: " + relative + " and " + guid_paths[guid])
        guid_paths[guid] = relative
        objects, local_stripped = _direct_objects(data, relative)
        stripped += local_stripped
        file_evidence.append({
            "path": relative, "kind": kind, "guid": guid,
            "source_sha256": hashlib.sha256(data).hexdigest(),
            "meta_sha256": hashlib.sha256(_read_stable_file(meta, 512 * 1024)).hexdigest(),
            "direct_count": len(objects), "stripped_docs": local_stripped,
        })
        for file_id, name in objects:
            rows.append({
                "kind": kind, "asset_guid": guid, "local_file_id": file_id,
                "path": relative, "name": name,
            })
        if len(rows) > MAX_RECORDS:
            raise IncompleteScan("Too many directly serialized objects")
    rows.sort(key=lambda r: (r["asset_guid"], int(r["local_file_id"]), r["kind"]))
    file_evidence.sort(key=lambda r: r["path"])
    return {
        "schema": SCHEMA, "coverage": COVERAGE, "complete": True,
        "asset_count": len(assets), "direct_object_count": len(rows),
        "stripped_prefab_documents_not_resolved": stripped,
        "files": file_evidence, "objects": rows,
    }


def _validated_snapshot(path: Path) -> dict:
    raw = _read_stable_file(Path(path), MAX_BASELINE_BYTES)
    try:
        s = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise IncompleteScan("Unreadable or malformed baseline") from exc
    if not isinstance(s, dict) or s.get("schema") != SCHEMA or s.get("coverage") != COVERAGE or s.get("complete") is not True:
        raise IncompleteScan("Unsupported or incomplete baseline")
    objects, files = s.get("objects"), s.get("files")
    if not isinstance(objects, list) or not isinstance(files, list) or len(objects) > MAX_RECORDS or len(files) > MAX_FILES:
        raise IncompleteScan("Baseline record count invalid")
    keys: set[tuple[str, str, str]] = set()
    file_guids: dict[str, dict] = {}
    for f in files:
        if not isinstance(f, dict) or not re.fullmatch(r"[0-9a-f]{32}",str(f.get("guid", ""))):
            raise IncompleteScan("Malformed baseline asset record")
        if f["guid"] in file_guids:
            raise IncompleteScan("Repeated GUID in baseline assets")
        _validate_asset_path(f.get("path"))
        kind = ALLOWED_SUFFIXES.get(Path(f["path"]).suffix.lower())
        if kind is None or kind != f.get("kind"):
            raise IncompleteScan("Baseline kind does not match asset extension")
        file_guids[f["guid"]] = f
    for obj in objects:
        if not isinstance(obj, dict):
            raise IncompleteScan("Malformed baseline object")
        kind, guid, file_id = obj.get("kind"), obj.get("asset_guid"), obj.get("local_file_id")
        if kind not in ("scene", "prefab") or not isinstance(guid, str) or not re.fullmatch(r"[0-9a-f]{32}", guid) or not isinstance(file_id,str) or not re.fullmatch(r"-?[1-9][0-9]*",file_id):
            raise IncompleteScan("Malformed baseline identity key")
        if not isinstance(obj.get("name"), str) or len(obj["name"]) > 500:
            raise IncompleteScan("Malformed baseline name")
        _validate_asset_path(obj.get("path"))
        if guid not in file_guids:
            raise IncompleteScan("Baseline refers to unknown asset GUID")
        if obj["path"] != file_guids[guid]["path"] or kind != file_guids[guid]["kind"]:
            raise IncompleteScan("Baseline identity path and asset identity disagree")
        key = (kind,guid,file_id)
        if key in keys:
            raise IncompleteScan("Repeated baseline identity")
        keys.add(key)
    if len(objects) != s.get("direct_object_count") or len(files) != s.get("asset_count"):
        raise IncompleteScan("Inconsistent baseline counts")
    return s


def _validate_asset_path(value: object) -> None:
    if not isinstance(value, str) or not value.startswith("Assets/") or "\\" in value or "\x00" in value:
        raise IncompleteScan("Unsafe baseline asset path")
    if any(part in ("", ".", "..") for part in value.split("/")):
        raise IncompleteScan("Unsafe baseline asset path")


def compare(baseline: dict, current: dict) -> dict:
    base = {(o["kind"],o["asset_guid"],o["local_file_id"]):o for o in baseline["objects"]}
    now = {(o["kind"],o["asset_guid"],o["local_file_id"]):o for o in current["objects"]}
    lost = [base[k] for k in sorted(base.keys() - now.keys())]
    added = [now[k] for k in sorted(now.keys() - base.keys())]
    bpaths = {f["path"]:f for f in baseline["files"]}
    npaths = {f["path"]:f for f in current["files"]}
    guid_changed = [{"path":p,"was":bpaths[p]["guid"],"now":npaths[p]["guid"]}
                    for p in sorted(bpaths.keys() & npaths.keys())
                    if bpaths[p]["guid"] != npaths[p]["guid"]]
    # Same GUID + local ID survives name edits and asset moves. These aren't lost IDs.
    renamed_or_moved = [{
        "was_path":base[k]["path"],"now_path":now[k]["path"],
        "was_name":base[k]["name"],"now_name":now[k]["name"],
        "asset_guid":k[1],"local_file_id":k[2],
    } for k in sorted(base.keys() & now.keys())
      if base[k]["path"] != now[k]["path"] or base[k]["name"] != now[k]["name"]]
    status = "REVIEW_REQUIRED" if lost or guid_changed else ("ADDITIONS_ONLY" if added else "IDENTITY_STABLE")
    return {
        "status":status, "scope":COVERAGE, "baseline_objects":len(base),
        "current_objects":len(now), "lost":lost, "added":added,
        "changed_asset_guids":guid_changed,
        "renamed_or_moved_without_identity_loss":renamed_or_moved,
        "warning":"This is NOT certification of runtime save compatibility, nested prefab instance IDs, unsaved Editor state or binary serialization.",
    }


def _write_new(path: Path, obj: dict) -> None:
    payload = (json.dumps(obj,indent=2,ensure_ascii=False,sort_keys=True)+"\n").encode("utf-8")
    if path.is_symlink():
        raise IncompleteScan("Output path is a symbolic link")
    # x is intentionally create-only: no replacing previous release baselines.
    with path.open("xb") as stream:
        stream.write(payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only, direct-GameObject Unity identity release witness.")
    parser.add_argument("action",choices=["capture","check"])
    parser.add_argument("project",type=Path)
    parser.add_argument("--out",type=Path,help="New, never-overwritten JSON output file")
    parser.add_argument("--baseline",type=Path,help="Required for check")
    args = parser.parse_args(argv)
    if args.action == "capture" and (args.out is None or args.baseline is not None):
        parser.error("capture requires --out and does not accept --baseline")
    if args.action == "check" and args.baseline is None:
        parser.error("check requires --baseline")
    try:
        baseline = _validated_snapshot(args.baseline) if args.action == "check" else None
        current = scan(args.project)
        result = current if baseline is None else compare(baseline,current)
        if args.out is not None:
            _write_new(args.out,result)
        print(json.dumps({"status":result.get("status","CAPTURED"),"assets":current["asset_count"],
            "objects":current["direct_object_count"],"coverage":COVERAGE,
            "missing":len(result.get("lost",[])),"added":len(result.get("added",[]))},sort_keys=True))
        return 1 if result.get("status") == "REVIEW_REQUIRED" else 0
    except (IncompleteScan,OSError) as exc:
        print("INCOMPLETE: "+str(exc),file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
