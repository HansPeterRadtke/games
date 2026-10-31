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
PROJECT = Path("/data/tmp/hpr_gameplay_suite_release_20261031/project")
RELEASE = Path("/data/var/marketplace-account-setup/unity-consolidated-20261031/release")
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
            raise RuntimeError("Missing original package: " + name)
        # Buyer content is one truly integrated product, not nine rejected
        # stand-alone storefront demos. Original Editor+Demo classes are
        # deliberately omitted: some require Unity UI, and their old UPM
        # paths are not valid inside a single-root .unitypackage archive.
        # All ten Runtime modules remain unmodified and independently tested.
        target = modules_dir / name
        if has_staged_modules:
            expected = source / "Runtime"
            candidate = target / "Runtime"
            if not target.is_dir() or not candidate.is_dir():
                raise RuntimeError("Unsafe previously staged project: " + name)
            source_files = sorted(f for f in expected.rglob("*.cs") if f.is_file())
            if not source_files or any(not (candidate / f.relative_to(expected)).is_file() or
                                       checksum(f) != checksum(candidate / f.relative_to(expected)) for f in source_files):
                raise RuntimeError("Staged module source has changed: " + name)
            if (target / "Demo").exists() or (target / "Editor").exists() or (target / "Tests").exists():
                raise RuntimeError("Unexpected stand-alone UPM demo/editor/test in buyer project")
        else:
            target.mkdir()
            shutil.copytree(source / "Runtime", target / "Runtime")
            for relative in ("Runtime.meta", "README.md", "LICENSE.md", "ThirdPartyNotices.md", "CHANGELOG.md"):
                f = source / relative
                if f.is_file():
                    shutil.copy2(f, target / relative)
                meta = source / (relative + ".meta")
                if meta.is_file():
                    shutil.copy2(meta, target / (relative + ".meta"))
        readme = target / "README.md"
        if readme.is_file():
            prefix = ("INTEGRATED SUITE INSTALLATION: This original HPR module is "
                      "already included under Assets/HPRGameplaySuite/Modules/" + name +
                      ". Do not install a second UPM copy. The former standalone "
                      "module demo/editor scenes are not bundled; use the "
                      "integrated GameplaySuiteShowcase scene in Assets/HPRGameplaySuite/Demo.\n\n")
            current = readme.read_text(encoding="utf-8")
            if not current.startswith("INTEGRATED SUITE INSTALLATION:"):
                readme.write_text(prefix + current, encoding="utf-8")
        original_files = [(str(f.relative_to(source)), checksum(f))
                          for f in sorted(source.rglob("*"))
                          if f.is_file() and not f.name.endswith(".meta") and "Tests" not in f.parts]
        manifests.append({"module": name, "source": "unity/packages/" + name,
                          "source_files": len(original_files),
                          "source_sha256": hashlib.sha256(json.dumps(original_files).encode()).hexdigest(),
                          "buyer_runtime_files": len(list((target / "Runtime").rglob("*.cs"))),
                          "standalone_module_demos_excluded": True})
    for dirname in ("Demo", "Integration", "Editor", "Samples"):
        (root / dirname).mkdir(parents=True, exist_ok=True)
    shutil.copy2(SCRIPT_DIR / "HprGameplaySuitePlayground.cs", root / "Integration" / "HprGameplaySuitePlayground.cs")
    shutil.copy2(SCRIPT_DIR / "HprGameplaySuiteSceneBuilder.cs", root / "Editor" / "HprGameplaySuiteSceneBuilder.cs")
    shutil.copy2(SCRIPT_DIR / "README.md", root / "README.md")
    shutil.copy2(SCRIPT_DIR / "INTEGRATED-SUITE-LICENSE.md", root / "LICENSE.md")
    shutil.copy2(SCRIPT_DIR / "ThirdPartyNotices.md", root / "ThirdPartyNotices.md")
    # The buyer has a single package root, unlike the nine former product drafts.
    manifest = {"format": "hpr-unity-suite-manifest-v1", "assembly_root": "Assets/HPRGameplaySuite", "source_branch": "product/unity-integrated-suite-20261030", "modules": manifests, "external_art_included": False, "includes_original_integration_demo": True, "excludes_test_assemblies": True}
    (RELEASE / "source-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("STAGED", len(MODULES), "RUNTIME_MODULES", sum(x["buyer_runtime_files"] for x in manifests), "C_SHARP_FILES", flush=True)
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
