#!/usr/bin/env python3
"""Independent POST-FREEZE assessment of the LEGO-Bench human-curated
reference 3D objects/rooms and independently annotated constraint categories.
No generation or physics effects. Do not turn unnamed reference assets into
known negatives or assert instance/pose/mesh fidelity without source linkage.
"""
import hashlib,importlib.util,json,re,math,statistics
from pathlib import Path
from collections import Counter,defaultdict
from stat import S_IMODE
HERE=Path(__file__).resolve().parent
ROOT=Path('/data/var/games/prse_semantic_research/runs/2026-10-26-lego-independent')
EXTERNAL=ROOT/'lego_full_data_public_human_gold.json'
SRC=ROOT/'lego_source_only_frozen_130_raw_v1.json'
NATIVE=ROOT/'lego_source_only_matched_native_130_raw_v1.json'
REFERENCES=ROOT/'reference-snapshots'
LEX=HERE.parent/'2026-10-24'/'prse_semantic_constraints.py'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
assert S_IMODE(ROOT.stat().st_mode)==0o700
assert all(S_IMODE(p.stat().st_mode)==0o600 for p in (EXTERNAL,SRC,NATIVE))
s=read(SRC);physics=read(NATIVE);gold=read(EXTERNAL)
assert len(gold)==len(s['scenes'])==len(physics['rows'])==130
assert physics['metadata']['frozenSourceOnlySHA256']==sha(SRC)
assert s['metadata']['rawFullDataSHA256']==sha(EXTERNAL)
spec=importlib.util.spec_from_file_location('previously_frozen_lexicon',LEX)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
def canonical(x):
    return module.canon(re.sub(r'-\d+$','',str(x).lower()).replace('-','_'))
def native_pairs(body_states,contacts):
    names={e['id']:canonical(e['kind']) for e in body_states}
    return Counter(tuple(sorted((names[c['a']],names[c['b']])))
                   for c in contacts if c.get('contactPointCount',0)>0)
def strict_native_top_support(body_states,contacts,child,parent):
    by=defaultdict(list)
    for e in body_states:by[canonical(e['kind'])].append(e)
    touching={frozenset((r['a'],r['b'])) for r in contacts if r.get('contactPointCount',0)>0}
    def tilt(q):
        n=math.hypot(q['x'],q['y'],q['z'],q['w'])
        if n<0.5:return math.pi
        return math.acos(max(-1,min(1,1-2*(q['x']**2+q['z']**2)/(n*n))))
    for p in by[parent]:
        if p['shape']!='box' or tilt(p['rotation'])>0.1:continue
        for c in by[child]:
            if p['id']==c['id'] or tilt(c['rotation'])>0.1:continue
            if any(abs(c['position'][axis]-p['position'][axis])+c['size'][axis]/2>
                   p['size'][axis]/2+0.03 for axis in ('x','z')):continue
            if abs((c['position']['y']-c['size']['y']/2)-
                   (p['position']['y']+p['size']['y']/2))>0.08:continue
            if frozenset((p['id'],c['id'])) not in touching:continue
            return True
    return False

scores=Counter();details=[];support_cases=[]
named_reference_types=Counter();actual_generated_types=Counter()
for i,(annotation,proposal,native) in enumerate(zip(gold,s['scenes'],physics['rows'])):
    assert native['sourceIndex']==i and proposal['sourceIndex']==i
    assert native['status']=='matched_real_native_and_saved'
    assert annotation['instruction']==proposal['sourceText']
    ref_path=REFERENCES/f'data_{i}.json'
    assert ref_path.is_file() and S_IMODE(ref_path.stat().st_mode)==0o600
    scene=read(ref_path)
    assert scene['index']==i
    assert scene.get('query')==annotation['instruction'],('Reference scene query mismatched author instruction',i)
    assert len(annotation['constraints'])==len(annotation['labels'])
    source_gold=annotation['labels']
    assert sorted(int(x['condition_idx']) for x in source_gold)==list(range(len(source_gold))),('Reference constraint indices must be unique within scene',i)
    types=Counter(x['condition_type'] for x in source_gold)
    assert set(types).issubset({'Object Placement','Object Selection','Floor Layout','Material Selection'})
    scores.update(types)
    assert native['sameBodyCount']==len(native['baseline']['bodyStates'])==len(native['lexical']['bodyStates'])==len(native['learned']['bodyStates'])
    # Ref names include tracked object instance labels, but many smaller
    # decoration assets have no object_name and cannot be scored as absent.
    reference=Counter(canonical(e['object_name']) for e in scene['objects']
                     if isinstance(e.get('object_name'),str) and e['object_name'])
    unnamed=sum(not isinstance(e.get('object_name'),str) or not e['object_name'] for e in scene['objects'])
    outputs=Counter(canonical(e['kind']) for e in native['baseline']['bodyStates'])
    named_reference_types.update(reference);actual_generated_types.update(outputs)
    covered=sum(min(reference[k],outputs[k]) for k in set(reference)|set(outputs))
    lower_misses=sum(max(0,reference[k]-outputs[k]) for k in reference)
    unmatched_outputs=sum(max(0,outputs[k]-reference[k]) for k in outputs)
    assert covered+lower_misses==sum(reference.values())
    assert covered+unmatched_outputs==sum(outputs.values())
    scores['referenceRooms']+=len(scene['rooms'])
    scores['sourceInstructions']+=1
    scores['sourceConstraints']+=len(source_gold)
    scores['referenceMultiRoomScenes']+=int(len(scene['rooms'])>1)
    scores['referenceSingleRoomScenes']+=int(len(scene['rooms'])==1)
    scores['referenceNamedInstanceLabels']+=sum(reference.values())
    scores['referenceUnnamedObjectsNotScorableAsTrueNegatives']+=unnamed
    scores['nativeOriginalInstantiatedBodies']+=sum(outputs.values())
    scores['sceneCategoryInstanceMatchingCeiling']+=covered
    scores['referenceNamedInstanceDeficitFloor']+=lower_misses
    scores['nativeInstancesNotFoundInNamedReference']+=unmatched_outputs
    scores['goldNamedCategories']+=len(reference)
    scores['goldNamedCategoriesWithOneOrMoreNative']+=sum(reference[k]>0 and outputs[k]>0 for k in reference)
    scores['nativeCategoriesNotNamedInReference']+=sum(reference[k]==0 for k in outputs)
    scores['scenesWithoutNamedReferenceInstanceDeficit']+=int(lower_misses==0)
    # Explicit human-annotated 'Object Placement' clauses are original
    # independent source evidence, but the category pair below is merely
    # an automatic extraction (not an independent instance-level human gold).
    oldpairs=native_pairs(native['baseline']['bodyStates'],native['baseline']['contactPairs'])
    lexpairs=native_pairs(native['lexical']['bodyStates'],native['lexical']['contactPairs'])
    learnedpairs=native_pairs(native['learned']['bodyStates'],native['learned']['contactPairs'])
    assert sum(oldpairs.values())==native['controlNativeContactCount']
    assert sum(lexpairs.values())==native['lexicalNativeContactCount']
    assert sum(learnedpairs.values())==native['learnedNativeContactCount']
    confirmedTypePairs=set()
    for label in source_gold:
        if label['condition_type']!='Object Placement':continue
        statement=' '.join(label['instructions'])
        if re.search(r'\b(?:on|atop|upon)\b',statement,re.I):
            scores['humanObjectPlacementContainsON']+=1
        # ONLY unambiguously identified object->physical-support mentions,
        # not room floor, wall art against walls, negated or model-derived
        # guesses. An unknown clause remains unknown.
        mentioned=[m for m in module.mentions(statement)]
        match=re.search(r'\b(?:on top of|on|atop|upon)\b',statement,re.I)
        if not match:continue
        pre=[m for m in mentioned if m['end']<=match.start()]
        post=[m for m in mentioned if m['start']>=match.end()]
        if not pre or not post:continue
        child=canonical(pre[-1]['type']);parent=canonical(post[0]['type'])
        if child==parent:continue
        if parent in {'wall','floor','room','door','window','ceiling'}:continue
        # This is a limited machine-readable subset of the positive
        # annotations, NOT complete human-relational gold.
        pair=tuple(sorted((child,parent)))
        confirmedTypePairs.add(pair)
        scores['posthocExtractablePositiveObjectOnClauses']+=1
        realOld=strict_native_top_support(native['baseline']['bodyStates'],native['baseline']['contactPairs'],child,parent)
        realLex=strict_native_top_support(native['lexical']['bodyStates'],native['lexical']['contactPairs'],child,parent)
        realNew=strict_native_top_support(native['learned']['bodyStates'],native['learned']['contactPairs'],child,parent)
        scores['posthocStrictTopSupportBaseline']+=int(realOld)
        scores['posthocStrictTopSupportLexical']+=int(realLex)
        scores['posthocStrictTopSupportLearned']+=int(realNew)
        support_cases.append({'scene':i,'constraintIndex':label['condition_idx'],
            'derivedChild':child,'derivedParent':parent,
            'oldStrictTopSupport':realOld,
            'lexicalStrictTopSupport':realLex,
            'learnedStrictTopSupport':realNew})
    # No human-negative annotation of every legal pair, so mark new
    # physical contacts without an annotated pair as UNVERIFIED, not FP.
    for pair,cnt in lexpairs.items():
        if cnt>oldpairs[pair]:
            scores['newRealLexicalContactsNotVerifiablySourceEntailed']+=(max(0,cnt-oldpairs[pair]) if pair not in confirmedTypePairs else 0)
            scores['newRealLexicalContactsWithMatchingPositiveSourceClause']+=(max(0,cnt-oldpairs[pair]) if pair in confirmedTypePairs else 0)
    details.append({'scene':i,'referenceRoomCount':len(scene['rooms']),
        'annotatedConstraintCategories':dict(types),
        'referenceNamedObjects':sum(reference.values()),
        'referenceUnnamedObjects':unnamed,'actualNativeBodies':sum(outputs.values()),
        'categoryInstanceOverlapCeiling':covered,
        'definiteReferenceNamedInstanceShortfall':lower_misses,
        'nativeInstancesUnmatchedByNamedReference':unmatched_outputs,
        'referenceCategories':dict(reference),'nativeCategories':dict(outputs),
        'lexicalTrueNativePairs':len(native['lexical']['contactPairs'])})
assert scores['sourceConstraints']==1250
assert scores['sourceInstructions']==130
assert scores['nativeOriginalInstantiatedBodies']==575
assert scores['referenceRooms']==295
assert scores['referenceNamedInstanceDeficitFloor']>=0
assert scores['referenceNamedInstanceDeficitFloor']+scores['sceneCategoryInstanceMatchingCeiling']==scores['referenceNamedInstanceLabels']
assert scores['nativeOriginalInstantiatedBodies']==scores['sceneCategoryInstanceMatchingCeiling']+scores['nativeInstancesNotFoundInNamedReference']
private=ROOT/'lego_independent_human_gold_source_and_3d_reference_score_v2.json'
with private.open('x') as f:json.dump({'details':details,'posthocExtractedGoldON':support_cases},f,indent=2);f.write('\n')
private.chmod(0o600)
referenceHashes={f'data_{i}.json':sha(REFERENCES/f'data_{i}.json') for i in range(130)}
hashfile=ROOT/'lego_independent_reference_scene_sha256_manifest_v2.json'
with hashfile.open('x') as f:json.dump({'source':'LEGO-Eval/LEGO_Bench/data/data_i/data_i.json',
'rawFileHashes':referenceHashes},f,indent=2);f.write('\n')
hashfile.chmod(0o600)
result={'metadata':{
 'officialHumanCuratedConstraintGoldSHA256':sha(EXTERNAL),
 'frozenSourceOnlySHA256':sha(SRC),
 'frozenNativeGameCoreSHA256':sha(NATIVE),
 'externalReferenceScenesIndependentFromSceneEval':130,
 'privateReferenceSceneSHA256Manifest':sha(hashfile),
 'privatePerCaseAuditSHA256':sha(private),
 'goldWasNotUsedBySourceOnlyModelOrNativePhysics':True,
 'strictOnRequiresDirectionalUprightTopFaceWithinFootprintAndRealRapierContact':True,
 'authorAnnotationIsPositiveConstraintTypeAndTextNotExhaustiveObjectPairNegatives':True,
 'categoryInstanceOverlapIsUpperBoundNotVerifiedIdentityCorrespondence':True,
 'referenceContainsUnlabelledObjectsAndSomeExtraPlausibleProps':True,
 'singleRoomGameCoreSourceCompilerCannotReproduceHumanMultiRoomTopology':True,
 'referenceScenesHaveCenterAndRotationButNoTrustedObjectDimensionsOrCollisionMeshAvailable':True,
 'genericUnsupportedCategoriesAndPreciseScaleCannotBeCalledPhysicallyCorrect':True,
 'observerProseNotIndependentlyAnnotatedInThisDataset':True,
 },'total':dict(scores),
 'categoryReferenceCountTop15':named_reference_types.most_common(15),
 'modelNativeTypeCountTop15':actual_generated_types.most_common(15)}
output=HERE/'prse_lego_external_human_gold_3d_source_aggregate_v2.json'
with output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print('LEGO_HUMAN_REFERENCED_SOURCE_AND_NATIVE',json.dumps(result['total'],sort_keys=True))
