#!/usr/bin/env python3
"""Create-only native NUnit QA of an already natively imported private archive.

Run through resource-broker-job. Does not import packages, open graphical consent,
modify source projects, or certify rendered usability. Stages canonical module tests
into a new project copy and checks exact product source before and after execution.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import time
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from unity_imported_archive_identity import verify_import


PRIVATE_QA_ROOT = Path("/data/var/marketplace-account-setup")
EXPECTED_ASSEMBLIES = {
    "HPR.Abilities.Tests.EditMode": 25, "HPR.Ai.Tests.EditMode": 6,
    "HPR.Composition.Tests.EditMode": 4, "HPR.Eventbus.Tests.EditMode": 4,
    "HPR.Interaction.Tests.EditMode": 3, "HPR.Inventory.Tests.EditMode": 4,
    "HPR.Save.Tests.EditMode": 2, "HPR.Stats.Tests.EditMode": 2,
    "HPR.Weapons.Tests.EditMode": 5, "HPR.World.Tests.EditMode": 1,
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(project):
    result = {}
    for folder in ("Assets", "Packages", "ProjectSettings"):
        for path in (project / folder).rglob("*"):
            if path.is_symlink():
                raise ValueError("Symlink in QA project")
            if path.is_file():
                result[path.relative_to(project).as_posix()] = digest(path)
    return result


def preserved_file_changes(before, after, resolved_lock, expected_lock):
    """Only the explicitly planned copied-project package resolution may change."""
    changed = [name for name, value in before.items() if after.get(name) != value]
    lock_name = "Packages/packages-lock.json"
    if resolved_lock == expected_lock and lock_name in after:
        changed = [name for name in changed if name != lock_name]
    elif lock_name not in changed:
        changed.append(lock_name)
    return changed


def expected_bundled_lock(previous, framework, nunit, direct_dependencies):
    """Derive the narrow permitted lock update from installed first-party manifests."""
    expected = deepcopy(previous)
    for package, depth in ((framework, 0), (nunit, 0 if nunit["name"] in direct_dependencies else 1)):
        expected["dependencies"][package["name"]] = {
            "version": package["version"], "depth": depth, "source": "builtin",
            "dependencies": package.get("dependencies", {})}
    return expected


def classify_xml(native_exit, xml_text):
    """Fail closed on missing, duplicate, skipped, partial or inconsistent results."""
    errors = []
    try:
        root = ET.fromstring(xml_text)
        cases = list(root.iter("test-case"))
        if root.tag != "test-run" or root.get("result") != "Passed":
            errors.append("Native NUnit run did not pass")
        total = sum(EXPECTED_ASSEMBLIES.values())
        if len(cases) != total or int(root.get("total", "-1")) != total or int(root.get("passed", "-1")) != total:
            errors.append("Missing or inconsistent test count")
        if any(int(root.get(key, "-1")) != 0 for key in ("failed", "skipped", "inconclusive")):
            errors.append("Failed, skipped or inconclusive tests")
        if any(c.get("result") != "Passed" for c in cases):
            errors.append("A test case did not pass")
        ids = [c.get("fullname") for c in cases]
        if any(not key for key in ids) or len(ids) != len(set(ids)):
            errors.append("Missing or duplicated test identities")
        assemblies = [s for s in root.iter("test-suite") if s.get("type") == "Assembly"]
        counts = {}
        for assembly in assemblies:
            name = assembly.get("name", "").removesuffix(".dll")
            if name in counts:
                errors.append("Duplicate assembly receipt")
            counts[name] = len(list(assembly.iter("test-case")))
            if assembly.get("result") != "Passed":
                errors.append("Assembly did not pass")
        if counts != EXPECTED_ASSEMBLIES:
            errors.append("Missing or unexpected module coverage")
    except (ET.ParseError, ValueError, TypeError):
        cases, counts = [], {}
        errors.append("Invalid NUnit XML")
    if native_exit != 0:
        errors.append("Native Editor exit was not zero")
    return {"passed": not errors, "test_cases": len(cases), "assembly_counts": counts, "errors": errors}


def verify_vendor(project, archive):
    mismatches, count = [], 0
    with tarfile.open(archive, "r:gz") as package:
        payloads = {m.name: package.extractfile(m).read() for m in package if m.isfile()}
    for key, raw in payloads.items():
        if key.endswith("/pathname"):
            name = raw.decode().rstrip("\r\n")
            if name.endswith(".cs"):
                count += 1
                target = project / name
                expected = hashlib.sha256(payloads[key.rsplit("/", 1)[0] + "/asset"]).hexdigest()
                if not target.is_file() or digest(target) != expected:
                    mismatches.append(name)
    return count, mismatches


def require_exact_package(project, archive, expected_sha):
    identity = verify_import(archive, project, expected_sha)
    if identity["status"] != "PASS":
        raise ValueError("Project differs from selected archive: " + "; ".join(identity["issues"]))
    if identity["script_payloads_verified"] != 55:
        raise ValueError("The native module suite expects 55 packaged scripts")
    return identity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--import-receipt", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--archive-sha256", required=True)
    parser.add_argument("--editor", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-seconds", type=int, default=600)
    args = parser.parse_args()
    if not 60 <= args.max_seconds <= 900:
        raise ValueError("Bounded native test time required")
    if args.output.exists() or args.output.is_symlink():
        raise FileExistsError("Inspect existing results; do not replay")
    parent = args.output.parent.resolve()
    if parent == PRIVATE_QA_ROOT or not parent.is_relative_to(PRIVATE_QA_ROOT):
        raise ValueError("Use a private task runtime subdirectory")
    if args.output.resolve().is_relative_to(args.template.resolve()):
        raise ValueError("The test output must be outside the source project")
    prior = json.loads(args.import_receipt.read_text())
    if prior.get("actual_unity_editor_executed") is not True or prior.get("exit_code") != 0 or prior.get("archive_sha256") != args.archive_sha256:
        raise ValueError("Matching successful actual native import receipt required")
    if not args.editor.is_file() or args.editor.is_symlink() or args.template.is_symlink():
        raise ValueError("Installed Editor and original private project required")
    for folder in ("Assets", "Packages", "ProjectSettings", "Library"):
        source = args.template / folder
        if source.is_symlink() or not source.is_dir() or any(p.is_symlink() for p in source.rglob("*")):
            raise ValueError("Unsafe template folder: " + folder)
    require_exact_package(args.template, args.archive, args.archive_sha256)
    framework_manifest = args.editor.parent / "Data/Resources/PackageManager/BuiltInPackages/com.unity.test-framework/package.json"
    framework = json.loads(framework_manifest.read_text())
    if framework.get("name") != "com.unity.test-framework":
        raise ValueError("Installed native test framework required")
    nunit = json.loads((framework_manifest.parent.parent / "com.unity.ext.nunit/package.json").read_text())
    if nunit.get("name") != "com.unity.ext.nunit":
        raise ValueError("Installed bundled NUnit required")
    args.output.mkdir(mode=0o700)
    project = args.output / "project"
    project.mkdir()
    started = time.monotonic()
    for folder in ("Assets", "Packages", "ProjectSettings", "Library"):
        subprocess.run(["cp", "-a", "--reflink=auto", str(args.template / folder), str(project)], check=True)
    # All intentional changes happen only in the new disposable copy.
    manifest = project / "Packages/manifest.json"
    packages = json.loads(manifest.read_text())
    packages["dependencies"]["com.unity.test-framework"] = framework["version"]
    manifest.write_text(json.dumps(packages, indent=2) + "\n")
    lock_file = project / "Packages/packages-lock.json"
    expected_lock = expected_bundled_lock(json.loads(lock_file.read_text()), framework, nunit, packages["dependencies"])
    cache = args.output / "copied-script-cache"
    cache.mkdir()
    for name in ("SourceAssetDB", "ArtifactDB", "Bee", "ScriptAssemblies"):
        source = project / "Library" / name
        if source.exists():
            shutil.move(str(source), str(cache / name))
    tests = project / "Assets/HprProductTests"
    if tests.exists():
        raise ValueError("QA test location collision")
    tests.mkdir()
    package_root = Path(__file__).resolve().parents[5] / "packages"
    staged = []
    for source in sorted(package_root.glob("*/Tests/EditMode")):
        asmdefs = list(source.glob("*.asmdef"))
        if len(asmdefs) != 1 or json.loads(asmdefs[0].read_text())["name"] not in EXPECTED_ASSEMBLIES:
            raise ValueError("Unexpected source test assembly")
        destination = tests / source.parents[1].name
        shutil.copytree(source, destination)
        staged.append(json.loads(asmdefs[0].read_text())["name"])
    if set(staged) != set(EXPECTED_ASSEMBLIES):
        raise ValueError("Incomplete canonical module tests")
    before = snapshot(project)
    (args.output / "protected-before.json").write_text(json.dumps(before, indent=2))
    command = [str(args.editor), "-batchmode", "-nographics", "-projectPath", str(project),
        "-runTests", "-testPlatform", "EditMode", "-assemblyNames", ";".join(EXPECTED_ASSEMBLIES),
        "-testResults", str(args.output / "test-results.xml"), "-logFile", str(args.output / "unity.log")]
    (args.output / "launch.json").write_text(json.dumps({"command": command,
        "archive_sha256": args.archive_sha256, "test_framework_version": framework["version"], "native_import_reused": str(args.import_receipt),
        "expected_assemblies": EXPECTED_ASSEMBLIES, "staged_source_sha256": {
            str(p.relative_to(tests)): digest(p) for p in tests.rglob("*") if p.is_file()}}, indent=2))
    require_exact_package(project, args.archive, args.archive_sha256)
    print("NATIVE_NUNIT_START", flush=True)
    try:
        result = subprocess.run(command, timeout=args.max_seconds - (time.monotonic() - started))
        native_exit = result.returncode
    except subprocess.TimeoutExpired:
        native_exit = -999
    result_file = args.output / "test-results.xml"
    verdict = classify_xml(native_exit, result_file.read_text() if result_file.is_file() else "")
    after = snapshot(project)
    changed = [name for name, value in before.items() if after.get(name) != value]
    lock_changed = "Packages/packages-lock.json" in changed
    try:
        resolved_lock = json.loads(lock_file.read_text())
    except (OSError, ValueError):
        resolved_lock = None
    changed = preserved_file_changes(before, after, resolved_lock, expected_lock)
    try:
        package_identity = verify_import(args.archive, project, args.archive_sha256)
    except (OSError, ValueError, tarfile.TarError) as error:
        package_identity = {"status": "FAIL", "issues": [str(error)]}
    passed = (verdict["passed"] and not changed and resolved_lock == expected_lock
              and package_identity["status"] == "PASS" and package_identity["script_payloads_verified"] == 55)
    receipt = {"status": "PASS" if passed else "FAIL", "actual_unity_editor_executed": True,
        "native_exit_code": native_exit, "archive_sha256": args.archive_sha256, "test_framework_version": framework["version"],
        "duration_seconds": round(time.monotonic() - started, 1), "nunit": verdict,
        "protected_files": len(before), "modified_original_files": changed,
        "copied_package_lock_updated": lock_changed, "package_lock_matches_planned_bundled_resolution": resolved_lock == expected_lock, "exact_packaged_scripts": package_identity.get("script_payloads_verified", 0),
        "vendor_script_mismatches": package_identity.get("script_payload_mismatches", []),
        "package_identity": package_identity, "rendered_usability_tested": False,
        "commercial_release_approved": False}
    (args.output / "RESULT.json").write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt), flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
