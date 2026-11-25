"""Actual process-level checks on saved files produced by prior native Unity QA.

Reads original native fixtures without modification. All malformed or changed
controls are independent disposable copies. This is not a new Unity run.
"""
from pathlib import Path
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile


def run(dll, native, native_csv, empty2022, out):
    out.mkdir()
    count=0
    def check(ok,label):
        nonlocal count
        if not ok:raise AssertionError(label)
        count+=1
        print("PASS",label,flush=True)
    def dig(p):return hashlib.sha256(p.read_bytes()).hexdigest()
    originals=[native/"ProjectSettings/ProjectVersion.txt",native/"ProjectSettings/EditorBuildSettings.asset"]
    originals+=sorted(x for x in (native/"Assets/HPRPrivateMatrixQA").rglob("*") if x.is_file())
    originals+=[empty2022/"ProjectSettings/ProjectVersion.txt",empty2022/"ProjectSettings/EditorBuildSettings.asset",native_csv]
    hashes={str(p):dig(p) for p in originals}
    binaries=[Path(dll),Path(dll).with_suffix(".deps.json"),Path(dll).with_suffix(".runtimeconfig.json")]
    binary_hashes={p.name:dig(p) for p in binaries}
    def invoke(*args):
        result=subprocess.run(["dotnet",str(dll),*map(str,args)],capture_output=True,text=True,timeout=15)
        check(not result.stderr,"command emits no unexpected stderr")
        return result.returncode,json.loads(result.stdout)
    def capture(project, selector, output, code=0):
        result,data=invoke("capture",project,selector,output)
        check(result==code, f"capture {selector}: exit {code}")
        if code==0:
            check(output.is_file() and data["status"]=="SAVED_PROJECT_SNAPSHOT_CREATED",
                  "create-only saved snapshot")
        else:
            check(data["status"]=="INVALID_INPUT_OR_READ_ERROR","invalid saved file explicitly rejected")
        return data
    def compare(a,b,code):
        result,data=invoke("compare",a,b)
        check(result==code,f"compare {a.name} -> {b.name}: exit {code}")
        return data

    global_=out/"actual-global.hpr-scenes"
    global2=out/"actual-global-second.hpr-scenes"
    inherited=out/"actual-inherited.hpr-scenes"
    override=out/"actual-override.hpr-scenes"
    empty=out/"actual-unity2022-empty.hpr-scenes"
    inherited_selector="Assets/HPRPrivateMatrixQA/Inherited.asset"
    override_selector="Assets/HPRPrivateMatrixQA/Override.asset"
    g=capture(native,"global",global_)
    check(g["unity_version"]=="6000.6.8f1" and g["declared_entries"]==3 and g["enabled_entries"]==2
          and g["missing_or_stale_entries"]==0,"actual saved native global list")
    i=capture(native,inherited_selector,inherited)
    check(i["source"]=="Inherits global scenes" and i["enabled_entries"]==2 and i["declared_entries"]==3,
          "actual inherited profile reads shared list rather than its unused custom list")
    o=capture(native,override_selector,override)
    check(o["source"]=="Overrides global scenes" and o["enabled_entries"]==3 and o["declared_entries"]==3,
          "actual override profile reads its own list")
    capture(native,"global",global2)
    check(compare(global_,global2,0)["changed_scene_identities"]==0,"same actual saved global capture")
    gi=compare(global_,inherited,1)
    check(gi["changed_scene_identities"]==0 and not gi["declared_entry_sequence_changed"] and gi["list_source_changed"],
          "global and inherited effective rows agree; different profile identity still requests review")
    go=compare(global_,override,1)
    with native_csv.open(encoding="utf-8-sig",newline="") as f:
        expected={r["Scene"]:(r["Reference state"],r["Compared state"]) for r in csv.DictReader(f)
                  if r["Scene"].startswith("Assets/")}
    actual={r["current_path"]:(r["reference_state"],r["current_state"]) for r in go["findings"] if r["changed"]}
    check(expected==actual and len(actual)==3 and go["scene_identities_with_warnings"]==2,
          "offline saved global vs override matches prior genuine native Unity comparison CSV")
    (out/"actual-native-list-comparison.json").write_text(json.dumps(go,indent=2)+"\n")
    (out/"native-capture-receipts.json").write_text(json.dumps({"global":g,"inherited":i,"override":o},indent=2)+"\n")
    e=capture(empty2022,"global",empty)
    check(e["unity_version"]=="2022.3.22f1" and e["declared_entries"]==0,
          "actual Unity 2022 empty saved list")
    check(compare(empty,empty,1)["current_has_no_enabled_scenes"],"empty actual configuration not certified")
    before=dig(global_)
    capture(native,"global",global_,2)
    check(dig(global_)==before,"existing output preserved")

    with tempfile.TemporaryDirectory(prefix="private-copy-",dir=out) as tmp:
        tmp=Path(tmp)
        def clone(name):
            p=tmp/name
            (p/"ProjectSettings").mkdir(parents=True)
            (p/"Assets").mkdir()
            for f in ("ProjectVersion.txt","EditorBuildSettings.asset"):
                shutil.copy2(native/"ProjectSettings"/f,p/"ProjectSettings"/f)
            shutil.copytree(native/"Assets/HPRPrivateMatrixQA",p/"Assets/HPRPrivateMatrixQA")
            return p
        def reject(name,edit,selector="global"):
            p=clone(name)
            edit(p)
            dest=tmp/(name+".hpr-scenes")
            capture(p,selector,dest,2)
            check(not dest.exists(), "rejected capture did not create "+name)
        def settings(p):return p/"ProjectSettings/EditorBuildSettings.asset"
        def change(p,old,new):
            f=settings(p);s=f.read_text();assert old in s
            f.write_text(s.replace(old,new,1))
        reject("unknown-version",lambda p:(p/"ProjectSettings/ProjectVersion.txt").write_text("m_EditorVersion: 6000.99.0f1\n"))
        reject("duplicate-list",lambda p:change(p,"  m_configObjects: {}","  m_Scenes: []\n  m_configObjects: {}"))
        reject("noncanonical-duplicate-list",lambda p:change(p,"  m_configObjects: {}","  m_Scenes : []\n  m_configObjects: {}"))
        reject("multiple-documents",lambda p:change(p,"  m_configObjects: {}","  m_configObjects: {}\n--- !u!1045 &2\nEditorBuildSettings:"))
        reject("blank-list-interruption",lambda p:change(p,"  - enabled: 0","\n  - enabled: 0"))
        reject("unexpected-entry-field",lambda p:change(p,"  - enabled: 0","    unknown: true\n  - enabled: 0"))
        reject("quoted-path",lambda p:change(p,"    path: Assets/HPRPrivateMatrixQA/A/Start.unity",'    path: "Assets/HPRPrivateMatrixQA/A/Start.unity"'))
        reject("escaping-path",lambda p:change(p,"Assets/HPRPrivateMatrixQA/A/Start.unity","Assets/../ProjectSettings/Bad.unity"))
        reject("package-path",lambda p:change(p,"Assets/HPRPrivateMatrixQA/A/Start.unity","Packages/Example/Start.unity"))
        reject("bad-enabled",lambda p:change(p,"  - enabled: 1","  - enabled: 3"))
        reject("empty-with-entries",lambda p:change(p,"  m_Scenes:","  m_Scenes: []"))
        def bad_profile(p):
            f=p/override_selector
            f.write_text(f.read_text().replace("m_OverrideGlobalSceneList: 1","m_OverrideGlobalSceneList: 9"))
        reject("bad-override-flag",bad_profile,override_selector)
        reject("not-build-profile",lambda p:None,"Assets/HPRPrivateMatrixQA/Level.unity")
        def linked_asset(p):
            f=p/"Assets/HPRPrivateMatrixQA/A/Start.unity"
            f.unlink()
            f.symlink_to(native/"Assets/HPRPrivateMatrixQA/A/Start.unity")
        reject("linked-scene",linked_asset)
        def linked_settings(p):
            f=settings(p);f.unlink();f.symlink_to(native/"ProjectSettings/EditorBuildSettings.asset")
        reject("linked-settings",linked_settings)
        reject("oversize-meta",lambda p:(p/"Assets/HPRPrivateMatrixQA/A/Start.unity.meta").write_bytes(b"a"*65537))
        reject("malformed-meta",lambda p:(p/"Assets/HPRPrivateMatrixQA/A/Start.unity.meta").write_text("fileFormatVersion: 2\nguid: invalid\n"))
        p=clone("missing")
        (p/"Assets/HPRPrivateMatrixQA/A/Start.unity").unlink()
        dest=tmp/"missing.hpr-scenes"
        stale=capture(p,"global",dest)
        check(stale["missing_or_stale_entries"]==1,"missing actual listed scene flagged")
        check(compare(global_,dest,1)["findings"][0]["warning"],"missing actual scene requests review")
        p=clone("metadata-lost")
        (p/"Assets/HPRPrivateMatrixQA/A/Start.unity.meta").unlink()
        dest=tmp/"metadata-lost.hpr-scenes"
        check(capture(p,"global",dest)["missing_or_stale_entries"]==1,"missing actual adjacent meta flagged")
        p=clone("different-meta")
        meta=p/"Assets/HPRPrivateMatrixQA/A/Start.unity.meta"
        meta.write_text(meta.read_text().replace("026a849cf395f2edd862ee50d5714d2b","a"*32))
        dest=tmp/"different-meta.hpr-scenes"
        check(capture(p,"global",dest)["missing_or_stale_entries"]==1,"changed GUID at same scene path flagged")
        p=clone("unicode-path")
        a=p/"Assets/HPRPrivateMatrixQA/A/Start.unity"
        new=a.with_name("New scene 日本語.unity")
        a.rename(new)
        Path(str(a)+".meta").rename(Path(str(new)+".meta"))
        change(p,"Assets/HPRPrivateMatrixQA/A/Start.unity","Assets/HPRPrivateMatrixQA/A/"+new.name)
        dest=tmp/"unicode-path.hpr-scenes"
        check(capture(p,"global",dest)["missing_or_stale_entries"]==0,"plain Unicode path and spaces preserved")
        check(compare(global_,dest,1)["findings"][0]["current_path"].endswith(new.name),"same identity rename in actual saved copy")
        p=clone("inside-output")
        dest=p/"Assets/forbidden.hpr-scenes"
        capture(p,"global",dest,2)
        check(not dest.exists(),"refused output inside project")
    check(hashes=={p:dig(Path(p)) for p in hashes},"all original native fixture and receipt bytes unchanged")
    (out/"native-source-read-only-hashes.json").write_text(json.dumps(hashes,indent=2)+"\n")
    check(binary_hashes=={p.name:dig(p) for p in binaries},"same tested executable and runtime metadata")
    (out/"saved-project-process-receipt.json").write_text(json.dumps({
        "status":"HPR_SAVED_PROJECT_PROCESS_PASS","assertions":count,
        "binary_hashes":binary_hashes,"native_input_hashes":hashes,
        "native_unity_editor_invoked":False,"previous_native_csv_matched":True
    },indent=2)+"\n")
    print("HPR_SAVED_PROJECT_PROCESS_PASS assertions="+str(count))


if __name__=="__main__":
    run(*[Path(x).resolve() for x in sys.argv[1:]])
