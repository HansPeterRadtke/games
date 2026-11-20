#!/usr/bin/env python3
"""Private QA: import an updated HPR archive into an existing Unity game project.

The base project and all original artifacts are read-only. Work occurs in a
new disposable project under /data/tmp. No marketplace or account API calls.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unity_call(unity: Path, project: Path, out: Path, label: str,
               *, execute_method: str | None = None,
               archive: Path | None = None,
               environment: dict[str, str]) -> None:
    command = [str(unity), "-batchmode", "-nographics", "-quit",
               "-projectPath", str(project)]
    if archive is not None:
        command += ["-importPackage", str(archive)]
    if execute_method is not None:
        command += ["-executeMethod", execute_method]
    log = out / (label + ".unity.log")
    command += ["-logFile", str(log)]
    finished = subprocess.run(command, env=environment,
                              stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL,
                              timeout=600, check=False)
    if finished.returncode != 0:
        raise RuntimeError("Unity failed " + label + " with exit " +
                           str(finished.returncode) + ". Inspect " + str(log))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-project", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--unity", type=Path, required=True)
    args = parser.parse_args()
    base = args.baseline_project.resolve()
    dest = args.project.resolve()
    candidate = args.candidate.resolve()
    if not (base / "Assets/HPRGameplaySuite").is_dir():
        raise ValueError("Baseline is not a verified imported Unity game project")
    if dest.exists() or not str(dest).startswith("/data/tmp/"):
        raise ValueError("QA destination must be unused and under /data/tmp")
    if not candidate.is_file() or candidate.suffix != ".unitypackage":
        raise ValueError("Candidate Unity buyer archive missing")
    if not args.unity.is_file():
        raise FileNotFoundError(args.unity)
    args.release.mkdir(parents=True, exist_ok=True)
    output = args.release.resolve()

    shutil.copytree(base, dest)
    customer = dest / "Assets/ExternalCustomerGame"
    customer.mkdir(parents=True, exist_ok=True)
    notes = customer / "customer-owned-data.txt"
    notes.write_text(
        "A simulated customer's unrelated scene and game files must remain unchanged.\n",
        encoding="utf-8")
    code = customer / "ExistingPlayerIntegration.cs"
    code.write_text('''using UnityEngine;
using HPR;

namespace ExternalCustomerGame
{
    public sealed class ExistingPlayerIntegration : MonoBehaviour
    {
        public int ReadInventory(IInventoryService inventory, string itemId)
        {
            return inventory.GetQuantity(itemId);
        }
    }
}
''', encoding="utf-8")
    before = {x.name: digest(x) for x in (notes, code)}

    env = os.environ.copy()
    env.update({
        "HOME": "/home/hans", "USER": "hans", "LOGNAME": "hans",
        "DISPLAY": ":1", "XAUTHORITY": "/home/hans/.Xauthority",
        "XDG_RUNTIME_DIR": "/run/user/1000",
        "DBUS_SESSION_BUS_ADDRESS": "unix:path=/run/user/1000/bus",
    })
    unity_call(args.unity, dest, output, "upgrade-import",
               archive=candidate, environment=env)
    for file in (notes, code):
        if digest(file) != before[file.name]:
            raise RuntimeError("Upgrade modified customer-owned file: " + file.name)
    # Private test harness is appended only after importing the buyer package.
    editor = dest / "Assets/Editor"
    editor.mkdir(parents=True, exist_ok=True)
    shutil.copy2(HERE / "HprGameplaySuiteCleanroomValidator.cs", editor)
    receipt_scene = output / "upgrade-existing-scene-qa.txt"
    if receipt_scene.exists():
        raise FileExistsError(receipt_scene)
    env["HPR_SUITE_CLEANROOM_RECEIPT"] = str(receipt_scene)
    unity_call(args.unity, dest, output, "upgrade-scene",
               execute_method="HprGameplaySuiteCleanroomValidator.Run",
               environment=env)
    if not receipt_scene.is_file():
        raise RuntimeError("Missing actual imported-scene QA after upgrade")
    shutil.copy2(HERE / "HprGameplaySuiteRuntimeSmokeValidator.cs", editor)
    receipt_runtime = output / "upgrade-existing-runtime-qa.txt"
    if receipt_runtime.exists():
        raise FileExistsError(receipt_runtime)
    env["HPR_SUITE_SMOKE_RECEIPT"] = str(receipt_runtime)
    env["HPR_SUITE_SMOKE_JSON"] = str(output / "upgrade-temp-save.json")
    unity_call(args.unity, dest, output, "upgrade-runtime",
               execute_method="HprGameplaySuiteRuntimeSmokeValidator.Run",
               environment=env)
    if not receipt_runtime.is_file():
        raise RuntimeError("Missing actual imported runtime QA after upgrade")
    if any(digest(file) != before[file.name] for file in (notes, code)):
        raise RuntimeError("Upgrade/test altered customer-owned game files")
    receipt = {
        "existing_customer_game_files_unchanged": True,
        "actual_unity_package_import": True,
        "integrated_scene_and_runtime_check": True,
        "unity_editor": args.unity.name,
        "source_archive_sha256": digest(candidate),
        "base_game_copied": True,
    }
    final = output / "upgrade-acceptance.json"
    if final.exists():
        raise FileExistsError(final)
    final.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print("UPGRADE_INTO_EXISTING_CUSTOM_GAME_VERIFIED")


if __name__ == "__main__":
    main()
