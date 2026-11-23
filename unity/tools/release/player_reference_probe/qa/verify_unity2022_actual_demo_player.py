#!/usr/bin/env python3
"""Independent original Unity2022 demo runtime receipt verification; no fake Player."""
import json
from pathlib import Path
import sys

def verify(log_path:Path,editor_path:Path,out_path:Path):
    if not log_path.is_file() or not editor_path.is_file() or out_path.exists():
        raise ValueError('Original Player log or Editor baseline missing or repeated output')
    log=log_path.read_text(errors='replace')
    marker='HPR_PLAYER_REFERENCE_RECEIPT='
    lines=[line.split(marker,1)[1].strip() for line in log.splitlines() if marker in line]
    if len(lines)!=1 or 'HPR_PLAYER_PROBE_PRIVATE_RUNTIME_AUTOEXIT_PASS' not in log:
        raise ValueError('No unique actual original Unity2022 Player runtime and auto-exit evidence')
    editor=json.loads(editor_path.read_text());player=json.loads(lines[0])
    for report,origin in ((editor,'EDITOR'),(player,'PLAYER')):
        if (report['schema']!=2 or report['origin']!=origin or
            report['unityVersion']!='2022.3.22f1' or report['checkedCount']!=2 or
            report['assignedCount']!=1 or report['missingCount']!=1 or
            report['unsupportedCount']!=0 or
            report['status']!='NULL_OR_UNSET_SELECTED_REFERENCE'):
            raise ValueError('Unexpected actual version or invalid original report')
        cases={x['id']:x for x in report['cases']}
        if set(cases)!={'demo-assigned','demo-intentionally-empty'}:
            raise ValueError('Original demo case identifiers differ')
        if cases['demo-assigned']['status']!='ASSIGNED' or \
            cases['demo-intentionally-empty']['status']!='REFERENCE_NULL_OR_UNSET':
            raise ValueError('Original assigned and empty reference distinction failed')
        for item in cases.values():
            if not item['sourceLookup'].startswith('RESOURCES:HPRSample/'):
                raise ValueError('Scene-based reference pin violates original path-only design')
    for a,b in zip(sorted(editor['cases'],key=lambda x:x['id']),
                   sorted(player['cases'],key=lambda x:x['id'])):
        for key in ('id','fieldName','sourceLookup','assetName','status',
                    'referencedType','referencedName'):
            if a[key]!=b[key]:
                raise ValueError('Actual Unity2022 Player and Editor disagree: '+key)
    result={'status':'PASS_ACTUAL_UNITY2022_LINUX_PLAYER_ORIGINAL_DEMO',
            'schema':2,'original_reference_cases':2,
            'assigned_in_both':1,'intentional_empty_in_both':1,
            'source_pinned_from_test_scene':False}
    with out_path.open('x') as file:
        json.dump(result,file,indent=2)
        file.write('\n')
    return result

if __name__=='__main__':
    assert len(sys.argv)==4
    print(json.dumps(verify(*map(Path,sys.argv[1:]))))
