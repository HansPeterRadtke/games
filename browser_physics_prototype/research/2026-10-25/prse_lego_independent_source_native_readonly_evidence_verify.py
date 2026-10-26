#!/usr/bin/env python3
"""Read-only independent integrity verifier for LEGO-Bench PRSE round one.
Checks an entirely new external human-authored source, native Rapier
matched-arm contact identity/size, source-to-reference alignment, conservative
post-frozen category ceilings, strict directed top supports, and abstentions.
No physical experiment is repeated and the denied placebo remains denied.
"""
from pathlib import Path
from stat import S_IMODE
from hashlib import sha256
from collections import Counter
import json,math,importlib.util,re
HERE=Path(__file__).resolve().parent
P=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-lego-independent')
R=P/'reference-snapshots'
DATA=P/'lego_full_data_public_human_gold.json'
SRC=P/'lego_source_only_frozen_130_raw_v1.json'
RAW=P/'lego_source_only_matched_native_130_raw_v1.json'
GOLD=P/'lego_independent_human_gold_source_and_3d_reference_score_v2.json'
SAFE=HERE/'prse_lego_external_human_gold_3d_source_aggregate_v2.json'
NATIVE_SAFE=HERE/'prse_lego_human_matched_native_130_aggregate_v1.json'
MANIFEST=P/'lego_independent_reference_scene_sha256_manifest_v2.json'
LEX=HERE.parent/'2026-10-24'/'prse_semantic_constraints.py'
def digest(path):return sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())
assert S_IMODE(P.stat().st_mode)==0o700
assert all(S_IMODE(x.stat().st_mode)==0o600 for x in (DATA,SRC,RAW,GOLD,MANIFEST))
assert len(list(R.glob('data_*.json')))==130
source=read(SRC);native=read(RAW);gold=read(DATA);ind=read(GOLD);safe=read(SAFE);pub=read(NATIVE_SAFE)
assert len(source['scenes'])==len(native['rows'])==len(gold)==130
assert digest(DATA)==safe['metadata']['officialHumanCuratedConstraintGoldSHA256']
assert digest(SRC)==safe['metadata']['frozenSourceOnlySHA256']==pub['metadata']['sourceSHA256']
assert digest(RAW)==safe['metadata']['frozenNativeGameCoreSHA256']==pub['metadata']['privateRawSHA256']
assert digest(GOLD)==safe['metadata']['privatePerCaseAuditSHA256']
assert digest(MANIFEST)==safe['metadata']['privateReferenceSceneSHA256Manifest']
assert native['metadata']['priorDeniedRandomSupportPlaceboNotAttempted'] is True
assert source['metadata']['neverAccessedHumanConstraintsOrReferencesInThisPhase'] is True
spec=importlib.util.spec_from_file_location('prse_frozen_parser_verify',LEX)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
def cn(s):return module.canon(re.sub(r'-\d+$','',str(s).lower()).replace('-','_'))
def pairset(records):return {tuple(sorted((a['a'],a['b']))) for a in records if a.get('contactPointCount',0)>0}
def tilt(q):
    n=math.hypot(q['x'],q['y'],q['z'],q['w'])
    if n<.5:return math.pi
    return math.acos(max(-1,min(1,1-2*(q['x']**2+q['z']**2)/(n*n))))
def supported(state,child,parent):
    by={}
    for e in state['bodyStates']:by.setdefault(cn(e['kind']),[]).append(e)
    pairs={frozenset((p['a'],p['b'])) for p in state['contactPairs'] if p.get('contactPointCount',0)>0}
    for p in by.get(parent,[]):
        if p['shape']!='box' or tilt(p['rotation'])>.1:continue
        for c in by.get(child,[]):
            if c['id']==p['id'] or tilt(c['rotation'])>.1:continue
            if any(abs(c['position'][axis]-p['position'][axis])+c['size'][axis]/2>
                p['size'][axis]/2+.03 for axis in ('x','z')):continue
            if abs(c['position']['y']-c['size']['y']/2-p['position']['y']-p['size']['y']/2)>.08:continue
            if frozenset((p['id'],c['id'])) in pairs:return True
    return False
m=Counter();kind_overlap=0;reference_count=0;unnamed=0
for index,(src,row,record) in enumerate(zip(source['scenes'],native['rows'],gold)):
    assert src['sourceIndex']==row['sourceIndex']==index
    assert row['status']=='matched_real_native_and_saved'
    assert src['sourceText']==record['instruction']
    assert sha256(record['instruction'].encode()).hexdigest()==src['sourceHash']
    f=R/f'data_{index}.json'
    assert S_IMODE(f.stat().st_mode)==0o600
    assert digest(f)==read(MANIFEST)['rawFileHashes'][f'data_{index}.json']
    ref=read(f)
    assert ref['index']==index and ref['query']==src['sourceText']
    m['references']+=1;m['rooms']+=len(ref['rooms']);m['multiroom']+=int(len(ref['rooms'])>1)
    m['constraints']+=len(record['labels'])
    assert len(record['labels'])==len(record['constraints'])
    assert sorted(int(x['condition_idx']) for x in record['labels'])==list(range(len(record['labels'])))
    counts=Counter(cn(z['object_name']) for z in ref['objects'] if isinstance(z.get('object_name'),str) and z['object_name'])
    output=Counter(cn(z['kind']) for z in row['baseline']['bodyStates'])
    a=set(z['id'] for z in row['baseline']['bodyStates'])
    for k in ('lexical','learned'):
        b=row[k]['bodyStates']
        assert {z['id'] for z in b}==a
        orig={z['id']:z for z in row['baseline']['bodyStates']}
        for z in b:
            first=orig[z['id']]
            assert z['kind']==first['kind'] and z['size']==first['size'] and z['shape']==first['shape'] and z['body']==first['body']
    assert row['sameBodyCount']==sum(output.values())
    m['bodies']+=row['sameBodyCount']
    old=pairset(row['baseline']['contactPairs']);lex=pairset(row['lexical']['contactPairs']);learn=pairset(row['learned']['contactPairs'])
    assert lex==learn,'No new ON placement was accepted, so the learned arm must be exact contact negative control'
    assert not old, 'Neutral-grid baseline should have zero interobject native contacts'
    m['lexContacts']+=len(lex)
    m['sourceLearnedProposals']+=row['learnedOnProposals']
    m['learnedAdmitted']+=row['grammarSourceContacts']
    m['nativeUnchangedLearnedNegativeScenes']+=int(learn==lex)
    m['namedReference']+=sum(counts.values())
    unnamed_here=sum(not isinstance(z.get('object_name'),str) or not z['object_name'] for z in ref['objects'])
    unnamed+=unnamed_here
    m['namedCategoryMatchesAtMost']+=sum(min(counts[k],output[k]) for k in set(counts)|set(output))
    m['namedCategoryAbsencesAtLeast']+=sum(max(0,counts[k]-output[k]) for k in counts)
    m['nativeInstancesNotConfirmedInNamedRef']+=sum(max(0,output[k]-counts[k]) for k in output)
assert m['namedReference']==3894 and unnamed==2950
assert m['rooms']==295 and m['multiroom']==95
assert m['constraints']==1250 and m['bodies']==575
assert m['lexContacts']==4 and m['sourceLearnedProposals']==2
assert m['namedCategoryMatchesAtMost']==239
assert m['namedCategoryAbsencesAtLeast']==3655
assert m['nativeInstancesNotConfirmedInNamedRef']==336
assert m['nativeUnchangedLearnedNegativeScenes']==130
assert m['namedReference']==m['namedCategoryMatchesAtMost']+m['namedCategoryAbsencesAtLeast']
assert m['bodies']==m['namedCategoryMatchesAtMost']+m['nativeInstancesNotConfirmedInNamedRef']
cases=ind['posthocExtractedGoldON'];assert len(cases)==16
assert ind['details'] and len(ind['details'])==130
strict=Counter()
for case in cases:
    row=native['rows'][case['scene']]
    child,parent=case['derivedChild'],case['derivedParent']
    assert any(label['condition_idx']==case['constraintIndex'] for label in gold[case['scene']]['labels'])
    for arm,key in [('baseline','oldStrictTopSupport'),('lexical','lexicalStrictTopSupport'),('learned','learnedStrictTopSupport')]:
        actual=supported(row[arm],child,parent)
        assert actual==case[key],('Strict native supporting source fact mismatched',case,arm)
        strict[arm]+=int(actual)
        if actual:
            # Reversed roles must not pass a non-directional collider-contact heuristic.
            assert not supported(row[arm],parent,child),'Backward on-top relation falsely accepted'
assert dict(strict)=={'lexical':4,'learned':4} or (strict['baseline']==0 and strict['lexical']==4 and strict['learned']==4)
assert safe['total']['posthocStrictTopSupportBaseline']==0
assert safe['total']['posthocStrictTopSupportLexical']==safe['total']['posthocStrictTopSupportLearned']==4
print('VERIFIED LEGO 130 external human-sourced/annotated instructions, 1250 constraints, 130 independent reference scenes.')
print('VERIFIED 575 native bodies per arm, exact IDs/categories/dimensions and preserved original source,')
print('all 130 frozen neutral-grid and learned-zero-addition negative controls, 4 true lexical native contacts.')
print('VERIFIED strictly directional real native top supports 0/16 baseline versus 4/16 lexical')
print('and 4/16 learned; reverse support roles rejected, all original author reference hashes valid.')
print('VERIFIED 95 multi-room topology misses and named reference category overlap ceiling 239/3894.')
print('Unlabeled reference objects, exact instance identity, asset scale, observer prose and real FP are UNKNOWN.')
