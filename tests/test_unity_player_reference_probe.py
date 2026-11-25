"""First-party player-only reference QA and boundaries; native smoke test is separate."""
import importlib.util
import json
from pathlib import Path

import pytest

BASE=Path(__file__).resolve().parents[1]/'unity/tools/release/player_reference_probe'
BUYER=BASE/'Assets/HPRPlayerReferenceProbe'
RUNTIME=(BUYER/'Runtime/HprPlayerReferenceProbe.cs').read_text()
EDITOR=(BUYER/'Editor/HprPlayerReferenceProbeWindow.cs').read_text()
QA=BASE/'qa'


def test_public_product_has_distinct_nonduplicative_editor_and_player_components():
    assert 'namespace HPR.PlayerReferenceProbe' in RUNTIME
    assert 'HprReferenceCase' in RUNTIME
    assert 'HprReferenceInspector.Inspect(checks,"PLAYER")' in RUNTIME
    assert 'HprReferenceInspector.Inspect(probe.checks,"EDITOR")' in EDITOR
    assert '[MenuItem("Tools/HPR/Player Reference Probe")]' in EDITOR
    assert 'Compare an actual Editor baseline against an actual Player report' in RUNTIME
    assert 'PLAYER_REFERENCE_LOSS_REPRODUCED' in RUNTIME


def test_read_only_opt_in_and_explicit_scope_no_invasive_auto_fix():
    assert '[DisallowMultipleComponent]' in RUNTIME
    assert 'if(Application.isEditor)return false;' in RUNTIME
    assert 'Application.persistentDataPath' in RUNTIME
    assert 'FileMode.CreateNew' in RUNTIME
    assert 'MaxCases=64' in RUNTIME
    assert 'Resources.Load<ScriptableObject>(check.resourcesPath)' in RUNTIME
    assert 'check.source!=null || !SafeResourcesPath(check.resourcesPath)' in RUNTIME
    for excluded in ('UnityWebRequest', 'HttpClient(', 'WebRequest(', 'File.Delete(',
                     'Directory.Delete(', 'AssetDatabase.DeleteAsset(',
                     'SetDirty(', 'AssetDatabase.SaveAssets('):
        assert excluded not in RUNTIME and excluded not in EDITOR
    assert 'Limited to selected direct, serialized Unity Object fields' in EDITOR
    assert 'Does not scan every serialized object' in RUNTIME


def test_only_direct_normal_unity_serialized_object_fields_are_examined():
    for contract in ('BindingFlags.DeclaredOnly','BindingFlags.Instance',
                     'Attribute.IsDefined(field,typeof(SerializeField))',
                     'field.IsNotSerialized','field.IsStatic','field.IsInitOnly',
                     'typeof(UnityEngine.Object).IsAssignableFrom(field.FieldType)',
                     'FIELD_UNSUPPORTED_OR_NOT_SERIALIZED'):
        assert contract in RUNTIME
    assert 'INCOMPLETE' in RUNTIME
    assert 'An intentionally empty field must not be described as broken' in RUNTIME


def test_explicit_case_scope_and_corrupt_report_rejected():
    for needle in ('!used.Add(check.id)', 'report.checkedCount!=report.cases.Length',
                   'report.assignedCount!=assigned', 'report.missingCount!=missing',
                   'report.unsupportedCount!=unsupported', '!ids.Add(entry.id)',
                   'first.unityVersion==second.unityVersion'):
        if needle=='first.unityVersion==second.unityVersion':
            assert 'editor.unityVersion!=player.unityVersion' in RUNTIME
        else:
            assert needle in RUNTIME
    assert 'Editor and Player case IDs must match exactly' in RUNTIME


def test_editor_labels_are_scoped_to_real_selection_and_requires_click():
    for needle in ('Selection.activeGameObject',
                   'Inspect selected scene probe — read only',
                   'Export NEW Editor baseline JSON',
                   'Choose actual built Player JSON report',
                   'Compare Editor and actual Player references',
                   'Path.IsPathRooted(absolutePath)',
                   'File.Exists(absolutePath)',
                   'FileMode.CreateNew'):
        assert needle in EDITOR or needle in RUNTIME
    assert 'AssetDatabase.SaveAssets' not in EDITOR
    assert 'AssetDatabase.CreateAsset' not in EDITOR


def test_actual_private_source_and_build_test_not_shipped_with_original_buyer_tool():
    for name in ('HprProbeQaAuthor.cs','HprProbeQaBuild.cs','HprProbeQaItem.cs',
                 'HprProbeQaAutoExit.cs','HprProbeQaCompare.cs',
                 'run_native_built_player.sh','verify_real_player_receipt.py'):
        assert (QA/name).is_file()
        assert not list(BUYER.rglob(name))
    author=(QA/'HprProbeQaBuild.cs').read_text()
    for needle in ('BuildPipeline.BuildPlayer(options)',
                   'HPR_PROBE_QA_RELOADED_EDITOR_FIELDS',
                   'ImportAssetOptions.ForceSynchronousImport',
                   'BuildTarget.StandaloneLinux64',
                   'EditorSceneManager.SaveScene(scene,scenePath)',
                   'AssetDatabase.CreateAsset(good',
                   'new HprReferenceCase{id="assigned-prefab"',
                   'new HprReferenceCase{id="private-serialized"',
                   'new HprReferenceCase{id="intentionally-null"'):
        assert needle in author


def load_verifier():
    path=QA/'verify_real_player_receipt.py'
    spec=importlib.util.spec_from_file_location('hpr_player_verifier',path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod


def make_report(origin):
    fields=[]
    for case,asset,field,status in (
        ('assigned-prefab','OriginalAssignedItem','itemPrefab','ASSIGNED'),
        ('private-serialized','OriginalAssignedItem','privatePrefab','ASSIGNED'),
        ('intentionally-null','OriginalEmptyItem','itemPrefab','REFERENCE_NULL_OR_UNSET')):
        good=status=='ASSIGNED'
        fields.append({'id':case,'assetName':asset,'fieldName':field,'status':status,
                       'referencedType':'UnityEngine.GameObject' if good else '',
                       'referencedName':'HPR_ProbePrefab' if good else '',
                       'sourceLookup':'DIRECT_SCENE'})
    return {'schema':2,'origin':origin,'unityVersion':'6000.6.8f1',
            'checkedCount':3,'assignedCount':2,'missingCount':1,
            'unsupportedCount':0,'status':'NULL_OR_UNSET_SELECTED_REFERENCE',
            'cases':fields}


def test_pure_independent_verifier_accepts_only_actual_log_marker_and_original_case_set(tmp_path):
    verify=load_verifier()
    baseline=tmp_path/'baseline.json';baseline.write_text(json.dumps(make_report('EDITOR')))
    log=tmp_path/'player.log'
    log.write_text('other log\nHPR_PLAYER_REFERENCE_RECEIPT='+json.dumps(make_report('PLAYER'))+
                   '\nHPR_PLAYER_PROBE_PRIVATE_RUNTIME_AUTOEXIT_PASS\n')
    destination=tmp_path/'new_player.json'
    receipt=verify.verify_log(log,baseline,destination)
    assert receipt['status']=='PASS_ORIGINAL_BUILT_PLAYER_OBSERVED'
    assert receipt['assigned_in_editor_and_player']==2
    with pytest.raises(ValueError,match='repeated'):
        verify.verify_log(log,baseline,destination)


@pytest.mark.parametrize('changed',('missing-end','not-runtime','changed-assignment','wrong-version','duplicate-marker'))
def test_pure_independent_player_verification_rejects_incomplete_or_mismatched_receipts(tmp_path,changed):
    verify=load_verifier()
    e=make_report('EDITOR');p=make_report('PLAYER')
    if changed=='not-runtime':p['origin']='EDITOR'
    if changed=='changed-assignment':p['cases'][0]['status']='REFERENCE_NULL_OR_UNSET'
    if changed=='wrong-version':p['unityVersion']='2022.3.22f1'
    content='HPR_PLAYER_REFERENCE_RECEIPT='+json.dumps(p)+'\n'
    if changed!='missing-end':content+='HPR_PLAYER_PROBE_PRIVATE_RUNTIME_AUTOEXIT_PASS\n'
    if changed=='duplicate-marker':content+='HPR_PLAYER_REFERENCE_RECEIPT='+json.dumps(p)+'\n'
    baseline=tmp_path/'baseline.json';baseline.write_text(json.dumps(e))
    log=tmp_path/'player.log';log.write_text(content)
    with pytest.raises(ValueError):
        verify.verify_log(log,baseline,tmp_path/'fresh.json')


def test_path_only_resources_mode_is_unpinned_and_has_distinct_source_loss_result():
    for code in ('public string resourcesPath=""',
                 'Resources.Load<ScriptableObject>(check.resourcesPath)',
                 'sourceLookup=useResources ? "RESOURCES:"+check.resourcesPath',
                 'PLAYER_SCRIPTABLEOBJECT_SOURCE_NOT_LOADED',
                 'playerSourceMissingCaseIds',
                 'entry.status=="SOURCE_NOT_LOADED"',
                 'SafeResourcesPath(check.resourcesPath)',
                 'sourceLookup.Substring(10)'):
        assert code in RUNTIME
    assert 'ScriptableObject sources not loaded' in EDITOR
    assert 'private' not in 'arbitrary'  # This is a narrow path-only feature, not general field extraction.


def test_pure_resources_path_only_verifier_requires_both_originals_unpinned(tmp_path,monkeypatch):
    verifier=load_verifier()
    before=make_report('EDITOR');after=make_report('PLAYER')
    paths={'assigned-prefab':'RESOURCES:OriginalAssignedItem',
           'private-serialized':'RESOURCES:OriginalAssignedItem',
           'intentionally-null':'RESOURCES:OriginalEmptyItem'}
    for report in (before,after):
        for item in report['cases']:
            item['sourceLookup']=paths[item['id']]
    e=tmp_path/'editor.json';e.write_text(json.dumps(before))
    log=tmp_path/'player.log'
    log.write_text('HPR_PLAYER_REFERENCE_RECEIPT='+json.dumps(after)+
                   '\nHPR_PLAYER_PROBE_PRIVATE_RUNTIME_AUTOEXIT_PASS\n')
    monkeypatch.setenv('HPR_PROBE_QA_RESOURCES_ONLY','1')
    assert verifier.verify_log(log,e,tmp_path/'actual-player.json')['status']=='PASS_ORIGINAL_BUILT_PLAYER_OBSERVED'
    after['cases'][0]['sourceLookup']='DIRECT_SCENE'
    log.write_text('HPR_PLAYER_REFERENCE_RECEIPT='+json.dumps(after)+
                   '\nHPR_PLAYER_PROBE_PRIVATE_RUNTIME_AUTOEXIT_PASS\n')
    with pytest.raises(ValueError,match='unexpectedly pinned'):
        verifier.verify_log(log,e,tmp_path/'reject.json')


def test_new_receipts_are_schema_two_with_explicit_lookup_and_old_schema_disallowed():
    assert RUNTIME.count('public int schema=2;')==2
    assert 'report.schema!=2' in RUNTIME
    assert 'entry.sourceLookup==null' in RUNTIME
    assert 'sourceLookup' in (QA/'verify_real_player_receipt.py').read_text()
    comparator=(QA/'HprProbeQaCompare.cs').read_text()
    assert 'PLAYER_SCRIPTABLEOBJECT_SOURCE_NOT_LOADED' in comparator
    assert 'missingCompare.playerSourceMissingCaseIds.SequenceEqual(new[]{"assigned-prefab"})' in comparator


def test_resources_mode_fixture_really_removes_scene_pinning_and_saves_scene():
    qa=(QA/'HprProbeQaBuild.cs').read_text()
    for text in ('HPR_PROBE_QA_RESOURCES_ONLY','probe.checks[0].source=null',
                 'probe.checks[1].source=null','probe.checks[2].source=null',
                 'probe.checks[0].resourcesPath="OriginalAssignedItem"',
                 'probe.checks[2].resourcesPath="OriginalEmptyItem"',
                 'EditorSceneManager.SaveScene(scene,scenePath)'):
        assert text in qa
    package=(BUYER/'README.md').read_text()
    assert "leave a check's **Source** field empty" in package
    assert 'force it into the build' in package


def _original_meta_guid(path):
    import re
    data=path.read_text()
    found=re.search(r'(?m)^guid: ([0-9a-f]{32})$',data)
    assert found, str(path)
    return found.group(1)


def test_real_unity_authored_demo_scene_has_original_stable_script_and_prefab_guids():
    scene=(BUYER/'Demo/Scenes/HPR_Player_Reference_Probe_Demo.unity').read_text()
    runtime_guid=_original_meta_guid(BUYER/'Runtime/HprPlayerReferenceProbe.cs.meta')
    item_guid=_original_meta_guid(BUYER/'Demo/Scripts/HprPlayerReferenceDemoItem.cs.meta')
    prefab_guid=_original_meta_guid(BUYER/'Demo/Resources/HPRSample/HPR_Demo_Reference.prefab.meta')
    assigned=(BUYER/'Demo/Resources/HPRSample/AssignedItem.asset').read_text()
    empty=(BUYER/'Demo/Resources/HPRSample/OptionalItem.asset').read_text()
    assert scene.startswith('%YAML 1.1')
    assert scene.count('--- !u!1 &')>=12
    assert 'HPR | Reference Probe (select me)' in scene
    assert 'guid: '+runtime_guid in scene
    assert 'guid: '+item_guid in assigned and 'guid: '+item_guid in empty
    assert 'guid: '+prefab_guid in assigned
    assert 'itemPrefab: {fileID: 0}' in empty
    assert 'HPR Demo Camera' in scene
    assert 'HPR Original Key Light' in scene


def test_original_demo_scene_uses_two_unpinned_resources_paths_and_readable_labels():
    scene=(BUYER/'Demo/Scenes/HPR_Player_Reference_Probe_Demo.unity').read_text()
    assert scene.count('source: {fileID: 0}')==2
    assert scene.count('resourcesPath: HPRSample/AssignedItem')==1
    assert scene.count('resourcesPath: HPRSample/OptionalItem')==1
    assert scene.count('fieldName: itemPrefab')==2
    assert 'm_Text: ASSIGNED' in scene and 'm_Text: EMPTY' in scene
    assert 'PLAYER REFERENCE PROBE' in scene
    docs=(BUYER/'Demo/README.md').read_text()
    assert 'documentation' in docs.lower()
    assert 'not' in docs.lower() and 'engine bug' in docs.lower()
    assert 'no direct ScriptableObject references' in docs


def test_buyer_offline_documentation_meets_validator_scope_in_actual_buyer_root():
    docs=(BUYER/'README.md').read_text()
    assert 'documentation' in docs.lower()
    for step in ('Tools → HPR → Player Reference Probe','Demo/README.md',
                 'resourcesPath','Application.persistentDataPath',
                 'Build and run a real game Player',
                 'disable or remove the diagnostic'):
        assert step.lower() in docs.lower()
    assert 'no direct ScriptableObject references' in docs or 'strong ScriptableObject' in docs


def test_original_native_demo_author_and_independent_buyer_test_are_private():
    author=(QA/'HprProbeQaCreateDemo.cs').read_text()
    buyer=(QA/'HprProbeQaDemoBuyer.cs').read_text()
    runner=(QA/'run_native_demo_buyer.sh').read_text()
    for step in ('PrefabUtility.SaveAsPrefabAsset',
                 'ScriptableObject.CreateInstance<HprPlayerReferenceDemoItem>',
                 'EditorSceneManager.SaveScene',
                 'source=null,','resourcesPath="HPRSample/AssignedItem"'):
        assert step in author
    for step in ('HprReferenceInspector.Inspect(configured,"EDITOR")',
                 'configured.All(v=>v.source==null)',
                 'BuildPipeline.BuildPlayer',
                 'HPR_PLAYER_REFERENCE_ORIGINAL_DEMO_BUYER_NATIVE_PASS'):
        assert step in buyer
    assert '2022.3.22f1' in runner and '6000.6.8f1' in runner
    assert not list(BUYER.rglob('HprProbeQaDemoBuyer.cs'))
    assert not list(BUYER.rglob('HprProbeQaCreateDemo.cs'))


def _make_private_original_unity_archive_test(tmp_path, extra_path=None):
    import io
    import tarfile
    import importlib.util
    spec=importlib.util.spec_from_file_location('hpr_original_package_check',
        QA/'verify_original_demo_archive.py')
    validator=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    source=tmp_path/'HPRPlayerReferenceProbe'
    archive=tmp_path/'original.unitypackage'
    for name in sorted(validator.REQUIRED):
        target=source/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(b'original first party test data\n'+name.encode())
    entries=[source]+sorted(source.rglob('*'))
    with tarfile.open(archive,'w:gz') as tar:
        def add(name,content):
            info=tarfile.TarInfo(name)
            info.size=len(content)
            tar.addfile(info,io.BytesIO(content))
        for i,target in enumerate(entries,1):
            guid=f'{i:032x}'
            rel=target.relative_to(source).as_posix()
            path=validator.ROOT if rel=='.' else validator.ROOT+'/'+rel
            metadata=f'fileFormatVersion: 2\nguid: {guid}\n'.encode()
            if target.is_dir():
                metadata+=b'folderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n'
            target.with_name(target.name+'.meta').write_bytes(metadata)
            add(guid+'/pathname',path.encode())
            if target.is_file():
                add(guid+'/asset',target.read_bytes())
            add(guid+'/asset.meta',metadata)
        if extra_path is not None:
            guid='f'*32
            add(guid+'/pathname',(validator.ROOT+'/'+extra_path).encode())
            add(guid+'/asset',b'private or unsafe unexpected entry')
            add(guid+'/asset.meta',f'fileFormatVersion: 2\nguid: {guid}\n'.encode())
    return archive,source,validator


def test_source_parity_archive_validator_checks_real_customer_file_meta_bytes(tmp_path):
    archive,source,validator=_make_private_original_unity_archive_test(tmp_path)
    report=validator.verify(archive,source)
    assert report['status']=='ORIGINAL_UNITY_CUSTOMER_CONTENT_MATCHES_SOURCE_WITH_EXPLICIT_META_NORMALIZATION'
    assert report['consumer_exported_paths']==len(validator.source_inventory(source))
    assert report['all_folder_and_file_guids_verified']
    assert report['complete_original_inventory_verified']
    chosen=source/'README.md'
    chosen.write_text('changed source: invalid archive comparison')
    with pytest.raises(ValueError,match='does not match original source'):
        validator.verify(archive,source)


def test_source_parity_archive_verifier_catches_wrong_meta_guid(tmp_path):
    archive,source,validator=_make_private_original_unity_archive_test(tmp_path)
    meta=source/'Runtime/HprPlayerReferenceProbe.cs.meta'
    meta.write_text('fileFormatVersion: 2\nguid: ffffffffffffffffffffffffffffffff\n')
    with pytest.raises(ValueError,match='GUID mismatch'):
        validator.verify(archive,source)


@pytest.mark.parametrize('extra_path',('qa/HprProbeQaHidden.cs','../outside.txt'))
def test_source_parity_archive_verifier_rejects_private_fixture_and_escaping(tmp_path,extra_path):
    archive,source,validator=_make_private_original_unity_archive_test(tmp_path,extra_path)
    with pytest.raises(ValueError,match='Private fixture|unsafe exported archive pathname'):
        validator.verify(archive,source)


def test_unity2022_script_meta_normalization_accepts_only_default_importer_values():
    import importlib.util
    spec=importlib.util.spec_from_file_location('hpr_original_meta_guard',
        QA/'verify_original_demo_archive.py')
    v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    raw=b'fileFormatVersion: 2\nguid: 1234567890abcdef1234567890abcdef'
    default=(raw.decode()+'\nMonoImporter:\n'
             '  externalObjects: {}\n'
             '  serializedVersion: 2\n'
             '  defaultReferences: []\n'
             '  executionOrder: 0\n'
             '  icon: {instanceID: 0}\n'
             '  userData: \n'
             '  assetBundleName: \n'
             '  assetBundleVariant: ').encode()
    assert v._accepted_unity2022_monoimporter_default(raw,default,
        'Assets/HPRPlayerReferenceProbe/Runtime/HprPlayerReferenceProbe.cs')
    assert not v._accepted_unity2022_monoimporter_default(raw,default.replace(b'executionOrder: 0',
        b'executionOrder: 5'),'Assets/HPRPlayerReferenceProbe/Runtime/HprPlayerReferenceProbe.cs')
    assert not v._accepted_unity2022_monoimporter_default(raw,default,
        'Assets/HPRPlayerReferenceProbe/Demo/Materials/Original.mat')
    assert not v._accepted_unity2022_monoimporter_default(raw,default.replace(b'icon: {instanceID: 0}',
        b'icon: {instanceID: 1}'),'Assets/HPRPlayerReferenceProbe/Runtime/HprPlayerReferenceProbe.cs')


def test_genuine_unity_editor_button_click_qa_uses_moused_event_not_private_invocation():
    qa=(QA/'HprProbeQaActualClicks.cs').read_text()
    runner=(QA/'run_native_actual_button_clicks.sh').read_text()
    for phrase in ('HPR_ACTUAL_UI_CLICK_READY_FOR_HUMAN_INPUT_EMULATION',
                   'HPR_ACTUAL_UI_INSPECT_BUTTON_CLICK_PASS',
                   'HPR_ACTUAL_UI_COMPARE_BUTTON_CLICK_PASS',
                   'scanned-by-actual-click.txt', 'compared-by-actual-click.txt',
                   '!EditorSceneManager.GetActiveScene().isDirty',
                   'EditorApplication.update+=Poll',
                   'Require(baseline.GetValue(window)==null'):
        assert phrase in qa
    assert 'xdotool' not in runner  # Human-like clicks must occur externally after UI inspection.
    assert 'HPR_ACTUAL_MOUSE_BUTTONS_READY' in runner
    assert 'Xvfb :143' in runner
    assert 'software terms' in runner.lower()
    assert 'HPRPlayerReferenceProbe' in runner
    assert not list(BUYER.rglob('HprProbeQaActualClicks.cs'))


def test_runtime_capture_on_demand_is_opt_in_and_bounded():
    assert 'public bool manualOnly=false;' in RUNTIME
    assert 'public int maxCaptures=8;' in RUNTIME
    assert 'if(!manualOnly)CaptureNow();' in RUNTIME
    assert 'public bool CaptureNow()' in RUNTIME
    assert 'if(Application.isEditor)return false;' in RUNTIME
    assert 'maxCaptures<=0 ? 8 : Mathf.Clamp(maxCaptures,1,32)' in RUNTIME
    assert 'if(captureCount>=limit)' in RUNTIME
    assert 'if(!limitWarningEmitted)' in RUNTIME
    assert 'captureCount++; // Failed inspections also count' in RUNTIME
    assert 'HPR_PLAYER_REFERENCE_CAPTURE_LIMIT_REACHED' in RUNTIME
    assert 'returns `true` if it successfully logged an original receipt' in (BUYER/'README.md').read_text()
    assert 'CaptureNow()' in (BUYER/'README.md').read_text()


def test_native_manual_capture_is_tested_after_player_frames_and_bounded():
    q=(QA/'HprProbeQaManualTrigger.cs').read_text()
    builder=(QA/'HprProbeQaBuild.cs').read_text()
    runner=(QA/'run_native_manual_late_capture.sh').read_text()
    verifier=(QA/'verify_real_player_receipt.py').read_text()
    for phrase in ('for(var frame=0;frame<6;frame++)yield return null;',
                   'source.itemPrefab=null;',
                   'HPR_PRIVATE_INTENTIONAL_LATE_PLAYER_FIELD_CLEAR_DONE',
                   'probe.CaptureNow()',
                   'HPR_PRIVATE_MANUAL_LATE_QA_CAPTURE_SUCCESS',
                   'HPR_PRIVATE_MANUAL_LATE_QA_CAPTURE_LIMIT_ENFORCED'):
        assert phrase in q
    for phrase in ('HPR_PROBE_QA_MANUAL_LATE','probe.manualOnly=true;',
                   'probe.maxCaptures=1;',
                   'GetComponent<HprProbeQaManualTrigger>().source=realGood'):
        assert phrase in builder
    assert 'HPR_PROBE_QA_MANUAL_LATE=1' in runner
    assert '--expect-manual-late-loss' in runner
    assert 'HPR_PRIVATE_MANUAL_LATE_QA_CAPTURE_LIMIT_ENFORCED' in runner
    assert 'expect_late_loss' in verifier
    assert 'HPR_PLAYER_REFERENCE_CAPTURE_LIMIT_REACHED' in verifier
    assert not list(BUYER.rglob('HprProbeQaManualTrigger.cs'))


def test_private_verifier_proves_late_manual_capture_fixture_receipt_and_limit(tmp_path):
    verify=load_verifier()
    editor=make_report('EDITOR');player=make_report('PLAYER')
    gone=player['cases'][0]
    assert gone['id']=='assigned-prefab'
    gone['status']='REFERENCE_NULL_OR_UNSET'
    gone['referencedType']='';gone['referencedName']=''
    player['assignedCount']=1;player['missingCount']=2
    edit=tmp_path/'actual-original-editor.json';edit.write_text(json.dumps(editor))
    logfile=tmp_path/'private-original-player.log'
    def write_log(markers):
        entries=list(markers)
        entries.insert(1,'HPR_PLAYER_REFERENCE_RECEIPT='+json.dumps(player))
        logfile.write_text('\n'.join(entries)+
            '\nHPR_PLAYER_PROBE_PRIVATE_RUNTIME_AUTOEXIT_PASS\n')
    required=('HPR_PRIVATE_INTENTIONAL_LATE_PLAYER_FIELD_CLEAR_DONE',
              'HPR_PRIVATE_MANUAL_LATE_QA_CAPTURE_SUCCESS',
              'HPR_PLAYER_REFERENCE_CAPTURE_LIMIT_REACHED',
              'HPR_PRIVATE_MANUAL_LATE_QA_CAPTURE_LIMIT_ENFORCED')
    write_log(required)
    result=verify.verify_log(logfile,edit,tmp_path/'one_real_player_report.json',
                             expect_late_loss=True)
    assert result['status']=='PASS_INTENTIONAL_LATE_MANUAL_BUILT_PLAYER_REFERENCE_LOSS'
    for i,marker in enumerate(required):
        write_log([x for x in required if x!=marker])
        with pytest.raises(ValueError,match='Missing or out-of-order real late capture'):
            verify.verify_log(logfile,edit,tmp_path/f'denied_without_marker_{i}.json',
                              expect_late_loss=True)


def test_actual_native_gui_file_dialog_qa_has_real_click_evidence_and_scene_guard():
    qa = QA / 'HprProbeQaFileDialogs.cs'
    assert qa.is_file()
    source = qa.read_text()
    for required in (
        'EditorSceneManager.OpenScene(Demo,OpenSceneMode.Single)',
        'Selection.activeGameObject=probe.gameObject;',
        'Require(baseline.GetValue(win)==null',
        'REAL_INSPECT_BUTTON_CLICK_PASS',
        'REAL_EXPORT_BUTTON_AND_NATIVE_SAVE_FILE_DIALOG_PASS',
        'REAL_NATIVE_OPEN_FILE_DIALOG_EDITOR_REPORT_SELECTED',
        'REAL_NATIVE_OPEN_FILE_DIALOG_PLAYER_REPORT_SELECTED',
        'REAL_BOTH_NATIVE_FILE_CHOOSERS_COMPARE_CLICK_PASS',
        'EditorSceneManager.GetActiveScene().isDirty',
        'FileMode.CreateNew',
    ):
        assert required in source, required
    warm = (QA / 'run_native_file_dialog_clicks_warm.sh').read_text()
    assert 'Xvfb :143' in warm
    assert 'HprProbeQaFileDialogs.Run' in warm
    assert 'comparison-complete.txt' in warm
    assert 'echo' in warm


def test_new_current_original_archive_author_is_explicitly_exact_source_and_create_only():
    author = (QA / 'run_current_matched_native_archive.sh').read_text()
    for required in (
        '2022.3.22f1|6000.6.8f1',
        '! -e "$work"',
        'stage_original_probe_source.py" "$source" "$project/Assets"',
        'HPR_PLAYER_PROBE_EXPECTED_ROOT_GUID',
        'HprProbeQaAuthor.Run',
        'verify_original_demo_archive.py',
        "b'CaptureNow()'",
        "b'manualOnly'",
    ):
        assert required in author, required
    importer = (QA / 'run_native_demo_buyer.sh').read_text()
    validator = (QA / 'run_native_official_ast.sh').read_text()
    for release in ('HPR_Player_Reference_Probe_2022-3-22f1_current_original.unitypackage',
                    'HPR_Player_Reference_Probe_6000-6-8f1_current_original.unitypackage'):
        assert release in importer and release in validator
    assert 'Refusing arbitrary unverified source package' in importer
    assert 'Refusing unrecognized original first-party source archive' in validator


def test_unity2022_real_buyer_player_qa_preserves_original_demo_and_autostops():
    source = (QA / 'HprProbeQa2022ActualPlayer.cs').read_text()
    for marker in (
        'Application.unityVersion=="2022.3.22f1"',
        'EditorSceneManager.OpenScene(sourceScene,OpenSceneMode.Single)',
        'scene.rootCount==13',
        'c.source==null && !string.IsNullOrWhiteSpace(c.resourcesPath)',
        'EditorSceneManager.SaveScene(scene,clonedScene,true)',
        'HprProbeQaAutoExit',
        'BuildTarget.StandaloneLinux64',
        'BuildPipeline.BuildPlayer',
        'HPR_REAL_UNITY2022_BUILT_PLAYER_PASS',
    ):
        assert marker in source, marker
    workflow = (QA / 'run_native_unity2022_actual_player.sh').read_text()
    assert '! -e "$work"' in workflow
    assert 'actual-Unity2022-Player.log' in workflow
    assert 'verify_unity2022_actual_demo_player.py' in workflow
    assert 'HPR_TRUE_UNITY2022_ORIGINAL_BUILT_PLAYER_PASS' in workflow
    assert not list(BUYER.rglob('HprProbeQa2022ActualPlayer.cs'))


def test_independent_real_unity2022_player_receipt_verifier_rejects_wrong_identity(tmp_path):
    import importlib.util
    path = QA / 'verify_unity2022_actual_demo_player.py'
    spec = importlib.util.spec_from_file_location('qa2022check', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = {
        'schema': 2, 'origin': 'EDITOR', 'unityVersion': '2022.3.22f1',
        'checkedCount': 2, 'assignedCount': 1, 'missingCount': 1,
        'unsupportedCount': 0, 'status': 'NULL_OR_UNSET_SELECTED_REFERENCE',
        'cases': [
            {'id':'demo-assigned','fieldName':'itemPrefab',
             'sourceLookup':'RESOURCES:HPRSample/AssignedItem','assetName':'AssignedItem',
             'status':'ASSIGNED','referencedType':'UnityEngine.GameObject',
             'referencedName':'HPR_Demo_Reference'},
            {'id':'demo-intentionally-empty','fieldName':'itemPrefab',
             'sourceLookup':'RESOURCES:HPRSample/OptionalItem','assetName':'OptionalItem',
             'status':'REFERENCE_NULL_OR_UNSET','referencedType':'','referencedName':''},
        ],
    }
    editor = tmp_path / 'editor.json'
    editor.write_text(json.dumps(report))
    player = json.loads(json.dumps(report))
    player['origin'] = 'PLAYER'
    log = tmp_path / 'actual-player.log'
    log.write_text('HPR_PLAYER_REFERENCE_RECEIPT='+json.dumps(player)+
                   '\nHPR_PLAYER_PROBE_PRIVATE_RUNTIME_AUTOEXIT_PASS\n')
    assert module.verify(log,editor,tmp_path/'first.json')['status']=='PASS_ACTUAL_UNITY2022_LINUX_PLAYER_ORIGINAL_DEMO'
    with pytest.raises(ValueError,match='repeated'):
        module.verify(log,editor,tmp_path/'first.json')
    player['cases'][0]['sourceLookup']='DIRECT_SCENE'
    log.write_text('HPR_PLAYER_REFERENCE_RECEIPT='+json.dumps(player)+
                   '\nHPR_PLAYER_PROBE_PRIVATE_RUNTIME_AUTOEXIT_PASS\n')
    with pytest.raises(ValueError,match='Scene-based reference pin'):
        module.verify(log,editor,tmp_path/'second.json')


def test_strict_archive_rejects_changed_root_identity(tmp_path):
    archive,source,validator=_make_private_original_unity_archive_test(tmp_path)
    meta=source.with_name(source.name+'.meta')
    meta.write_bytes(meta.read_bytes().replace(b'00000000000000000000000000000001',b'eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee'))
    with pytest.raises(ValueError,match='GUID mismatch'):
        validator.verify(archive,source)


def test_strict_archive_rejects_nested_folder_import_settings_change(tmp_path):
    archive,source,validator=_make_private_original_unity_archive_test(tmp_path)
    meta=source/'Demo.meta'
    meta.write_bytes(meta.read_bytes()+b'  assetBundleName: changed\n')
    with pytest.raises(ValueError,match='import settings differ'):
        validator.verify(archive,source)


def test_strict_archive_rejects_omitted_original_extra_asset(tmp_path):
    archive,source,validator=_make_private_original_unity_archive_test(tmp_path)
    original=source/'Extra.txt'
    original.write_text('not shipped')
    original.with_name(original.name+'.meta').write_text('fileFormatVersion: 2\nguid: eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee\n')
    with pytest.raises(ValueError,match='Incomplete or unexpected archive inventory'):
        validator.verify(archive,source)


def test_stage_preserves_root_meta_and_refuses_overwrite(tmp_path):
    import subprocess,sys
    _,source,validator=_make_private_original_unity_archive_test(tmp_path)
    assets=tmp_path/'fresh-assets';assets.mkdir()
    script=QA/'stage_original_probe_source.py'
    cmd=[sys.executable,str(script),str(source),str(assets)]
    receipt=json.loads(subprocess.check_output(cmd,text=True))
    assert receipt['root_guid']==validator.source_inventory(source)[validator.ROOT][2]
    assert receipt['verified_paths']==len(validator.source_inventory(source))
    assert (assets/(source.name+'.meta')).read_bytes()==source.with_name(source.name+'.meta').read_bytes()
    actual=assets/source.name/'README.md'
    actual.write_text('preserve existing buyer')
    repeated=subprocess.run(cmd,capture_output=True,text=True)
    assert repeated.returncode!=0 and 'Refusing to replace existing' in repeated.stderr
    assert actual.read_text()=='preserve existing buyer'
    verify=subprocess.run([sys.executable,str(script),'--verify-existing',str(source),str(assets)],
                          capture_output=True,text=True)
    assert verify.returncode!=0 and 'payload mismatch' in verify.stderr


def test_native_author_checks_root_and_all_fresh_stages_preserve_it():
    for name in ('run_current_matched_native_archive.sh','run_native_final_ui_author.sh',
                 'run_native_demo_seed.sh','run_native_demo_refine.sh',
                 'run_native_demo_refine_labels_v2.sh','run_native_built_player.sh'):
        source=(QA/name).read_text()
        assert 'stage_original_probe_source.py' in source
        assert 'HPR_PLAYER_PROBE_EXPECTED_ROOT_GUID' in source
    author=(QA/'HprProbeQaAuthor.cs').read_text()
    assert 'AssetDatabase.AssetPathToGUID(root)' in author
    assert author.index('HPR_PLAYER_REFERENCE_AUTHOR_ROOT_GUID_MISMATCH')<author.index('AssetDatabase.ExportPackage')
    old=(QA/'run_native_2022_retail_archive.sh').read_text()
    assert '--verify-existing' in old
    assert old.index('--verify-existing')<old.index('timeout 420')


def test_release_consumers_require_exact_archive_or_existing_tree_before_mutation():
    for name,create in (
        ('run_native_demo_buyer.sh','mkdir -p "$work"'),
        ('run_native_official_ast.sh','mkdir -p "$out"'),
        ('run_existing_original_buyer.sh','mkdir -p "$work"'),
    ):
        source=(QA/name).read_text()
        assert source.index('verify_original_demo_archive.py')<source.index(create)
    source=(QA/'run_native_unity2022_actual_player.sh').read_text()
    assert source.index('--verify-existing')<source.index('mkdir -p "$work"')
    source=(QA/'run_native_built_player.sh').read_text()
    assert source.index('verify_original_demo_archive.py')<source.index('run create-buyer')


def test_fresh_native_import_identity_gates_surround_buyer_qa():
    for name,import_step,qa_step,after_receipt in (
        ('run_native_demo_buyer.sh','run "$version" import-real-original-package',
         'run "$version" real-native-demo-acceptance','post-qa-source-identity.json'),
        ('run_native_official_ast.sh','run buyer-import-original','run official-validation',
         'post-validator-source-identity.json'),
        ('run_native_built_player.sh','run buyer-original-package-import',
         'run original-editor-and-actual-player-build','post-qa-source-identity.json'),
        ('run_existing_original_buyer.sh','run original-product-package-import',
         'run editor-baseline-and-actual-Linux64-build','post-qa-source-identity.json'),
    ):
        source=(QA/name).read_text()
        imported=source.index(import_step)
        qa=source.index(qa_step)
        assert imported < source.index('imported-source-identity.json',imported) < qa
        assert qa < source.index(after_receipt,qa)
        assert source.count('--verify-existing')>=2
