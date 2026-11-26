"""Create an exact, private, framework-dependent companion ZIP after acceptance.

No Unity invocation, third-party SDK/runtime redistribution, or publication.
The inputs must be the final tested output of run_offline_acceptance.sh.
"""
from pathlib import Path
import hashlib
import json
import sys
import zipfile


def package(acceptance, saved_acceptance, fresh_acceptance, readme, license_path, revision, output):
    acceptance,saved_acceptance,fresh_acceptance,readme,license_path,output=map(
        Path,(acceptance,saved_acceptance,fresh_acceptance,readme,license_path,output))
    def require(value, message):
        if not value:raise ValueError(message)
    if output.exists():
        raise FileExistsError("Refusing to replace a prior package")
    process=json.loads((acceptance/"companion-process-receipt.json").read_text())
    saved=json.loads((saved_acceptance/"saved-project-process-receipt.json").read_text())
    require(process["status"]=="HPR_SCENE_GATE_PROCESS_PASS" and process["assertions"]>=100,
            "Missing companion process acceptance")
    require(saved["status"]=="HPR_SAVED_PROJECT_PROCESS_PASS" and saved["assertions"]>=100
            and saved["previous_native_csv_matched"] and not saved["native_unity_editor_invoked"],
            "Missing independently checked saved-project acceptance")
    fresh=json.loads((fresh_acceptance/"fresh-project-process-receipt.json").read_text())
    require(fresh["status"]=="HPR_FRESH_PROJECT_PROCESS_PASS" and
            not fresh["native_unity_editor_invoked"] and all(fresh.get(k) is True for k in
                ("fresh_saved_read_verified","stale_snapshot_contrast_verified",
                 "nonregular_input_rejected","read_only_project_verified")),
            "Missing fresh-project command and special-file acceptance")
    require(len(revision)==40 and all(c in "0123456789abcdef" for c in revision),"Invalid source revision")
    build=acceptance/"build/bin/Release/net10.0"
    contents={
        "HprSceneGate.dll":build/"HprSceneGate.dll",
        "HprSceneGate.deps.json":build/"HprSceneGate.deps.json",
        "HprSceneGate.runtimeconfig.json":build/"HprSceneGate.runtimeconfig.json",
        "README.md":readme,
        "LICENSE.md":license_path,
        **{f"examples/{name}.hpr-scenes":acceptance/"fixtures"/f"{name}.hpr-scenes"
           for name in ("approved","same","renamed")}
    }
    blobs={name:path.read_bytes() for name,path in contents.items()}
    digest=lambda data:hashlib.sha256(data).hexdigest()
    binary_names=[n for n in blobs if n.startswith("HprSceneGate.")]
    require({n:digest(blobs[n]) for n in binary_names}==process["binary_hashes"]==saved["binary_hashes"]==fresh["binary_hashes"],
            "Packaged executable differs from actually tested output")
    require(all(digest(data)==process["fixture_hashes"][Path(name).name] for name,data in blobs.items()
                if name.startswith("examples/")),"Example snapshot differs from tested fixture")
    runtime=json.loads(blobs["HprSceneGate.runtimeconfig.json"])["runtimeOptions"]
    require(runtime["tfm"]=="net10.0" and runtime["framework"]["name"]=="Microsoft.NETCore.App"
            and runtime["framework"]["version"]=="10.0.15" and runtime["rollForward"]=="LatestPatch",
            "Unsupported runtime configuration")
    deps=json.loads(blobs["HprSceneGate.deps.json"])
    require(set(deps["libraries"])=={"HprSceneGate/0.2.0"},"Unexpected bundled dependency")
    require(b"Internal prerelease candidate" in blobs["LICENSE.md"],"Missing private license boundary")
    manifest={
        "status":"PRIVATE_COMPANION_CANDIDATE_NOT_PUBLISHED",
        "source_revision":revision,
        "version":"0.2.0",
        "runtime":"External .NET 10.0.15 or later 10.0 security patch",
        "runtime_included":False,
        "native_unity_editor_invoked":False,
        "platform_verified":"Linux x86-64",
        "example_data":"Synthetic snapshots, not real Unity scans",
        "companion_process_assertions":process["assertions"],
        "saved_project_process_assertions":saved["assertions"],
        "fresh_project_process_assertions":fresh["assertions"],
        "fresh_saved_read_check_verified":True,
        "special_file_inputs_rejected":True,
        "files":{name:{"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()}
                 for name,data in sorted(blobs.items())},
    }
    blobs["PRIVATE_MANIFEST.json"]=(json.dumps(manifest,indent=2)+"\n").encode()
    with zipfile.ZipFile(output,"x",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,data in sorted(blobs.items()):
            item=zipfile.ZipInfo(name,date_time=(2026,11,26,0,0,0))
            item.compress_type=zipfile.ZIP_DEFLATED
            item.external_attr=0o100644<<16
            z.writestr(item,data)
    with zipfile.ZipFile(output) as z:
        require(z.testzip() is None and set(z.namelist())==set(blobs) and
                len(z.namelist())==len(blobs),"ZIP integrity failure")
        for name,data in blobs.items():require(z.read(name)==data,"ZIP payload mismatch: "+name)
    print(json.dumps({"status":manifest["status"],"source_revision":revision,
        "sha256":hashlib.sha256(output.read_bytes()).hexdigest(),
        "bytes":output.stat().st_size,"entries":len(blobs)},indent=2))


if __name__=="__main__":
    package(*sys.argv[1:])
