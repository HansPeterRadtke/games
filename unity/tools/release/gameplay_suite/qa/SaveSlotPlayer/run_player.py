"""Build a verified package's showcase and test its normal save slot across two Linux Players."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

FIXTURE = Path(__file__).resolve().parent
sys.path.insert(0, str(FIXTURE.parent))
from NativeEditMode.run_native_editmode import digest, snapshot
from unity_imported_archive_identity import verify_import


def check(condition, message):
    if not condition:
        raise ValueError(message)


def run_player(binary, profile, phase, log):
    env = dict(os.environ, XDG_CONFIG_HOME=str(profile), HPR_SAVE_PLAYER_PHASE=phase)
    cmd = [str(binary), "-batchmode", "-nographics", "-logFile", str(log)]
    with subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT) as proc:
        try:
            code = proc.wait(timeout=75)
        except subprocess.TimeoutExpired:
            proc.kill()
            raise
    check(code == 0, f"{phase} Player exited {code}; inspect {log}")
    prefix = "HPR_SAVE_PLAYER_OBSERVATION "
    rows = [line[len(prefix):] for line in log.read_text().splitlines() if line.startswith(prefix)]
    check(len(rows) == 1, f"Expected exactly one {phase} result")
    result = json.loads(rows[0])
    check(result["phase"] == phase and result["scene"] ==
          "Assets/HPRGameplaySuite/Demo/GameplaySuiteShowcase.unity", "Unexpected phase or scene")
    result["pid"] = proc.pid
    return result


def run(args):
    template, archive, output = (path.resolve() for path in (args.template, args.archive, args.output))
    check(not output.is_relative_to(template) and not output.is_relative_to(FIXTURE.parents[5]),
          "Choose a fresh output directory outside the project and source repository")
    old = snapshot(template)
    check(verify_import(archive, template, args.sha256)["status"] == "PASS", "Wrong source package")
    output.mkdir(mode=0o700)
    project = output / "project"
    project.mkdir()
    for name in ("Assets", "Packages", "ProjectSettings", "Library"):
        folder = template / name
        check(folder.is_dir() and not folder.is_symlink() and not any(p.is_symlink() for p in folder.rglob("*")),
              f"Cannot stage {folder}")
        subprocess.run(["cp", "-a", "--reflink=auto", str(folder), str(project)], check=True)
    check(snapshot(project) == old, "Project copy is incomplete")
    for source, target in (("SaveSlotPlayerBuild.cs", "Editor"), ("SaveSlotPlayerProbe.cs", "SaveSlotPrivateQA")):
        dest = project / "Assets" / target / source
        check(not dest.exists() and not dest.with_suffix(".cs.meta").exists(), f"QA fixture collision at {dest}")
        dest.parent.mkdir(exist_ok=True)
        shutil.copyfile(FIXTURE / source, dest)
    staged = snapshot(project)

    binary = output / "build" / "HprSave.x86_64"
    binary.parent.mkdir()
    build_log = output / "build.log"
    subprocess.run([str(args.editor), "-batchmode", "-nographics", "-quit", "-job-worker-count", "2",
                    "-projectPath", str(project), "-executeMethod", "SaveSlotPlayerBuild.Run",
                    "-logFile", str(build_log)], env=dict(os.environ, HPR_SAVE_PLAYER_BINARY=str(binary)),
                   check=True, timeout=900, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    check(binary.is_file() and "HPR_SAVE_PLAYER_BUILD_PASS" in build_log.read_text().splitlines(),
          "Missing native build proof")
    profile = output / "profile"
    profile.mkdir()
    written = run_player(binary, profile, "write", output / "write.log")
    slot = Path(written["slot"]).resolve()
    check(slot.is_relative_to(profile) and slot.name == "demo-slot.json", "Unexpected default save path")
    saved_bytes = slot.read_bytes()
    payload = json.loads(saved_bytes)
    check(payload["SchemaVersion"] == 3 and payload["Player"]["health"] == written["finalHealth"]
          and payload["Weapon"]["MagazineAmmo"] == written["finalAmmo"], "Disk payload differs from game state")
    loaded = run_player(binary, profile, "read", output / "read.log")
    check(written["pid"] != loaded["pid"] and written["slot"] == loaded["slot"], "Expected restart at same slot")
    for field in ("version", "initialHealth", "initialAmmo", "finalHealth", "finalAmmo"):
        check(written[field] == loaded[field], f"Writer and reader disagree on {field}")
    check(slot.read_bytes() == saved_bytes and Path(str(slot) + ".writing").read_text() == "private neighboring file",
          "Restore changed the save or its neighbor")
    damaged_profile = output / "damaged-profile"
    damaged_slot = damaged_profile / slot.relative_to(profile)
    damaged_slot.parent.mkdir(parents=True)
    damaged_slot.write_bytes(b'{"Player":')
    shutil.copyfile(str(slot) + ".writing", str(damaged_slot) + ".writing")
    rejected = run_player(binary, damaged_profile, "reject", output / "reject.log")
    check(Path(rejected["slot"]) == damaged_slot and damaged_slot.read_bytes() == b'{"Player":'
          and rejected["initialHealth"] == rejected["finalHealth"] == written["initialHealth"]
          and rejected["initialAmmo"] == rejected["finalAmmo"] == written["initialAmmo"],
          "Rejected save should leave the damaged slot and new encounter intact")
    after = snapshot(project)
    check(all(after.get(k) == v for k, v in staged.items()), "A staged source or setting changed")
    check(snapshot(template) == old, "A source template file changed")
    identity = verify_import(archive, project, args.sha256)
    check(identity["status"] == "PASS", "Packaged assets changed during Player QA")
    result = dict(status="PASS", write=written, read=loaded, reject=rejected, binary_sha256=digest(binary),
                  slot_sha256=digest(slot), package_identity=identity, template_files=len(old),
                  staged_files=len(staged), added_project_files=sorted(after.keys() - staged.keys()))
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("template", "archive", "output", "editor"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    run(parser.parse_args())
