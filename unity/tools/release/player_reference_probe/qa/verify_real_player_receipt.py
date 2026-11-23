#!/usr/bin/env python3
"""Verify exact real built Player log & create-only extracted receipt; no simulator claims."""
import json
import os
import pathlib
import sys


def verify_log(logpath: pathlib.Path, baselinepath: pathlib.Path, output: pathlib.Path,
               expect_intentional_loss: bool = False,
               expect_late_loss: bool = False) -> dict:
    if not logpath.is_file() or not baselinepath.is_file() or output.exists():
        raise ValueError('Missing original Player log or baseline, or repeated receipt creation')
    log=logpath.read_text(errors='replace')
    marker='HPR_PLAYER_REFERENCE_RECEIPT='
    items=[line.partition(marker)[2].strip() for line in log.splitlines() if marker in line]
    if len(items)!=1 or 'HPR_PLAYER_PROBE_PRIVATE_RUNTIME_AUTOEXIT_PASS' not in log:
        raise ValueError('Expected one real runtime receipt and actual Player auto-exit evidence')
    player=json.loads(items[0]);editor=json.loads(baselinepath.read_text())
    if expect_late_loss and expect_intentional_loss:
        raise ValueError('Negative test fixture modes must not overlap')
    if expect_late_loss:
        required_sequence=(
            'HPR_PRIVATE_INTENTIONAL_LATE_PLAYER_FIELD_CLEAR_DONE',
            'HPR_PLAYER_REFERENCE_RECEIPT=',
            'HPR_PRIVATE_MANUAL_LATE_QA_CAPTURE_SUCCESS',
            'HPR_PLAYER_REFERENCE_CAPTURE_LIMIT_REACHED',
            'HPR_PRIVATE_MANUAL_LATE_QA_CAPTURE_LIMIT_ENFORCED',
            'HPR_PLAYER_PROBE_PRIVATE_RUNTIME_AUTOEXIT_PASS')
        positions=[log.find(evidence) for evidence in required_sequence]
        if any(n<0 for n in positions) or positions!=sorted(positions) or len(set(positions))!=len(positions):
            raise ValueError('Missing or out-of-order real late capture, limit or Player-exit evidence')
    if expect_intentional_loss and 'HPR_PRIVATE_INTENTIONAL_PLAYER_FIELD_CLEAR_DONE' not in log:
        raise ValueError('Missing explicit evidence of intentional Player-only negative fixture')
    expect_loss=expect_intentional_loss or expect_late_loss
    for report,origin in ((player,'PLAYER'),(editor,'EDITOR')):
        expected_assigned=1 if origin=='PLAYER' and expect_loss else 2
        expected_missing=2 if origin=='PLAYER' and expect_loss else 1
        if (report['schema']!=2 or report['origin']!=origin or report['checkedCount']!=3
                or report['assignedCount']!=expected_assigned or report['missingCount']!=expected_missing
                or report['unsupportedCount']!=0
                or report['status']!='NULL_OR_UNSET_SELECTED_REFERENCE'):
            raise ValueError('Unexpected or incomplete genuine reference report: '+origin)
        records={r['id']:r for r in report['cases']}
        if set(records)!={'assigned-prefab','private-serialized','intentionally-null'}:
            raise ValueError('Actual selected probe case labels differ')
        for n in (('private-serialized',) if origin=='PLAYER' and expect_loss
                  else ('assigned-prefab','private-serialized')):
            if (records[n]['status']!='ASSIGNED' or
                    records[n]['referencedName']!='HPR_ProbePrefab' or
                    records[n]['referencedType']!='UnityEngine.GameObject'):
                raise ValueError('Actual Player original positive prefab reference not retained')
        if origin=='PLAYER' and expect_loss:
            if records['assigned-prefab']['status']!='REFERENCE_NULL_OR_UNSET':
                raise ValueError('Actual Player fixture did not clear originally assigned prefab')
        if records['intentionally-null']['status']!='REFERENCE_NULL_OR_UNSET':
            raise ValueError('Intentionally missing reference not detected')
    if os.environ.get('HPR_PROBE_QA_RESOURCES_ONLY')=='1':
        expected={'assigned-prefab':'RESOURCES:OriginalAssignedItem',
                  'private-serialized':'RESOURCES:OriginalAssignedItem',
                  'intentionally-null':'RESOURCES:OriginalEmptyItem'}
        for report in (player,editor):
            for entry in report['cases']:
                if entry.get('sourceLookup')!=expected.get(entry['id']):
                    raise ValueError('Path-only original buyer fixture unexpectedly pinned a source')
    if player['unityVersion']!=editor['unityVersion']:
        raise ValueError('Actual original Editor and Player Unity versions differ')
    for a,b in zip(sorted(player['cases'],key=lambda e:e['id']),
                   sorted(editor['cases'],key=lambda e:e['id'])):
        for k in ('id','assetName','fieldName','sourceLookup','status','referencedName','referencedType'):
            if a[k]!=b[k] and not (expect_loss and a['id']=='assigned-prefab' and
                                   k in ('status','referencedName','referencedType')):
                raise ValueError('Actual direct-reference fingerprint changed: '+a['id']+' '+k)
    with output.open('x',encoding='utf-8') as f:
        json.dump(player,f,indent=2,sort_keys=True)
        f.write('\n')
    return {'status':('PASS_INTENTIONAL_LATE_MANUAL_BUILT_PLAYER_REFERENCE_LOSS' if expect_late_loss
                       else 'PASS_INTENTIONAL_BUILT_PLAYER_REFERENCE_LOSS' if expect_intentional_loss
                       else 'PASS_ORIGINAL_BUILT_PLAYER_OBSERVED'),
            'actual_Unity_version':player['unityVersion'],
            'original_checks':3,'assigned_in_editor_and_player':(1 if expect_loss else 2),
            'intentionally_null_in_both':1,'unsupported':0,
            'real_runtime_log':str(logpath),'original_player_receipt':str(output)}


if __name__=='__main__':
    if len(sys.argv) not in (4,5) or (len(sys.argv)==5 and sys.argv[4] not in
        ('--expect-loss','--expect-manual-late-loss')):
        raise SystemExit('usage: verifier LOG EDITOR_BASELINE NEW_PLAYER_JSON '
                         '[--expect-loss|--expect-manual-late-loss]')
    result=verify_log(*map(pathlib.Path,sys.argv[1:4]),
        expect_intentional_loss=len(sys.argv)==5 and sys.argv[4]=='--expect-loss',
        expect_late_loss=len(sys.argv)==5 and sys.argv[4]=='--expect-manual-late-loss')
    print(json.dumps(result,sort_keys=True))
