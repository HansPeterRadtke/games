#!/usr/bin/env python3
"""Run a bounded real-saved-project CLI acceptance in a new private evidence folder.

Never edits source projects. Native Unity Editor is NOT used.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

SOURCE = Path(__file__).resolve().parents[1] / "hpr_scene_identity.py"


def digest(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def invoke(project: Path, *args: str) -> tuple[int, dict | None, str]:
    output = subprocess.run(
        [sys.executable, "-B", str(SOURCE), *args],
        cwd=project, capture_output=True, text=True, timeout=8, check=False)
    receipt = json.loads(output.stdout.strip()) if output.stdout.strip().startswith("{") else None
    return output.returncode, receipt, output.stderr.strip()


def run(project: Path, evidence: Path) -> dict:
    project = project.resolve(strict=True)
    evidence = evidence.absolute()
    assert project.is_dir()
    assert not evidence.exists(), "Use a new evidence directory, do not overwrite a prior run."
    evidence.mkdir(parents=True)
    files = sorted([
        f for f in (project / "Assets").rglob("*")
        if f.is_file() and f.suffix.lower() in (".unity", ".prefab", ".meta")
        and (f.name.endswith(".unity") or f.name.endswith(".prefab") or f.name.endswith(".unity.meta") or f.name.endswith(".prefab.meta"))
    ])
    source_hashes = {str(p.relative_to(project)): digest(p) for p in files}
    baseline = evidence / "baseline.json"
    same = evidence / "same-check.json"
    copy = evidence / "changed-project"
    (copy / "ProjectSettings").mkdir(parents=True)
    shutil.copy2(project / "ProjectSettings" / "ProjectVersion.txt", copy / "ProjectSettings" / "ProjectVersion.txt")
    for orig in files:
        dest = copy / orig.relative_to(project)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(orig, dest)
    rc1,out1,e1=invoke(project,"capture",str(project),"--out",str(baseline))
    assert rc1==0 and out1 and out1["status"]=="CAPTURED" and not e1,(rc1,out1,e1)
    rc2,out2,e2=invoke(project,"check",str(project),"--baseline",str(baseline),"--out",str(same))
    assert rc2==0 and out2 and out2["status"]=="IDENTITY_STABLE" and not e2,(rc2,out2,e2)
    originals = json.loads(baseline.read_text())
    assert originals["coverage"]=="direct-serialized-gameobject-documents-only"
    assert originals["asset_count"]>0 and originals["direct_object_count"]>0
    selected = next(row for row in originals["objects"] if row["kind"]=="scene")
    changed_source = copy / selected["path"]
    data = changed_source.read_text()
    old_id = selected["local_file_id"]
    replacement = "98765432109876"
    ids = {row["local_file_id"] for row in originals["objects"] if row["path"]==selected["path"]}
    assert replacement not in ids
    # Change one serialized GameObject document identifier in COPY only.
    pattern = re.compile(r"(?m)^--- !u!1 &"+re.escape(old_id)+r"(\s*)$")
    revised, count = pattern.subn("--- !u!1 &"+replacement+r"\1",data)
    assert count == 1, (selected,count)
    changed_source.write_text(revised)
    drift = evidence/"drift-check.json"
    rc3,out3,e3=invoke(project,"check",str(copy),"--baseline",str(baseline),"--out",str(drift))
    assert rc3==1 and out3 and out3["status"]=="REVIEW_REQUIRED" and not e3,(rc3,out3,e3)
    comparison = json.loads(drift.read_text())
    assert any(o["local_file_id"]==old_id and o["asset_guid"]==selected["asset_guid"] for o in comparison["lost"])
    assert any(o["local_file_id"]==replacement and o["asset_guid"]==selected["asset_guid"] for o in comparison["added"])
    for item,hash_ in source_hashes.items():
        assert digest(project/item) == hash_,"Original source mutated: "+item
    rc4, out4,e4=invoke(project,"capture",str(project),"--out",str(baseline))
    assert rc4==3 and baseline.exists() and "INCOMPLETE" in e4 and out4 is None
    record={
        "kind":"PRIVATE_SAVED_FILE_ONLY_CLI_ACCEPTANCE","status":"PASS",
        "tested_utc":datetime.now(timezone.utc).isoformat(),
        "source_project":str(project), "target_tool":str(SOURCE),
        "native_unity_editor_started":False,
        "read_only_originals_preserved":True,"source_file_hashes":source_hashes,
        "baseline_source_assets":originals["asset_count"],
        "baseline_direct_objects":originals["direct_object_count"],
        "test_changed_only_a_private_copy":True,
        "changed_asset":selected["path"],"changed_gameobject_fileid_from":old_id,
        "changed_gameobject_fileid_to":replacement,
        "actual_commands_exit_codes":{"capture":rc1,"stable_check":rc2,"modified_copy_check":rc3,"overwrite_rejected":rc4},
        "scope":"direct serialized GameObjects in Force Text Unity YAML only; not native Player save certification",
        "unknowns":["Native Unity Editor import/interaction","Actual Player runtime save compatibility","Nested/stripped prefab child IDs","Buyer demand/pricing/platform approval"],
    }
    (evidence / "acceptance-receipt.json").write_text(json.dumps(record,indent=2)+"\n")
    return record


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("source_project",type=Path)
    parser.add_argument("new_evidence_directory",type=Path)
    args=parser.parse_args()
    print(json.dumps(run(args.source_project,args.new_evidence_directory),indent=2))


if __name__ == "__main__":
    main()
