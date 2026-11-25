"""Actual command-line execution and immutable input checks, not Unity acceptance."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

def run(dll, fixture):
    fixture=Path(fixture)
    count=0
    def check(ok, label):
        nonlocal count
        if not ok:raise AssertionError(label)
        count+=1
        print("PASS", label)
    def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
    original={p.name:digest(p) for p in fixture.glob("*.hpr-scenes")}
    binaries=[Path(dll),Path(dll).with_suffix(".deps.json"),Path(dll).with_suffix(".runtimeconfig.json")]
    binary_hashes={p.name:digest(p) for p in binaries}
    def command(*args):
        return subprocess.run(["dotnet", str(dll), *map(str,args)], capture_output=True,
                              text=True,timeout=15)
    def compare(left,right,code):
        a=fixture/(left+".hpr-scenes")
        b=fixture/(right+".hpr-scenes")
        result=command("compare",a,b)
        check(result.returncode==code, f"{left} -> {right}: exit {code}")
        check(not result.stderr, f"{left} -> {right}: no unstructured stderr")
        data=json.loads(result.stdout)
        check(data["schema"]==1 and data["tool_version"]=="0.1.0", f"{left} -> {right}: JSON schema/version")
        if code!=2:
            check(not data["project_identity_verified"] and
                  not data["current_snapshot_freshness_verified"],"truthful verification boundary")
        return data
    help_=command("--help")
    check(help_.returncode==0 and "Exit 2" in help_.stdout,"help documents exits")
    ver=command("--version")
    check(ver.returncode==0 and ver.stdout.strip()=="0.1.0","version identifies candidate")
    bad=command("compare")
    check(bad.returncode==2 and "Usage:" in bad.stderr,"wrong argument count")
    good=compare("approved","same",0)
    check(good["status"]=="MATCH_WITHOUT_WARNINGS" and good["changed_scene_identities"]==0
          and not good["findings"],"matching list, later capture")
    renamed=compare("approved","renamed",1)
    check(renamed["changed_scene_identities"]==1 and
          renamed["findings"][0]["reference_path"]=="Assets/Scenes/Start.unity" and
          renamed["findings"][0]["current_path"]=="Assets/Scenes/StartRenamed.unity","same GUID rename")
    stale=compare("approved","missing",1)
    check(stale["findings"][0]["reference_state"]==stale["findings"][0]["current_state"]
          and stale["findings"][0]["warning"],"missing state without index change")
    ordered=compare("approved","reordered",1)
    check(ordered["declared_entry_sequence_changed"] and ordered["changed_scene_identities"]==2,
          "enabled order affects build indices")
    disabled=compare("approved","disabled-reordered",1)
    check(disabled["declared_entry_sequence_changed"] and disabled["changed_scene_identities"]==0,
          "disabled order change distinguished from enabled indices")
    first=disabled["first_differing_entry"]
    check(first["list_index"]==0 and first["current"]["enabled"] is False and
          first["reference"]["build_index"]==0,"disabled-order report shows precise first differing entry")
    empty=compare("approved","empty",1)
    check(empty["current_has_no_enabled_scenes"],"empty enabled list")
    check(compare("empty","empty",1)["reference_has_no_enabled_scenes"],"identically empty still fails")
    check(compare("approved","older",1)["current_capture_precedes_reference"],"reversed chronology")
    check(compare("approved","other-profile",1)["profile_identifier_changed"],"profile identity drift")
    check(compare("approved","override",1)["list_source_changed"],"inheritance drift")
    check(compare("approved","moved-profile",1)["profile_asset_path_changed"],"profile asset path drift")
    check(compare("approved","duplicate",1)["scene_identities_with_warnings"]>0,"repeated GUID warning")
    check(compare("approved","ambiguous",1)["scene_identities_with_warnings"]==2,"ambiguous scene names")
    check(compare("warning-baseline","warning-current",1)["changed_scene_identities"]==0,
          "identical stale warnings still require review")
    check(compare("approved","added",1)["findings"][0]["reference_state"]=="Absent","disabled addition")
    check(compare("approved","removed",1)["findings"][0]["current_state"]=="Absent","disabled removal")
    check(compare("approved","unicode",0)["current"]["title"].startswith("日本語"),"UTF-8 metadata")
    raw=command("compare",fixture/"approved.hpr-scenes",fixture/"unicode.hpr-scenes")
    check("\x1b" not in raw.stdout,"terminal escape safely JSON encoded")
    for name in ("truncated","oversized","bad-magic","does-not-exist"):
        check(compare("approved",name,2)["status"]=="INVALID_INPUT_OR_READ_ERROR","invalid input classified")
    check(original=={p.name:digest(p) for p in fixture.glob("*.hpr-scenes")},"all source snapshot bytes unchanged")
    check(binary_hashes=={p.name:digest(p) for p in binaries},"executed binary and runtime metadata unchanged")
    receipt={"status":"HPR_SCENE_GATE_PROCESS_PASS","assertions":count,
             "binary_hashes":binary_hashes,"fixture_hashes":original}
    with (fixture.parent/"companion-process-receipt.json").open("x") as out:
        json.dump(receipt,out,indent=2)
    print("HPR_SCENE_GATE_PROCESS_PASS assertions="+str(count))

if __name__=="__main__":
    run(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve())
