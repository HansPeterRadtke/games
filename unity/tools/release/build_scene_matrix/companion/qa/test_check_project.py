"""Buyer process acceptance for a fresh, read-only saved-project scene check.

Original native Unity fixtures are read without changes. Every deliberately
changed input is a disposable subset clone. The synthetic timestamp controls
alter only the documented first length-prefixed UTC field after checking its
magic, length and ISO shape; they are not presented as native captures.
No Unity Editor is invoked, and no supported-version expansion is implied.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import re
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
import time


INHERITED = "Assets/HPRPrivateMatrixQA/Inherited.asset"
OVERRIDE = "Assets/HPRPrivateMatrixQA/Override.asset"
START = "Assets/HPRPrivateMatrixQA/A/Start.unity"
OTHER_START = "Assets/HPRPrivateMatrixQA/B/Start.unity"
LEVEL = "Assets/HPRPrivateMatrixQA/Level.unity"
SETTINGS = "ProjectSettings/EditorBuildSettings.asset"
VERSION = "ProjectSettings/ProjectVersion.txt"


def run(dll, native, native_csv, empty2022, out):
    out.mkdir()
    count = 0

    def check(ok, label):
        nonlocal count
        if not ok:
            raise AssertionError(label)
        count += 1
        print("PASS", label, flush=True)

    def dig(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    originals = [native / VERSION, native / SETTINGS, native_csv,
                 empty2022 / VERSION, empty2022 / SETTINGS]
    originals += sorted(p for p in (native / "Assets/HPRPrivateMatrixQA").rglob("*")
                        if p.is_file())
    native_hashes = {str(p): dig(p) for p in originals}
    binaries = [dll, dll.with_suffix(".deps.json"), dll.with_suffix(".runtimeconfig.json")]
    binary_hashes = {p.name: dig(p) for p in binaries}

    def tree_state(root):
        """Never read pipes/links while establishing our own no-write controls."""
        state = {}
        for p in [root, *sorted(root.rglob("*"))]:
            info = p.lstat()
            kind = stat.S_IFMT(info.st_mode)
            key = str(p.relative_to(root))
            if stat.S_ISREG(info.st_mode):
                state[key] = (kind, info.st_mode, info.st_size, info.st_mtime_ns, dig(p))
            elif stat.S_ISLNK(info.st_mode):
                state[key] = (kind, os.readlink(p))
            else:
                state[key] = (kind, info.st_mode)
        return state

    def invoke(*args, timeout=15, usage=False, readonly=True):
        before = tree_state(out) if readonly else None
        result = subprocess.run(["dotnet", str(dll), *map(str, args)],
                                capture_output=True, text=True, timeout=timeout)
        if usage:
            check(result.returncode == 2 and not result.stdout
                  and "Usage:" in result.stderr, "invalid arguments give exit two and stderr usage")
        else:
            check(not result.stderr, "valid command form emits no unexpected stderr")
        if readonly:
            check(tree_state(out) == before,
                  "check/compare leaves disposable project, references and output inventory unchanged")
        return result

    def capture(project, selector, dest):
        result = invoke("capture", project, selector, dest, readonly=False)
        data = json.loads(result.stdout)
        check(result.returncode == 0 and dest.is_file()
              and data["status"] == "SAVED_PROJECT_SNAPSHOT_CREATED",
              "test baseline created through the actual capture command")
        return data

    def checked(reference, project, selector="global", code=0, form="json", timeout=15):
        args = ["check", reference, project, selector]
        if form is not None:
            args += ["--format", form]
        result = invoke(*args, timeout=timeout)
        check(result.returncode == code, "fresh check returns expected exit " + str(code))
        if form == "json":
            data = json.loads(result.stdout)
            check(isinstance(data, dict) and data["tool_version"] == "0.2.0",
                  "JSON is one report from the tested release version")
            expected = "INVALID_INPUT_OR_READ_ERROR" if code == 2 else (
                "MATCH_WITHOUT_WARNINGS" if code == 0 else "REVIEW_REQUIRED")
            check(data["status"] == expected, "JSON status matches process exit")
            if code != 2:
                check(data["current_saved_configuration_read_this_run"] is True
                      and data["current_configuration_source"] == "saved_project_read_this_run",
                      "report explicitly identifies a fresh saved-project read")
                check(data["project_identity_verified"] is False
                      and data["current_snapshot_freshness_verified"] is False,
                      "fresh saved read does not claim project identity or live snapshot freshness")
                check(data["project_path"] == str(project.resolve())
                      and data["profile_selector"] == selector,
                      "report names the actual selected project and list")
                started = datetime.fromisoformat(data["current_read_started_utc"])
                ended = datetime.fromisoformat(data["current_read_completed_utc"])
                check(started <= ended and ended == datetime.fromisoformat(data["current"]["captured_utc"]),
                      "fresh-read timestamps are ordered and match the current comparison")
            return data
        check(result.stdout.startswith("Scene Gate: "), "text begins with a plain result")
        check(not result.stdout.lstrip().startswith("{"), "text mode does not leak JSON")
        check("\x1b" not in result.stdout and "\u202e" not in result.stdout,
              "text has no raw terminal escape or bidirectional format controls")
        if code == 2:
            check("INPUT ERROR" in result.stdout, "text read error is explicit")
        else:
            check(("MATCH" if code == 0 else "REVIEW REQUIRED") in result.stdout.splitlines()[0],
                  "text status agrees with process exit")
            check("Scope: saved files only." in result.stdout
                  and "approval of the reference" in result.stdout,
                  "text limits the result to saved files and does not imply reference approval")
        return result.stdout

    def compared(a, b, code, timeout=15):
        result = invoke("compare", a, b, timeout=timeout)
        check(result.returncode == code, "snapshot comparison returns expected exit " + str(code))
        return json.loads(result.stdout)

    def substantive(data):
        fields = ["status", "profile_identifier_changed", "list_source_changed",
                  "profile_asset_path_changed", "declared_entry_sequence_changed",
                  "first_differing_entry", "reference_has_no_enabled_scenes",
                  "current_has_no_enabled_scenes", "current_capture_precedes_reference",
                  "changed_scene_identities", "scene_identities_with_warnings", "findings"]
        value = {k: data[k] for k in fields}
        for role in ["reference", "current"]:
            value[role] = {k: v for k, v in data[role].items() if k != "captured_utc"}
        return value

    def shift_stamp(source, dest, year):
        raw = source.read_bytes()
        check(raw[:9] == b"HPRSCENE1" and len(raw) > 13, "timestamp control uses documented snapshot magic")
        size = struct.unpack_from("<i", raw, 9)[0]
        old = raw[13:13 + size].decode("ascii")
        check(re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{7}\+00:00", old) is not None,
              "timestamp control validates exact round-trip UTC field shape")
        stamp = f"{year:04d}" + old[4:]
        datetime.fromisoformat(stamp)
        changed = stamp.encode("ascii")
        check(len(changed) == size, "timestamp control preserves field length")
        dest.write_bytes(raw[:13] + changed + raw[13 + size:])
        check(dest.read_bytes()[13 + size:] == raw[13 + size:],
              "synthetic time control preserves all profile and scene bytes")

    global_ref = out / "actual-global.hpr-scenes"
    inherited_ref = out / "actual-inherited.hpr-scenes"
    override_ref = out / "actual-override.hpr-scenes"
    empty_ref = out / "actual-2022-empty.hpr-scenes"
    capture(native, "global", global_ref)
    capture(native, INHERITED, inherited_ref)
    capture(native, OVERRIDE, override_ref)
    capture(empty2022, "global", empty_ref)

    receipts = {}
    same = checked(global_ref, native)
    check(same["current"]["first_enabled_scene"] == START
          and same["current"]["enabled_entries"] == 2
          and same["unity_version"] == "6000.6.8f1", "real nonempty native global list is identified")
    default_text = checked(global_ref, native, form=None)
    explicit_text = checked(global_ref, native, form="text")
    for text in (default_text, explicit_text):
        check("Launch scene: " + START in text and "Selected list: global" in text
              and "List source: Shared scene list" in text,
              "default and explicit text reveal launch scene, selector and source")
    compared_same = compared(global_ref, global_ref, 0)
    check(substantive(same) == substantive(compared_same),
          "fresh check and snapshot compare share unchanged substantive comparison semantics")
    inherited = checked(inherited_ref, native, INHERITED)
    check(inherited["current"]["source"] == "Inherits global scenes"
          and inherited["current"]["first_enabled_scene"] == START
          and inherited["current"]["enabled_entries"] == 2,
          "inherited profile ignores its unused custom B/Start row")
    override = checked(override_ref, native, OVERRIDE, code=1)
    check(override["current"]["source"] == "Overrides global scenes"
          and override["current"]["first_enabled_scene"] == LEVEL
          and not override["declared_entry_sequence_changed"]
          and override["scene_identities_with_warnings"] == 2,
          "matching override still requires review of its two ambiguous enabled names")
    other_profile = checked(global_ref, native, INHERITED, code=1)
    check(other_profile["profile_identifier_changed"] and other_profile["list_source_changed"]
          and not other_profile["declared_entry_sequence_changed"],
          "wrong valid profile is reviewable identity/source drift even with identical effective rows")
    empty = checked(empty_ref, empty2022, code=1)
    check(empty["reference_has_no_enabled_scenes"] and empty["current_has_no_enabled_scenes"]
          and empty["current"]["first_enabled_scene"] == "(none)",
          "matching genuine empty Unity 2022 list is not certified")
    empty_text = checked(empty_ref, empty2022, code=1, form=None)
    check("Launch scene: (none)" in empty_text and "no enabled scenes" in empty_text,
          "empty text explains the missing launch scene")
    old_ref, future_ref = out / "old.hpr-scenes", out / "future.hpr-scenes"
    shift_stamp(global_ref, old_ref, 2000)
    shift_stamp(global_ref, future_ref, 2100)
    check(not checked(old_ref, native)["current_capture_precedes_reference"],
          "old valid reference has no invented expiry")
    check(checked(future_ref, native, code=1)["current_capture_precedes_reference"],
          "future reference timestamp is explicitly reviewable")
    check("reference capture time is later" in checked(future_ref, native, code=1, form=None),
          "future timestamp warning is visible in text")
    receipts["native_matching_json"] = same
    receipts["native_matching_text"] = default_text
    receipts["native_override_warnings"] = override

    with tempfile.TemporaryDirectory(prefix="fresh-check-copies-", dir=out) as temporary:
        tmp = Path(temporary)

        def clone(name):
            p = tmp / name
            (p / "ProjectSettings").mkdir(parents=True)
            (p / "Assets").mkdir()
            for relative in (VERSION, SETTINGS):
                shutil.copy2(native / relative, p / relative)
            shutil.copytree(native / "Assets/HPRPrivateMatrixQA", p / "Assets/HPRPrivateMatrixQA")
            return p

        def list_blocks(p):
            text = (p / SETTINGS).read_text()
            match = re.search(r"(  m_Scenes:\n)((?:  - enabled: [01]\n    path: [^\n]*\n    guid: [0-9a-f]{32}\n)+)", text)
            if match is None:
                raise AssertionError("Expected documented native three-line scene rows")
            rows = re.findall(r"  - enabled: [01]\n    path: [^\n]*\n    guid: [0-9a-f]{32}\n", match[2])
            return text, match, rows

        def replace_rows(p, transform):
            text, match, rows = list_blocks(p)
            changed = transform(rows)
            (p / SETTINGS).write_text(text[:match.start(2)] + "".join(changed) + text[match.end(2):])

        p = clone("stale-current-project")
        stale = tmp / "old-current.hpr-scenes"
        capture(p, "global", stale)
        replace_rows(p, lambda rows: [rows[0].replace("enabled: 1", "enabled: 0"), *rows[1:]])
        prior = compared(global_ref, stale, 0)
        fresh = checked(global_ref, p, code=1)
        check(prior["status"] == "MATCH_WITHOUT_WARNINGS"
              and fresh["current"]["first_enabled_scene"] == LEVEL
              and fresh["first_differing_entry"]["list_index"] == 0,
              "stale snapshot comparison passes while fresh project check catches the changed launch scene")
        new_snapshot = tmp / "fresh-current.hpr-scenes"
        capture(p, "global", new_snapshot)
        check(substantive(fresh) == substantive(compared(global_ref, new_snapshot, 1)),
              "fresh check agrees with independently captured changed snapshot")
        text = checked(global_ref, p, code=1, form=None)
        check("Launch scene: " + LEVEL in text and "Reference launch scene: " + START in text
              and "First differing declared entry 1:" in text,
              "changed launch and first meaningful difference are visible")
        receipts["stale_snapshot_contrast"] = {"compare": prior, "check": fresh, "text": text}

        p = clone("disabled-row-moved-first")
        replace_rows(p, lambda rows: [rows[1], rows[0], rows[2]])
        moved = checked(global_ref, p, code=1)
        check(moved["declared_entry_sequence_changed"] and moved["changed_scene_identities"] == 0
              and moved["current"]["first_enabled_scene"] == START,
              "disabled-only movement is detected without changing the enabled launch scene")
        disabled_ref = tmp / "disabled-first-reference.hpr-scenes"
        capture(p, "global", disabled_ref)
        check(checked(disabled_ref, p)["current"]["first_enabled_scene"] == START,
              "matching list with disabled first row still chooses first enabled scene")

        p = clone("inheritance-changed")
        profile = p / INHERITED
        profile.write_text(profile.read_text().replace("m_OverrideGlobalSceneList: 0", "m_OverrideGlobalSceneList: 1", 1))
        changed = checked(inherited_ref, p, INHERITED, code=1)
        check(changed["list_source_changed"] and not changed["profile_identifier_changed"]
              and changed["current"]["first_enabled_scene"] == OTHER_START,
              "same profile changing to override uses its actual stored list")
        p = clone("profile-identity-changed")
        metadata = p / (INHERITED + ".meta")
        metadata.write_text(re.sub(r"(?m)^guid: [0-9a-f]{32}$", "guid: " + "a" * 32, metadata.read_text()))
        check(checked(inherited_ref, p, INHERITED, code=1)["profile_identifier_changed"],
              "same profile path with different metadata identity requests review")

        for name, relative in [("scene-missing", START), ("scene-metadata-missing", START + ".meta")]:
            p = clone(name)
            (p / relative).unlink()
            data = checked(global_ref, p, code=1)
            check(data["scene_identities_with_warnings"] >= 1
                  and any(row["warning"] for row in data["findings"]),
                  "missing listed scene or metadata cannot pass")
        p = clone("all-disabled")
        replace_rows(p, lambda rows: [row.replace("enabled: 1", "enabled: 0") for row in rows])
        check(checked(global_ref, p, code=1)["current_has_no_enabled_scenes"],
              "all-disabled current list requests review")

        p = clone("project with spaces")
        checked(global_ref, p)
        controls = clone("control-\x1b[31m\nINJECTED\u202e\U000e0001")
        text = checked(global_ref, controls, form=None)
        check(r"\u001b" in text and r"\u000a" in text and r"\u202e" in text
              and r"\U000e0001" in text and "\U000e0001" not in text,
              "successful text escapes input-derived terminal, newline and bidi controls")
        text = checked(global_ref, p, "Assets/\x1b[31m\nINJECTED.asset", code=2, form=None)
        check(r"\u001b" in text and r"\u000a" in text,
              "error text also escapes hostile selector controls")

        p = clone("invalid-controls")
        missing_ref = tmp / "absent.hpr-scenes"
        checked(missing_ref, p, code=2)
        checked(missing_ref, p, code=2, form=None)
        corrupt = tmp / "corrupt.hpr-scenes"
        corrupt.write_bytes(b"not a snapshot")
        checked(corrupt, p, code=2)
        truncated = tmp / "truncated.hpr-scenes"
        truncated.write_bytes(global_ref.read_bytes()[:-1])
        checked(truncated, p, code=2)
        checked(global_ref, tmp / "absent-project", code=2)
        for selector in ["Assets/Missing.asset", "../outside.asset", "Assets/../Outside.asset",
                         str((p / INHERITED).resolve()), "Assets/HPRPrivateMatrixQA/Level.unity"]:
            checked(global_ref, p, selector, code=2)
        for args in [[], [global_ref], [global_ref, p],
                     [global_ref, p, "global", "--format"],
                     [global_ref, p, "global", "--format", "xml"],
                     [global_ref, p, "global", "--format", "JSON"],
                     [global_ref, p, "global", "--unknown", "json"],
                     [global_ref, p, "global", "--format", "json", "--format", "text"]]:
            invoke("check", *args, usage=True)

        p = clone("unsupported-version")
        (p / VERSION).write_text("m_EditorVersion: 6000.99.0f1\n")
        checked(global_ref, p, code=2)
        p = clone("malformed-settings")
        (p / SETTINGS).write_text("Not a saved Unity scene list\n")
        checked(global_ref, p, code=2)
        p = clone("linked-scene")
        scene = p / START
        scene.unlink()
        scene.symlink_to(native / START)
        checked(global_ref, p, code=2)

        # FIFOs must be rejected as non-regular paths before any blocking open.
        # A timeout is an actual acceptance failure; subprocess.run kills only
        # its own child, and finally removes only this control's exact FIFO.
        fifo_count = 0
        def fifo_control(path, action):
            nonlocal fifo_count
            if path.exists():
                path.unlink()
            os.mkfifo(path)
            before = time.monotonic()
            try:
                action()
                check(time.monotonic() - before < 5,
                      "stable non-regular input is rejected promptly before a blocking read")
                fifo_count += 1
            finally:
                path.unlink(missing_ok=True)

        fifo = tmp / "reference-fifo.hpr-scenes"
        fifo_control(fifo, lambda: checked(fifo, native, code=2, timeout=5))
        fifo_control(fifo, lambda: compared(global_ref, fifo, 2, timeout=5))
        for name, relative, selector in [
            ("version", VERSION, "global"), ("settings", SETTINGS, "global"),
            ("scene-meta", START + ".meta", "global"), ("listed-scene", START, "global"),
            ("profile", INHERITED, INHERITED), ("profile-meta", INHERITED + ".meta", INHERITED)
        ]:
            p = clone("fifo-" + name)
            fifo_control(p / relative, lambda p=p, selector=selector:
                         checked(global_ref, p, selector, code=2, timeout=5))
        check(fifo_count == 8, "all eight stable FIFO boundary controls completed")

    check(native_hashes == {p: dig(Path(p)) for p in native_hashes},
          "all original native fixture and CSV bytes unchanged")
    check(binary_hashes == {p.name: dig(p) for p in binaries},
          "same executable and runtime metadata throughout acceptance")
    (out / "fresh-check-examples.json").write_text(json.dumps(receipts, indent=2) + "\n")
    (out / "native-source-read-only-hashes.json").write_text(json.dumps(native_hashes, indent=2) + "\n")
    (out / "fresh-project-process-receipt.json").write_text(json.dumps({
        "status": "HPR_FRESH_PROJECT_PROCESS_PASS", "assertions": count,
        "binary_hashes": binary_hashes, "native_input_hashes": native_hashes,
        "native_unity_editor_invoked": False,
        "fresh_saved_read_verified": True,
        "stale_snapshot_contrast_verified": True,
        "nonregular_input_rejected": True,
        "read_only_project_verified": True,
        "fifo_controls": fifo_count
    }, indent=2) + "\n")
    print("HPR_FRESH_PROJECT_PROCESS_PASS assertions=" + str(count), flush=True)


if __name__ == "__main__":
    run(*[Path(x).resolve() for x in sys.argv[1:]])
