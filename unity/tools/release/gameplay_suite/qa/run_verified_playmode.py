"""Run the showcase in Play Mode only against the selected builder artifact."""
import argparse
import fcntl
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

from unity_imported_archive_identity import verify_import


ARCHIVE = "hpr-gameplay-systems-suite-candidate.unitypackage"
QA = Path(__file__).parent
VALIDATORS = ("HprGameplaySuitePlaymodeValidator.cs", "HprShowcasePlayAfterStartup.cs")
CHECKS = {
    "imported_scene_actual_playmode", "real_awake_and_scene_bindings",
    "collision_aware_character_motor", "automatic_enemy_chase",
    "composition_and_world_registry", "combat_and_typed_damage_event",
    "live_ability_and_stamina", "live_weapon_and_checkpoint_restore",
}


def builder_digest(archive):
    built = json.loads(archive.with_name("release-receipt.json").read_text())
    if (not isinstance(built, dict) or built.get("artifact") != archive.name
            or built.get("unity_editor_success") is not True):
        raise ValueError("The builder receipt does not identify a successful export of the selected archive")
    return built.get("sha256")


def verify_project(archive, project, digest):
    result = verify_import(archive, project, digest)
    if result["status"] != "PASS":
        raise ValueError("Imported project differs from the selected archive:\n" +
                         "\n".join(result["issues"]))


def stage_validators(project):
    folder = project / "Assets/Editor"
    if folder.is_symlink():
        raise ValueError(f"Refusing symlinked Editor folder: {folder}")
    folder_meta = folder.with_suffix(".meta")
    if folder_meta.is_symlink() or (not folder.exists() and folder_meta.exists()):
        raise ValueError(f"Preserving existing Editor folder metadata: {folder_meta}")
    pending = []
    for name in VALIDATORS:
        target = folder / name
        content = (QA / name).read_bytes()
        meta = target.with_suffix(".cs.meta")
        if meta.is_symlink() or (not target.exists() and meta.exists()):
            raise ValueError(f"Preserving existing validator metadata: {meta}")
        if not os.path.lexists(target):
            pending.append((target, content))
        elif target.is_symlink() or not target.is_file() or target.read_bytes() != content:
            raise ValueError(f"Preserving a different existing validator: {target}")
    folder.mkdir(exist_ok=True)
    for target, content in pending:
        with target.open("xb") as handle:
            handle.write(content)


def run_playmode(editor, release, project):
    receipt = release / "actual-playmode-receipt.txt"
    if os.path.lexists(receipt):
        raise FileExistsError(f"Refusing to replace the existing Play Mode receipt: {receipt}")
    archive = release / ARCHIVE
    digest = builder_digest(archive)
    verify_project(archive, project, digest)
    if not (project / "Assets/HPRGameplaySuite/Demo/GameplaySuiteShowcase.unity").is_file():
        raise ValueError("The imported package is missing the showcase scene")
    stage_validators(project)

    attempt = Path(tempfile.mkdtemp(prefix="playmode-", dir=release))
    raw = attempt / "native-checks.txt"
    log = release / "actual-playmode.unity.log"
    if os.path.lexists(log):
        log = attempt / log.name
    print(f"Unity Play Mode log: {log}", flush=True)
    subprocess.run([str(editor), "-batchmode", "-projectPath", str(project), "-executeMethod",
                    "HprShowcasePlayAfterStartup.Run", "-logFile", str(log)],
                   check=True, timeout=420, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   env=dict(os.environ, HPR_SUITE_PLAYMODE_RECEIPT=str(raw)))
    native_log = log.read_text(errors="replace")
    engine = re.search(r"^Initialize engine version: (\S+)", native_log, re.MULTILINE)
    if not engine or "HPR_QA_REAL_PLAYMODE_PASS" not in native_log.splitlines():
        raise ValueError(f"Missing Unity version or Play Mode completion marker: {log}")
    if re.search(r"^(?:[\w.]*Exception:|.*\berror CS\d{4}:)", native_log, re.MULTILINE):
        raise ValueError(f"Unity logged a managed exception or C# compiler error: {log}")
    checks = raw.read_text().splitlines()
    if sorted(checks) != sorted(name + "=PASS" for name in CHECKS):
        raise ValueError(f"Incomplete or unexpected Unity Play Mode results: {raw}")
    verify_project(archive, project, digest)
    if builder_digest(archive) != digest:
        raise ValueError("The selected release receipt changed during Play Mode")
    evidence = attempt / "verified-receipt.txt"
    evidence.write_text("\n".join([*checks, f"archive_sha256={digest}",
                                  f"unity_version={engine.group(1)}", f"unity_project={project}",
                                  f"unity_log={log}"]) + "\n")
    os.link(evidence, receipt)
    print(evidence.read_text(), end="")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--editor", required=True, type=Path)
    parser.add_argument("--release", required=True, type=Path)
    parser.add_argument("--project", required=True, type=Path)
    args = parser.parse_args()
    release = args.release.absolute()
    # The builder locks this directory while replacing its archive and receipt.
    directory = os.open(release, os.O_RDONLY | os.O_DIRECTORY)
    try:
        fcntl.flock(directory, fcntl.LOCK_EX | fcntl.LOCK_NB)
        run_playmode(args.editor, release, args.project.absolute())
    finally:
        os.close(directory)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.SubprocessError, tarfile.TarError) as error:
        sys.exit(f"Play Mode verification failed: {error}")
