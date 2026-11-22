"""Original separate native Unity imported prefab state parity product contracts."""
from pathlib import Path
import hashlib
import importlib.util
import json
import subprocess
import sys
import tarfile
import pytest

ROOT=Path(__file__).resolve().parents[1]/'unity/tools/release/imported_prefab_state_parity'
BUYER=ROOT/'Assets/HPRImportedPrefabParity'
SOURCE=BUYER/'Editor/HprImportedPrefabStateParity.cs'
COMPARE=ROOT/'qa/compare_native_receipts.py'


def comparator():
    spec=importlib.util.spec_from_file_location('hpr_prefab_parity_comparison',COMPARE)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m


def original(version, change=None, source_change=False):
    values=[{'key':'Prefab/Assets%2FA.prefab/@name','value':'A'},
            {'key':'Prefab/Assets%2FA.prefab/Transform/position','value':'0,0,0'},
            {'key':'Prefab/Assets%2FA.prefab/Component/UnityEngine.MeshRenderer[0]/enabled','value':'true'}]
    if change:values[1]['value']=change
    return {'schema':1,'unityVersion':version,'status':'CAPTURED_COVERED_PREFAB_VALUES',
            'incomplete':False,'failureReason':'','valuesCaptured':3,'unsupportedComponents':1,
            'inputs':[{'path':'Assets/A.prefab','sourceSha256':('b' if source_change else 'a')*64,
                       'metaSha256':'c'*64}], 'values':values,
            'limitation':'only a subset of actual imported fields'}


def write(root,name,data):
    p=root/name;p.write_text(json.dumps(data));return p


def test_original_buyer_path_and_guid_metadata():
    import re
    seen=set()
    for asset in [BUYER,*BUYER.rglob('*')]:
        if asset.suffix=='.meta' or not (asset.is_file() or asset.is_dir()):continue
        meta=Path(str(asset)+'.meta')
        assert meta.is_file()
        match=re.search(r'(?m)^guid: ([a-f0-9]{32})$',meta.read_text())
        assert match and match.group(1) not in seen
        seen.add(match.group(1))
    assert len(seen)==5
    assert SOURCE.exists() and (BUYER/'README.md').is_file()
    assert (BUYER/'LICENSE.md').is_file()
    docs=(BUYER/'README.md').read_text()
    for heading in ('Documentation: prepare a real two-version prefab comparison',
                    'Troubleshooting and release acceptance',
                    'SOURCE_BYTES_DIFFER_NO_EDITOR_INFERENCE',
                    'MATCHED_COVERED_IMPORTED_PREFAB_VALUES',
                    'never edit a JSON result'):
        assert heading in docs
    assert not list(BUYER.rglob('*.dll'))


def test_public_unity_editor_api_and_read_only_structure():
    s=SOURCE.read_text()
    for needle in ('Tools/HPR/Imported Prefab State Parity',
                   'PrefabUtility.LoadPrefabContents','PrefabUtility.UnloadPrefabContents',
                   'AssetDatabase.LoadAssetAtPath<GameObject>',
                   'AssetDatabase.TryGetGUIDAndLocalFileIdentifier',
                   'MaxPrefabs=24','MaxValues=25000',
                   'CAPTURED_COVERED_PREFAB_VALUES','REVIEW_IMPORTED_PREFAB_VALUE_DIFFERENCES',
                   'SOURCE_BYTES_DIFFER_NO_EDITOR_INFERENCE',
                   'FileMode.CreateNew','EditorUtility.DisplayCancelableProgressBar',
                   'MeshFilter)', 'TextMesh)', 'SkinnedMeshRenderer)',
                   'SpriteRenderer)', 'unsupportedComponents'):
        assert needle in s,needle
    assert "new[]{';','\\r','\\n'}" in s
    assert 'EditorGUILayout.TextArea(paths,multilinePaths,GUILayout.MinHeight(80f))' in s
    assert 'ReceiptLabel(first)' in s and 'ReceiptLabel(second)' in s
    assert 'Covered values match in both Editors' in s
    for forbidden in ('AssetDatabase.SaveAssets(', 'AssetDatabase.ImportAsset(',
                      'PrefabUtility.SaveAsPrefabAsset(', 'Undo.RecordObject(',
                      'AssetDatabase.DeleteAsset(', 'File.Delete(', 'UnityWebRequest',
                      'EditorPrefs.Set', 'FileMode.Create,'):
        assert forbidden not in s


def test_real_unity_native_export_and_buyer_harness_scope():
    t=(ROOT/'qa/run_native.sh').read_text()
    for needle in ('-createProject "$author"','-createProject "$buyer"',
                   'HprPrefabParityExporter.Run','HprPrefabParityNativeQa.Run',
                   'HPR_PREFAB_STATE_PARITY_NATIVE_PASS',
                   'verify_original_archive.py','HPR_Imported_Prefab_State_Parity_original.unitypackage'):
        assert needle in t
    qa=(ROOT/'qa/HprPrefabParityNativeQa.cs').read_text()
    for needle in ('native_three_original_first_party_prefabs_loaded',
                   'native_cancel_is_incomplete_not_clean',
                   'same_source_original_value_modified_in_memory_detected',
                   'different_original_source_cannot_implicate_Unity_engine',
                   'create_only_refuses_original_overwrite'):
        assert needle in qa


def test_native_real_sample_field_coverage_and_same_scanner_source_guard():
    qa=(ROOT/'qa/HprPrefabParityNativeQa.cs').read_text()
    for required in ('result.unsupportedComponents==0',
                     'result.values.Any(v=>v.key.EndsWith("/sharedMesh"))',
                     'result.values.Any(v=>v.key.EndsWith("/text"))'):
        assert required in qa
    verifier=(ROOT/'qa/run_native_two_editor_compare.sh').read_text()
    assert "A['source_sha256']==B['source_sha256']" in verifier
    assert 'Scanner source revisions differ' in verifier
    src=SOURCE.read_text()
    for branch in ('part is MeshFilter','part is TextMesh','part is SkinnedMeshRenderer',
                   'part is SpriteRenderer','part is Renderer','part is Animator'):
        assert branch in src


def test_identical_loaded_values_are_narrowly_matched(tmp_path):
    m=comparator()
    p=write(tmp_path,'2022.json',original('2022.3.22f1'))
    q=write(tmp_path,'6000.json',original('6000.6.8f1'))
    r=m.compare(p,q)
    assert r['status']=='MATCHED_COVERED_IMPORTED_PREFAB_VALUES'
    assert r['unsupported_component_types']==2
    assert not r['changed_keys'] and not r['source_differences']


def test_semantic_changed_field_detected_with_identical_source(tmp_path):
    m=comparator()
    p=write(tmp_path,'2022.json',original('2022.3.22f1'))
    q=write(tmp_path,'6000.json',original('6000.6.8f1',change='0,1,0'))
    r=m.compare(p,q)
    assert r['status']=='REVIEW_IMPORTED_PREFAB_VALUE_DIFFERENCES'
    assert r['changed_keys']==['Prefab/Assets%2FA.prefab/Transform/position']
    assert not r['source_differences']


def test_source_changed_not_misrepresented_as_engine_regression(tmp_path):
    m=comparator()
    p=write(tmp_path,'2022.json',original('2022.3.22f1'))
    q=write(tmp_path,'6000.json',original('6000.6.8f1',change='0,1,0',source_change=True))
    r=m.compare(p,q)
    assert r['status']=='SOURCE_BYTES_DIFFER_NO_EDITOR_INFERENCE'
    assert r['source_differences']==['Assets/A.prefab']


@pytest.mark.parametrize('corrupt', [
    {'schema':2}, {'incomplete':True}, {'status':'INCOMPLETE'},
    {'inputs':[]}, {'valuesCaptured':0}, {'failureReason':'partial'},
    {'inputs':[{'path':'Assets/../evil.prefab','sourceSha256':'a'*64,'metaSha256':'c'*64}]},
    {'inputs':[{'path':'Assets/A.prefab','sourceSha256':'a'*63,'metaSha256':'c'*64}]},
    {'values':[{'key':'x','value':'a'},{'key':'x','value':'b'}]},
    {'values':[{'key':'Prefab/Assets%2FOther.prefab/@name','value':'foreign'}], 'valuesCaptured':1},
])
def test_corrupted_or_incomplete_native_receipts_fail_closed(tmp_path,corrupt):
    m=comparator()
    p=write(tmp_path,'invalid.json',original('2022.3.22f1')|corrupt)
    with pytest.raises(ValueError):m.load(p)


def test_create_only_comparison_and_original_receipts_preserved(tmp_path):
    p=write(tmp_path,'2022.json',original('2022.3.22f1'))
    q=write(tmp_path,'6000.json',original('6000.6.8f1'))
    out=tmp_path/'comparison.json'
    cmd=[sys.executable,str(COMPARE),str(p),str(q),'--output',str(out)]
    a=subprocess.run(cmd,capture_output=True,text=True)
    assert a.returncode==0,a.stderr
    original_output=out.read_bytes()
    b=subprocess.run(cmd,capture_output=True,text=True)
    assert b.returncode!=0 and out.read_bytes()==original_output
    assert json.loads(p.read_text())['unityVersion']=='2022.3.22f1'
    assert json.loads(q.read_text())['unityVersion']=='6000.6.8f1'


def test_meta_only_change_is_original_input_difference_not_unity_bug(tmp_path):
    m=comparator();a=original('2022.3.22f1');b=original('6000.6.8f1')
    b['inputs'][0]['metaSha256']='d'*64
    p=write(tmp_path,'2022.json',a);q=write(tmp_path,'6000.json',b)
    outcome=m.compare(p,q)
    assert outcome['status']=='SOURCE_BYTES_DIFFER_NO_EDITOR_INFERENCE'
    assert outcome['source_differences']==['Assets/A.prefab']


def test_imported_fields_added_or_removed_are_explicit(tmp_path):
    m=comparator();a=original('2022.3.22f1');b=original('6000.6.8f1')
    b['values'].pop(0);b['values'].append({'key':'Prefab/Assets%2FA.prefab/@layer','value':'2'})
    p=write(tmp_path,'2022.json',a);q=write(tmp_path,'6000.json',b)
    outcome=m.compare(p,q)
    assert outcome['status']=='REVIEW_IMPORTED_PREFAB_VALUE_DIFFERENCES'
    assert outcome['removed_keys']==['Prefab/Assets%2FA.prefab/@name']
    assert outcome['added_keys']==['Prefab/Assets%2FA.prefab/@layer']
    assert not outcome['changed_keys']


def test_independent_real_source_hash_verifier_and_tamper_detection(tmp_path):
    import hashlib
    script=ROOT/'qa/verify_native_prefab_receipt.py'
    spec=importlib.util.spec_from_file_location('hpr_prefab_native_verifier',script)
    v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    project=tmp_path/'project';source=project/'Assets/A.prefab';source.parent.mkdir(parents=True)
    source.write_bytes(b'original test prefab bytes from private fixture')
    meta=Path(str(source)+'.meta');meta.write_bytes(b'original private importer metadata')
    r=original('2022.3.22f1')
    r['inputs'][0]['sourceSha256']=hashlib.sha256(source.read_bytes()).hexdigest()
    r['inputs'][0]['metaSha256']=hashlib.sha256(meta.read_bytes()).hexdigest()
    receipt=write(tmp_path,'receipt.json',r)
    assert v.verify(project,receipt)['original_prefab_and_meta_files']==2
    source.write_bytes(source.read_bytes()+b'\nchanged without changing GUID')
    with pytest.raises(ValueError,match='bytes differ'):
        v.verify(project,receipt)
    source.write_bytes(b'original test prefab bytes from private fixture')
    meta.write_bytes(b'changed importer metadata without changing GUID')
    with pytest.raises(ValueError,match='bytes differ'):
        v.verify(project,receipt)


def test_native_domain_reload_disabled_enter_exit_and_original_state_unchanged():
    qa=(ROOT/'qa/HprPrefabParityPlaymodeQa.cs').read_text()
    runner=(ROOT/'qa/run_native_fast_playmode.sh').read_text()
    for expected in ('EnterPlayModeOptions.DisableDomainReload',
                     'PlayModeStateChange.EnteredPlayMode',
                     'PlayModeStateChange.EnteredEditMode',
                     'original_loaded_prefab_state_identical_before_after_playmode',
                     'HPR_PREFAB_PLAYMODE_NATIVE_PASS',
                     'EditorSettings.enterPlayModeOptions=savedOptions'):
        assert expected in qa
    assert '-batchmode -nographics' in runner
    assert 'HPR_PREFAB_PLAYMODE_NATIVE_PASS' in runner
    assert 'FileMode.CreateNew' in qa


def test_original_graphical_preview_is_not_fabricated_or_shipped_to_buyer():
    qa=(ROOT/'qa/HprPrefabParityGraphicalQa.cs').read_text()
    runner=(ROOT/'qa/run_graphical_evidence.sh').read_text()
    for expected in ('!Application.isBatchMode','HprPrefabStateScan.Scan(paths)',
                     'HprPrefabStateCompare.Compare(',
                     'HprPrefabStateParityWindow.Open()',
                     'HPR_PREFAB_PARITY_GRAPHICAL_NATIVE_PASS',
                     'actual_real_window_not_a_mockup=TRUE',
                     'software_terms_accepted=FALSE','human_clicked_controls=FALSE'):
        assert expected in qa
    for expected in ('Xvfb :147','-executeMethod HprPrefabParityGraphicalQa.Run',
                     'actual-product-unity-editor-window.png','actual-editor-window-receipt.txt'):
        assert expected in runner
    assert not list(BUYER.rglob('HprPrefabParityGraphicalQa.cs'))
    for forbidden in ('AssetDatabase.SaveAssets(', 'AssetDatabase.DeleteAsset(',
                      'PrefabUtility.SaveAsPrefabAsset(', 'UnityWebRequest', 'File.Delete('):
        assert forbidden not in qa
