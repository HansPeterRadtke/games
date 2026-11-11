#!/usr/bin/env python3
"""Build an independently testable, single-root Unity release candidate.

Never sends/submits to Unity's Asset Store and never touches publisher/account state.
Stages a new integration/sample plus the original authored HPR modules. Excludes
module unit-test assemblies from the buyer archive; original tests remain at source.
"""
from __future__ import annotations
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

MODULES = (
    "com.hpr.eventbus", "com.hpr.composition", "com.hpr.save", "com.hpr.stats",
    "com.hpr.inventory", "com.hpr.interaction", "com.hpr.abilities",
    "com.hpr.weapons", "com.hpr.ai", "com.hpr.world",
)
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[3]
PROJECT = Path(os.environ.get("HPR_SUITE_PROJECT_ROOT", "/data/tmp/hpr_gameplay_suite_release_20261031_v2/project"))
RELEASE = Path(os.environ.get("HPR_SUITE_RELEASE_ROOT", "/data/var/marketplace-account-setup/unity-consolidated-20261031-v2/release"))
UNITY = Path(os.environ.get("UNITY_BIN", "/data/apps/Unity/Hub/Editor/6000.4.0f1/Editor/Unity"))


def integrated_module_readme(name: str, original_text: str) -> str:
    """Keep original module API guidance; exclude unavailable standalone workflows."""
    removed_sections = {"Installation", "Demo", "Validation", "Samples", "Documentation", "Editor regression tests"}
    retained = []
    skipping = False
    for line in original_text.splitlines(keepends=True):
        if line.startswith("## "):
            skipping = line[3:].strip() in removed_sections
        if not skipping:
            retained.append(line)
    prefix = (
        "INTEGRATED SUITE INSTALLATION: This source module is already included "
        "inside Assets/HPRGameplaySuite/Modules/" + name + ". "
        "Do not separately install com.hpr.* packages because assembly names may "
        "collide. The standalone module editor and demo are not included. "
        "Use the suite Integration Guide, QUICKSTART.md, ARCHITECTURE.md and "
        "the integrated GameplaySuiteShowcase scene instead.\n\n"
    )
    return prefix + "".join(retained)


def checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


INSTALLER = Path("HPRGameplaySuite/Editor/HprSelectedAbilityInstaller.cs")


def stage_authored_buyer_assets(*, reuse_project: bool) -> dict[str, str]:
    """Stage source-controlled Unity YAML/meta before Editor opens the project.

    Import GUIDs must not be regenerated on every build: stable GUIDs are part
    of the buyer's public serialized contract, just like API names.
    Reuse preserves authored assets. Pre-installer projects can add the new pair.
    """
    source_root = SCRIPT_DIR / "buyer_source_assets"
    if not source_root.is_dir():
        raise RuntimeError("Missing source-controlled Unity buyer asset baseline")
    destination_root = PROJECT / "Assets"
    installer_pair = (INSTALLER, INSTALLER.with_suffix(".cs.meta"))
    add_installer = reuse_project and all(
        not os.path.lexists(destination_root / path) for path in installer_pair
    )
    asset_hashes = {}
    to_create = []
    for source_path in sorted(source_root.rglob("*")):
        if not source_path.is_file():
            continue
        if source_path.is_symlink():
            raise RuntimeError("Symlink not allowed in authored Unity asset baseline")
        relative = source_path.relative_to(source_root)
        staged = destination_root / relative
        if any((destination_root / parent).is_symlink() for parent in (relative, *relative.parents)):
            raise RuntimeError("Symlink in staged Unity asset path: " + str(relative))
        asset_hashes[relative.as_posix()] = checksum(source_path)
        if reuse_project and not (add_installer and relative in installer_pair):
            if not staged.is_file():
                raise RuntimeError("Required staged Unity asset is missing: " + str(relative))
            if source_path.suffix == ".meta":
                # Unity can update importer metadata, but not a published GUID.
                def read_guid(file: Path) -> str:
                    for line in file.read_text(encoding="utf-8").splitlines():
                        if line.startswith("guid: "):
                            return line[6:].strip()
                    raise ValueError("Invalid Unity meta file: " + str(file))
                if read_guid(source_path) != read_guid(staged):
                    raise RuntimeError("Staged Unity asset GUID differs from authored source: " + str(relative))
            elif checksum(source_path) != checksum(staged):
                raise RuntimeError("Staged Unity asset differs from source; create a fresh project: " + str(relative))
        else:
            if staged.exists():
                raise RuntimeError("Refusing to replace an existing Unity asset: " + str(relative))
            to_create.append((source_path, staged))
    if len(asset_hashes) < 70:
        raise RuntimeError("Incomplete source-controlled Unity scene / metadata baseline")
    # Validate the entire existing baseline before adding anything to it.
    for source_path, staged in to_create:
        staged.parent.mkdir(parents=True, exist_ok=True)
        with source_path.open("rb") as source, staged.open("xb") as output:
            shutil.copyfileobj(source, output)
    return asset_hashes


def run_editor(args: list[str], label: str, env: dict[str, str] | None = None) -> None:
    log = RELEASE / (label + ".unity.log")
    cmd = [str(UNITY), "-batchmode", "-nographics", "-quit", *args, "-logFile", str(log)]
    proc = subprocess.run(cmd, env=env, stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL, timeout=600, check=False)
    if proc.returncode:
        print("UNITY_FAILED", label, "exit", proc.returncode, "log", log, flush=True)
        raise RuntimeError("Unity " + label + " failed")
    print("UNITY_PASSED", label, flush=True)


def source_revision() -> dict:
    """An exported source tree may legitimately have no Git metadata."""
    def git(*args: str) -> str:
        result = subprocess.run(["git", "-C", str(REPO_ROOT), *args], capture_output=True,
                                text=True, check=False)
        return result.stdout.strip() if result.returncode == 0 else ""

    if not shutil.which("git") or git("rev-parse", "--show-toplevel") != str(REPO_ROOT):
        return {"source_commit": None, "source_branch": None, "source_tree_dirty": None}
    return {
        "source_commit": git("rev-parse", "HEAD"),
        "source_branch": git("branch", "--show-current") or None,
        "source_tree_dirty": bool(git("status", "--porcelain", "--", "unity/packages",
                                      "unity/tools/release/gameplay_suite")),
    }


def export_candidate(manifest: dict) -> None:
    from validate_release import inspect

    filename = "hpr-gameplay-systems-suite-candidate.unitypackage"
    # Unity must create a fresh file even when this directory already contains
    # a successful release. Leave that release intact if export or validation fails.
    with tempfile.TemporaryDirectory(dir=RELEASE, prefix=".hpr-export-") as directory:
        work = Path(directory)
        candidate = work / filename
        env = os.environ.copy()
        # Inherit the invoking account and any explicitly configured display.
        # Nitro's import workers use these defaults for its desktop session.
        for key, value in {
            "DISPLAY": ":1", "XAUTHORITY": "/home/hans/.Xauthority",
            "XDG_RUNTIME_DIR": "/run/user/1000",
            "DBUS_SESSION_BUS_ADDRESS": "unix:path=/run/user/1000/bus",
        }.items():
            env.setdefault(key, value)
        env["HPR_GAMEPLAY_SUITE_OUTPUT"] = str(candidate)
        run_editor(["-projectPath", str(PROJECT), "-executeMethod",
                    "HPR.GameplaySuite.HprGameplaySuiteSceneBuilder.ExportExisting"], "build-export", env)
        validation = inspect(candidate)
        digest = checksum(candidate)
        manifest_path = work / "source-manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        receipt = {
            "artifact": filename, "bytes": candidate.stat().st_size, "sha256": digest,
            "source_manifest_sha256": checksum(manifest_path), "module_count": len(MODULES),
            "unity_editor_success": True, "validation": validation,
            "release_status": "INTERNAL_QA_CANDIDATE_NOT_SUBMITTED_NOT_PUBLISHED",
        }
        receipt_path = work / "release-receipt.json"
        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        # Serialize replacement of related files. The receipt is the last write
        # and records both hashes, including after an interrupted replacement.
        directory_fd = os.open(RELEASE, os.O_RDONLY)
        try:
            fcntl.flock(directory_fd, fcntl.LOCK_EX)
            for output in (candidate, manifest_path, receipt_path):
                output.replace(RELEASE / output.name)
        finally:
            os.close(directory_fd)
        print("EXPORTED_BYTES", receipt["bytes"], "SHA256", digest, flush=True)


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
        args.reuse_project = False
    elif not args.reuse_project:
        raise RuntimeError("Build project exists; use --reuse-project to explicitly reuse, never delete it")

    authored_assets = stage_authored_buyer_assets(reuse_project=args.reuse_project)
    root = PROJECT / "Assets" / "HPRGameplaySuite"
    modules_dir = root / "Modules"
    # The stable asset GUID baseline includes Modules/ and module-folder .meta
    # files, but they do not mean runtime source modules were already staged.
    has_staged_modules = any((modules_dir / name).is_dir() for name in MODULES)
    if has_staged_modules and not args.reuse_project:
        raise RuntimeError("Modules are already staged; explicit --reuse-project is required")
    if not modules_dir.is_dir():
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
        original_module_readme = source / "README.md"
        if original_module_readme.is_file():
            desired_readme = integrated_module_readme(
                name, original_module_readme.read_text(encoding="utf-8"))
            # The project is an explicitly owned disposable staging directory.
            # Always refresh authored source docs on intentional --reuse-project.
            readme.write_text(desired_readme, encoding="utf-8")
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
    shutil.copy2(SCRIPT_DIR / "HprSuiteIntegration.cs", root / "Integration" / "HprSuiteIntegration.cs")
    shutil.copy2(SCRIPT_DIR / "HprSuiteArenaMotor.cs", root / "Integration" / "HprSuiteArenaMotor.cs")
    shutil.copy2(SCRIPT_DIR / "HprSuiteInput.cs", root / "Integration" / "HprSuiteInput.cs")
    shutil.copy2(SCRIPT_DIR / "HprSuiteSnapshot.cs", root / "Integration" / "HprSuiteSnapshot.cs")
    shutil.copy2(SCRIPT_DIR / "HprGameplaySuiteSceneBuilder.cs", root / "Editor" / "HprGameplaySuiteSceneBuilder.cs")
    shutil.copy2(SCRIPT_DIR / "HprSuiteIntegrationGuide.cs", root / "Editor" / "HprSuiteIntegrationGuide.cs")
    styles_dir = root / "Editor" / "Styles"
    styles_dir.mkdir(exist_ok=True)
    shutil.copy2(SCRIPT_DIR / "HprSuiteIntegrationGuide.uss", styles_dir / "HprSuiteIntegrationGuide.uss")
    shutil.copy2(SCRIPT_DIR / "README.md", root / "README.md")
    shutil.copy2(SCRIPT_DIR / "QUICKSTART.md", root / "QUICKSTART.md")
    shutil.copy2(SCRIPT_DIR / "ARCHITECTURE.md", root / "ARCHITECTURE.md")
    shutil.copy2(SCRIPT_DIR / "INTEGRATED-SUITE-LICENSE.md", root / "LICENSE.md")
    shutil.copy2(SCRIPT_DIR / "ThirdPartyNotices.md", root / "ThirdPartyNotices.md")
    # The buyer has a single package root, unlike the nine former product drafts.
    manifest = {
        "format": "hpr-unity-suite-manifest-v2",
        "assembly_root": "Assets/HPRGameplaySuite",
        **source_revision(),
        "modules": manifests,
        "external_art_included": False,
        "includes_original_integration_demo": True,
        "excludes_test_assemblies": True,
    }
    manifest["authored_buyer_assets"] = authored_assets
    manifest["integration_sources"] = {
        item: checksum(SCRIPT_DIR / item) for item in (
            "HprGameplaySuitePlayground.cs", "HprGameplaySuiteSceneBuilder.cs",
            "HprSuiteIntegration.cs", "HprSuiteSnapshot.cs",
            "HprSuiteArenaMotor.cs", "HprSuiteInput.cs", "HprSuiteIntegrationGuide.cs",
            "HprSuiteIntegrationGuide.uss", "README.md",
            "QUICKSTART.md", "ARCHITECTURE.md")
    }
    print("STAGED", len(MODULES), "RUNTIME_MODULES", sum(x["buyer_runtime_files"] for x in manifests), "C_SHARP_FILES", flush=True)
    export_candidate(manifest)
    print("DONE_WITHOUT_PROVIDER_WRITE", flush=True)


if __name__ == "__main__":
    main()
