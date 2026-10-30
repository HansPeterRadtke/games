#!/usr/bin/env python3
"""Build an independently testable, single-root Unity release candidate.

Never sends/submits to Unity's Asset Store and never touches publisher/account state.
Stages a new integration/sample plus the original authored HPR modules. Excludes
module unit-test assemblies from the buyer archive; original tests remain at source.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

MODULES = (
    "com.hpr.eventbus", "com.hpr.composition", "com.hpr.save", "com.hpr.stats",
    "com.hpr.inventory", "com.hpr.interaction", "com.hpr.abilities",
    "com.hpr.weapons", "com.hpr.ai", "com.hpr.world",
)
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[3]
PROJECT = Path("/data/tmp/hpr_gameplay_suite_release_20261030/project")
RELEASE = Path("/data/var/marketplace-account-setup/unity-consolidated-20261030/release")
UNITY = Path("/data/apps/Unity/Hub/Editor/6000.4.0f1/Editor/Unity")


def checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_editor(args: list[str], label: str) -> None:
    log = RELEASE / (label + ".unity.log")
    cmd = [str(UNITY), "-batchmode", "-nographics", "-quit", *args, "-logFile", str(log)]
    proc = subprocess.run(cmd, env=os.environ.copy(), stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL, timeout=600, check=False)
    if proc.returncode:
        print("UNITY_FAILED", label, "exit", proc.returncode, "log", log, flush=True)
        raise RuntimeError("Unity " + label + " failed")
    print("UNITY_PASSED", label, flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reuse-project", action="store_true", help="Only reuse a project created by this script; does not destroy existing projects")
    args = ap.parse_args()
    RELEASE.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(RELEASE, 0o700)
    print("GAMES_REPO", REPO_ROOT, flush=True)
    if not UNITY.is_file():
        raise RuntimeError("Unity editor is not installed")
    if not PROJECT.exists():
        PROJECT.parent.mkdir(parents=True, exist_ok=True)
        run_editor(["-createProject", str(PROJECT)], "create")
    elif not args.reuse_project:
        raise RuntimeError("Build project exists; use --reuse-project to explicitly reuse, never delete it")

    # Original AbilitiesDemoController uses UnityEngine.UI.Text. Ship the
    # matching Unity Registry uGUI dependency in project QA (buyer must also
    # install com.unity.ugui 2.0.0 before opening the original module demos).
    unity_manifest_path = PROJECT / "Packages" / "manifest.json"
    unity_manifest = json.loads(unity_manifest_path.read_text())
    unity_manifest.setdefault("dependencies", {})["com.unity.ugui"] = "2.0.0"
    unity_manifest_path.write_text(json.dumps(unity_manifest, indent=2) + "\n")
    root = PROJECT / "Assets" / "HPRGameplaySuite"
    modules_dir = root / "Modules"
    has_staged_modules = modules_dir.exists()
    if has_staged_modules and not args.reuse_project:
        raise RuntimeError("Modules are already staged; explicit --reuse-project is required")
    if not has_staged_modules:
        modules_dir.mkdir(parents=True)
    manifests = []
    for name in MODULES:
        source = REPO_ROOT / "unity" / "packages" / name
        if not (source / "package.json").exists():
            raise RuntimeError("Missing package: " + name)
        # Imported Assets cannot require test assemblies/NUnit during normal compilation;
        # all original tests are kept in source and validated in a separate clean project.
        target = modules_dir / name
        if has_staged_modules:
            # Reuse only the workspace created by this builder with matching
            # original module sources, not an arbitrary directory a bot found.
            expected = source / "Runtime"
            candidate = target / "Runtime"
            if not target.is_dir() or not candidate.is_dir():
                raise RuntimeError("Unsafe staged project: missing module " + name)
            src_files = sorted(p for p in expected.rglob("*.cs") if p.is_file())
            if not src_files or any(not (candidate / p.relative_to(expected)).is_file() or
                                    checksum(p) != checksum(candidate / p.relative_to(expected)) for p in src_files):
                raise RuntimeError("Unsafe staged project: module source mismatch " + name)
        else:
            shutil.copytree(source, target, ignore=shutil.ignore_patterns("Tests", "Tests.meta", "__pycache__"))
        items = [(str(p.relative_to(source)), checksum(p)) for p in sorted(source.rglob("*")) if p.is_file() and not p.name.endswith(".meta") and "Tests" not in p.parts]
        manifests.append({"module": name, "source": "unity/packages/" + name, "files": len(items), "source_sha256": hashlib.sha256(json.dumps(items).encode()).hexdigest()})
    for dirname in ("Demo", "Integration", "Editor", "Samples"):
        (root / dirname).mkdir(parents=True, exist_ok=True)
    shutil.copy2(SCRIPT_DIR / "HprGameplaySuitePlayground.cs", root / "Integration" / "HprGameplaySuitePlayground.cs")
    shutil.copy2(SCRIPT_DIR / "HprGameplaySuiteSceneBuilder.cs", root / "Editor" / "HprGameplaySuiteSceneBuilder.cs")
    shutil.copy2(SCRIPT_DIR / "README.md", root / "README.md")
    shutil.copy2(SCRIPT_DIR / "INTEGRATED-SUITE-LICENSE.md", root / "LICENSE.md")
    # The buyer has a single package root, unlike the nine former product drafts.
    manifest = {"format": "hpr-unity-suite-manifest-v1", "assembly_root": "Assets/HPRGameplaySuite", "source_branch": "product/unity-integrated-suite-20261030", "modules": manifests, "external_art_included": False, "includes_original_integration_demo": True, "excludes_test_assemblies": True}
    (RELEASE / "source-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("STAGED", len(MODULES), "MODULES", sum(x["files"] for x in manifests), "FILES", flush=True)
    archive = RELEASE / "hpr-gameplay-systems-suite-candidate.unitypackage"
    env = os.environ.copy()
    env.update({"HOME": "/home/hans", "USER": "hans", "LOGNAME": "hans", "DISPLAY": ":1", "XAUTHORITY": "/home/hans/.Xauthority", "XDG_RUNTIME_DIR": "/run/user/1000", "DBUS_SESSION_BUS_ADDRESS": "unix:path=/run/user/1000/bus", "HPR_GAMEPLAY_SUITE_OUTPUT": str(archive)})
    log = RELEASE / "build-export.unity.log"
    proc = subprocess.run([str(UNITY), "-batchmode", "-nographics", "-quit", "-projectPath", str(PROJECT), "-executeMethod", "HPR.GameplaySuite.HprGameplaySuiteSceneBuilder.BuildAndExport", "-logFile", str(log)], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600, check=False)
    if proc.returncode or not archive.is_file():
        print("EXPORT_FAILED", proc.returncode, "log", log, flush=True)
        raise RuntimeError("Unity scene build/export failed; do not publish this candidate")
    print("EXPORTED_BYTES", archive.stat().st_size, "SHA256", checksum(archive), flush=True)
    receipt = {"artifact": archive.name, "bytes": archive.stat().st_size, "sha256": checksum(archive), "module_count": len(MODULES), "unity_editor_success": True, "release_status": "INTERNAL_QA_CANDIDATE_NOT_SUBMITTED_NOT_PUBLISHED"}
    (RELEASE / "release-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print("DONE_WITHOUT_PROVIDER_WRITE", flush=True)


if __name__ == "__main__":
    main()
