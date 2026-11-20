"""Exercise pointer aiming in a prebuilt Linux showcase Player with PointerAimPlayerProbe staged."""
import argparse
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time

BASE_CASES = ["native", "disabled", "absent", "nan-x", "infinite-y", "finite"]
RENDERED_CASES = BASE_CASES + ["left", "right", "mouse-left", "mouse-right"]
CAMERA_WARNING = "Screen position out of view frustum"


def player_command(binary, log):
    return [str(binary), "-screen-fullscreen", "0", "-screen-width", "960",
            "-screen-height", "540", "-logFile", str(log)]


def xdotool(*args):
    return subprocess.run(["xdotool", *args], capture_output=True, text=True, timeout=3)


def click_chase_control(window, cancel):
    # The Pause/Resume button occupies this point in the 960 x 540 showcase HUD.
    xdotool("mousemove", "--window", window, "454", "215").check_returncode()
    time.sleep(.15)
    xdotool("mousedown", "1").check_returncode()
    try:
        time.sleep(.2)
        if cancel:
            xdotool("mousemove", "--window", window, "845", "465").check_returncode()
            time.sleep(.2)
    finally:
        xdotool("mouseup", "1").check_returncode()


def drive_mouse(binary, folder):
    authority = folder / "Xauthority"
    if os.environ.get("XAUTHORITY") != str(authority) or not authority.is_file():
        raise ValueError("Desktop input requires the runner's private X server")
    log = folder / "player.log"
    env = dict(os.environ, XDG_CONFIG_HOME=str(folder / "profile"), HPR_POINTER_DESKTOP="1")
    with (folder / "console.log").open("x") as console:
        proc = subprocess.Popen(player_command(binary, log) + ["-force-glcore"],
                                env=env, stdout=console, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + 75
            dispatched = set()
            while proc.poll() is None:
                if time.monotonic() > deadline:
                    raise TimeoutError(f"Rendered Player timed out. Inspect {log}")
                # The outer invocation created this X server solely for this Player.
                windows = xdotool("search", "--onlyvisible", "--name", ".").stdout.splitlines()
                if len(windows) == 1 and log.is_file():
                    window = windows[0]
                    xdotool("windowfocus", window)
                    current_log = log.read_text(errors="replace")
                    requests = re.findall(r"^HPR_POINTER_MOVE (mouse-left|mouse-right) (\d+) (\d+)$",
                                          current_log, re.MULTILINE)
                    for stage, x, y in requests:
                        if stage not in dispatched:
                            xdotool("mousemove", "--window", window, x, y).check_returncode()
                            dispatched.add(stage)
                    for action in re.findall(r"^HPR_HUD_ACTION (cancel|pause|resume)$", current_log, re.MULTILINE):
                        if action not in dispatched:
                            click_chase_control(window, action == "cancel")
                            dispatched.add(action)
                time.sleep(.1)
            if proc.returncode:
                raise RuntimeError(f"Rendered Player exited {proc.returncode}. Inspect {log}")
            if dispatched != {"mouse-left", "mouse-right", "cancel", "pause", "resume"}:
                raise ValueError("Missing desktop mouse movements or HUD clicks")
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()


def verify_log(path, graphics, stages):
    log = path.read_text()
    rows = [line for line in log.splitlines() if line.startswith("HPR_POINTER_CASE ")]
    actual = []
    for row in rows:
        fields = dict(field.split("=", 1) for field in row.split()[1:])
        if fields["graphics"] != graphics or fields["pass"] != "True" or fields["warnings"] != "0":
            raise ValueError(row)
        stage = fields["stage"]
        reads = int(fields["reads"])
        if (stage == "disabled" and reads != 0) or (stage != "disabled" and reads <= 0):
            raise ValueError(f"Unexpected input polling: {row}")
        if fields["available"] not in {"True", "False"}:
            raise ValueError(f"Missing availability measurement: {row}")
        available = fields["available"] == "True"
        if stage != "native" and available != (stage not in {"disabled", "absent"}):
            raise ValueError(f"Incorrect pointer availability: {row}")
        x, y = (float(v) for v in fields["pointer"].strip("()").split(","))
        valid = available and math.isfinite(x) and math.isfinite(y)
        if (stage == "nan-x" and not (math.isnan(x) and math.isfinite(y)) or
                stage == "infinite-y" and not (math.isfinite(x) and math.isinf(y)) or
                stage in {"finite", "left", "right", "mouse-left", "mouse-right"} and not valid):
            raise ValueError(f"Test did not supply the requested coordinates: {row}")
        if not valid and fields["stayed"] != "True":
            raise ValueError(f"Missing or invalid pointer turned the character: {row}")
        if stage in {"left", "right", "mouse-left", "mouse-right"} and fields["aimed"] != "True":
            raise ValueError(f"Character missed the requested direction: {row}")
        actual.append(stage)
    if actual != stages or log.splitlines().count("HPR_POINTER_DONE failures=0") != 1:
        raise ValueError(f"Incomplete Player test in {path}")
    if CAMERA_WARNING in log or "HPR_POINTER_TEST_INVALID" in log or "Exception:" in log:
        raise ValueError(f"Player diagnostic in {path}")
    hud_rows = [row for row in log.splitlines() if row.startswith("HPR_HUD_CASE ")]
    expected_hud = [
        "HPR_HUD_CASE cancel released=True live=True pass=True",
        "HPR_HUD_CASE pause released=True live=False pass=True",
        "HPR_HUD_CASE resume released=True live=True pass=True",
    ] if graphics == "OpenGLCore" else []
    if hud_rows != expected_hud:
        raise ValueError(f"Unexpected HUD results in {path}: {hud_rows}")
    return rows + hud_rows


def run(binary, output):
    output.mkdir(mode=0o700)
    results = {}
    for label in ("headless", "rendered"):
        folder = output / label
        folder.mkdir()
        (folder / "profile").mkdir()
        log = folder / "player.log"
        if label == "headless":
            env = dict(os.environ, XDG_CONFIG_HOME=str(folder / "profile"), HPR_POINTER_DESKTOP="0")
            for key in ("DISPLAY", "WAYLAND_DISPLAY", "XAUTHORITY"):
                env.pop(key, None)
            with (folder / "console.log").open("x") as console:
                # The legacy Linux Player needs an X display even with a null graphics device.
                cmd = ["xvfb-run", "-a", "-s", "-screen 0 1024x768x24", "timeout",
                       "--kill-after=5s", "75s", *player_command(binary, log),
                       "-batchmode", "-nographics"]
                subprocess.run(cmd, check=True,
                               timeout=95, env=env, stdout=console, stderr=subprocess.STDOUT)
            results[label] = verify_log(log, "Null", BASE_CASES)
        else:
            authority = folder / "Xauthority"
            authority.touch(mode=0o600, exist_ok=False)
            subprocess.run(["xvfb-run", "-a", "-f", str(authority), "-s", "-screen 0 1024x768x24", sys.executable,
                            str(Path(__file__).resolve()), "--private-display", "--binary", str(binary),
                            "--output", str(folder)], check=True,
                           env=dict(os.environ, LIBGL_ALWAYS_SOFTWARE="1", __GLX_VENDOR_LIBRARY_NAME="mesa"))
            results[label] = verify_log(log, "OpenGLCore", RENDERED_CASES)
    (output / "result.json").write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--private-display", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.private_display:
        drive_mouse(args.binary.resolve(strict=True), args.output.resolve(strict=True))
    else:
        run(args.binary.resolve(strict=True), args.output.resolve())
