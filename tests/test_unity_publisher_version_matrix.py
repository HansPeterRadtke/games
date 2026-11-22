"""New first-party Unity publisher version matrix source, comparator and fail-closed QA."""
from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import pytest

BASE=Path(__file__).resolve().parents[1]/'unity/tools/release/publisher_version_matrix'
C=BASE/'Assets/HPRPublisherVersionMatrix/Editor/HprPublisherVersionMatrix.cs'
TOOL=BASE/'qa/compare_version_receipts.py'


def module():
    spec=importlib.util.spec_from_file_location('hpr_matrix_comparator',TOOL)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def sample(version,*,paths=('Assets/HPRPackage/File.cs','Assets/HPRPackage/Prefab.prefab'),guid_override=False,dep_override=False):
    rows=[]
    for idx,path in enumerate(paths):
        guid=('f' if guid_override and idx==0 else str(idx+1))*32
        rows.append({'path':path,'guid':guid,'directDependencies':
            ['Assets/HPRPackage/File.cs'] if dep_override and idx==1 else []})
    return {'schema':1,'unityVersion':version,'rootFolders':'Assets/HPRPackage',
            'status':'SNAPSHOT_COMPLETE','incomplete':False,'assetCount':len(rows),'assets':rows,
            'limitation':'This result does not prove runtime compatibility.'}


def write(tmp,name,report):
    p=tmp/name;p.write_text(json.dumps(report));return p


def test_original_buyer_root_is_metadata_complete():
    p=BASE/'Assets/HPRPublisherVersionMatrix';seen=set();count=0
    for asset in [p,*p.rglob('*')]:
        if asset.is_file() and asset.suffix=='.meta':continue
        if not (asset.is_dir() or asset.is_file()):continue
        meta=Path(str(asset)+'.meta');assert meta.is_file(),meta
        import re
        match=re.search(r'(?m)^guid: ([a-f0-9]{32})$',meta.read_text())
        assert match and match.group(1) not in seen
        seen.add(match.group(1));count+=1
    assert count==6
    assert C.is_file() and (p/'README.md').is_file() and (p/'LICENSE.md').is_file()
    assert (p/'Editor/HprPublisherVersionMatrixCompare.cs').is_file()
    assert not list(p.rglob('*.dll'))
    docs=(p/'README.md').read_text()
    for statement in ('Documentation and purpose','Scan imported publisher assets',
                      'Compare imported paths, GUIDs and direct dependencies',
                      'MATCHED_IMPORT_METADATA','private commercial candidate'):
        assert statement in docs


def test_first_party_readonly_editor_scanner_public_api_and_strict_write():
    t=C.read_text()
    for required in ('Tools/HPR/Publisher Version Matrix','AssetDatabase.FindAssets',
                     'AssetDatabase.GUIDToAssetPath','AssetDatabase.AssetPathToGUID',
                     'AssetDatabase.GetDependencies','SNAPSHOT_COMPLETE','INCOMPLETE',
                     'FileMode.CreateNew','ValidateRoots','MaxAssets = 4000',
                     'AssetDatabase.IsValidFolder','rootFolders','directDependencies',
                     'this does not validate'.capitalize() if False else 'does not validate'):
        assert required in t, required
    for forbidden in ('SaveAndReimport(', 'AssetDatabase.ImportPackage(',
                      'AssetDatabase.SaveAssets(', 'AssetDatabase.DeleteAsset(',
                      'EditorSettings.', 'UnityWebRequest', 'File.Delete(',
                      'Process.Start(', 'FileMode.Create,'):
        assert forbidden not in t
    compare=(BASE/'Assets/HPRPublisherVersionMatrix/Editor/HprPublisherVersionMatrixCompare.cs').read_text()
    for required in ('HprVersionReceiptCompare', 'ReadReceipt', 'Validate(',
                     'REVIEW_IMPORT_DIFFERENCES','MATCHED_IMPORT_METADATA',
                     'Tools/HPR/Compare Publisher Version Receipts','FileMode.CreateNew'):
        assert required in compare
    for forbidden in ('SaveAndReimport(', 'AssetDatabase.ImportPackage(', 'File.Delete(', 'FileMode.Create,'):
        assert forbidden not in compare
    qa=(BASE/'qa/HprPublisherVersionMatrixQa.cs').read_text()
    assert 'HPR_PUBLISHER_VERSION_MATRIX_NATIVE_PASS' in qa
    assert 'create_only_output_refuses_overwrite' in qa
    assert 'HPR_MATRIX_QA_FAIL' in qa
    assert 'HPR_PUBLISHER_VERSION_COMPARE_NATIVE_PASS' in (BASE/'qa/HprPublisherVersionCompareNativeQa.cs').read_text()


def test_exact_comparison_no_diff(tmp_path):
    m=module();p=write(tmp_path,'u2022.json',sample('2022.3.22f1'))
    q=write(tmp_path,'u6.json',sample('6000.6.8f1'))
    d=m.compare(p,q)
    assert d['status']=='MATCHED_IMPORT_METADATA'
    assert d['asset_counts']==[2,2]
    assert all(not d[k] for k in ('missing_from_second','new_in_second','guid_changes','direct_dependency_changes'))


def test_changed_identity_and_dependency_are_review_only(tmp_path):
    m=module();p=write(tmp_path,'old.json',sample('2022.3.22f1'))
    q=write(tmp_path,'new.json',sample('6000.6.8f1',guid_override=True,dep_override=True))
    d=m.compare(p,q)
    assert d['status']=='REVIEW_DIFFERENCES'
    assert d['guid_changes']==['Assets/HPRPackage/File.cs']
    assert d['direct_dependency_changes']==['Assets/HPRPackage/Prefab.prefab']
    assert not d['missing_from_second']


def test_refuse_missing_asset_and_different_scope(tmp_path):
    m=module();p=write(tmp_path,'old.json',sample('2022.3.22f1'))
    q=write(tmp_path,'new.json',sample('6000.6.8f1',paths=('Assets/HPRPackage/File.cs',)))
    d=m.compare(p,q)
    assert d['status']=='REVIEW_DIFFERENCES'
    assert d['missing_from_second']==['Assets/HPRPackage/Prefab.prefab']
    corrupted=sample('6000.6.8f1');corrupted['rootFolders']='Assets/Other'
    q.write_text(json.dumps(corrupted))
    with pytest.raises(ValueError,match='(Different package roots|Asset outside publisher roots)'):
        m.compare(p,q)


@pytest.mark.parametrize('invalid', [
    {'incomplete':True},
    {'assetCount':0},
    {'status':'INCOMPLETE'},
    {'schema':2},
    {'assets':[{'path':'Assets/HPRPackage/../Private/file.cs','guid':'a'*32,'directDependencies':[]}]},
    {'assets':[{'path':'Assets/Other/File.cs','guid':'a'*32,'directDependencies':[]}]},
])
def test_invalid_reports_fail_closed(tmp_path,invalid):
    d=sample('2022.3.22f1');d.update(invalid)
    p=write(tmp_path,'invalid.json',d)
    with pytest.raises(ValueError):module().load_receipt(p)


def test_output_create_only_preserves_existing_source_and_result(tmp_path):
    a=write(tmp_path,'old.json',sample('2022.3.22f1'))
    b=write(tmp_path,'new.json',sample('6000.6.8f1'))
    out=tmp_path/'compare.json'
    args=[sys.executable,str(TOOL),str(a),str(b),'--output',str(out)]
    first=subprocess.run(args,capture_output=True,text=True)
    assert first.returncode==0,first.stderr
    blob=out.read_bytes();assert json.loads(blob)['status']=='MATCHED_IMPORT_METADATA'
    second=subprocess.run(args,capture_output=True,text=True)
    assert second.returncode!=0 and out.read_bytes()==blob
    assert json.loads(a.read_text())['unityVersion']=='2022.3.22f1'
    assert json.loads(b.read_text())['unityVersion']=='6000.6.8f1'


def test_official_unity_archive_rejects_foreign_asset_path_and_rewritten_bytes(tmp_path):
    """Native exporter format fixture, not a substitute for actual Unity export."""
    import tarfile,io,re
    base=BASE/'Assets/HPRPublisherVersionMatrix'
    spec=importlib.util.spec_from_file_location('hpr_original_archive',BASE/'qa/verify_original_archive.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    entries=[]
    for asset in [base,*base.rglob('*')]:
        if asset.suffix=='.meta' or not (asset.is_file() or asset.is_dir()):continue
        meta=Path(str(asset)+'.meta')
        guid=re.search(r'(?m)^guid: ([a-f0-9]{32})$',meta.read_text()).group(1)
        name='Assets/'+str(asset.relative_to(base.parent))
        entries.extend([(guid+'/pathname',name.encode()),(guid+'/asset.meta',meta.read_bytes())])
        if asset.is_file():entries.append((guid+'/asset',asset.read_bytes()))
    def build(out,*,foreign=False,tamper=False):
        with tarfile.open(out,'w:gz') as tar:
            for path,raw in entries:
                if tamper and path.endswith('/asset') and b'Publisher Version Matrix' in raw:
                    raw+=b'\nCHANGED'
                meta=tarfile.TarInfo(path);meta.size=len(raw);tar.addfile(meta,io.BytesIO(raw))
            if foreign:
                data=b'Assets/NotOurPublisher/Fake.cs'
                meta=tarfile.TarInfo('f'*32+'/pathname');meta.size=len(data);tar.addfile(meta,io.BytesIO(data))
    good=tmp_path/'good.unitypackage';build(good)
    assert m.verify(good)['status']=='PASS'
    wrong=tmp_path/'wrong.unitypackage';build(wrong,foreign=True)
    with pytest.raises(ValueError):m.verify(wrong)
    bad=tmp_path/'changed.unitypackage';build(bad,tamper=True)
    with pytest.raises(ValueError):m.verify(bad)


def test_native_runner_never_replays_existing_author_or_accepts_unknown_version():
    runner=(BASE/'qa/run_native_matrix.sh').read_text()
    for expected in ('! -e "$work"','verified_author','! -e "$work/independent-buyer-project"',
                     'HPR_PUBLISHER_VERSION_MATRIX_NATIVE_PASS',
                     'HPR_PUBLISHER_VERSION_COMPARE_NATIVE_PASS',
                     'verify_original_archive.py','independent-buyer-project','-importPackage "$package"'):
        assert expected in runner
    for forbidden in ('UnityWebRequest','AssetDatabase.DeleteAsset(', 'rm -rf', 'File.Delete(', 'adb shell'):
        assert forbidden not in runner


def test_real_cross_version_first_party_native_verifier_is_scoped_and_strict():
    qa=(BASE/'qa/HprPublisherVersionRealReceiptsQa.cs').read_text()
    for marker in ('HPR_MATRIX_REAL_TWO_EDITOR_COMPARE_PASS','2022.3.22f1','6000.6.8f1',
                   'original_buyer_assets_same_metadata_in_two_real_editors',
                   'HprVersionReceiptCompare.ReadReceipt', 'HprVersionReceiptCompare.Compare',
                   'refuse_replace_existing_report'):
        assert marker in qa
    for forbidden in ('SaveAndReimport(', 'AssetDatabase.ImportPackage(', 'AssetDatabase.SaveAssets(',
                      'UnityWebRequest', 'File.Delete('):
        assert forbidden not in qa


def test_native_fast_playmode_contract_is_real_callbacks_and_restores_setting():
    qa=(BASE/'qa/HprPublisherVersionPlaymodeQa.cs').read_text()
    run=(BASE/'qa/run_native_fast_playmode.sh').read_text()
    for marker in ('EnterPlayModeOptions.DisableDomainReload','PlayModeStateChange.EnteredPlayMode',
                   'PlayModeStateChange.EnteredEditMode','original_vendor_scan_identical_before_after_playmode',
                   'FileMode.CreateNew','EditorSettings.enterPlayModeOptions=savedOptions',
                   'HPR_PUBLISHER_MATRIX_PLAYMODE_NATIVE_PASS'):
        assert marker in qa
    assert '-batchmode -nographics' in run
    assert 'timeout 230' in run
    assert 'HPR_PUBLISHER_MATRIX_PLAYMODE_NATIVE_PASS' in run
